"""Scheduled workflow execution manager."""

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel, Field

from test_ai.config import get_settings
from test_ai.orchestrator import WorkflowEngine

logger = logging.getLogger(__name__)


class ScheduleType(str, Enum):
    """Types of schedule triggers."""

    CRON = "cron"
    INTERVAL = "interval"


class ScheduleStatus(str, Enum):
    """Schedule status."""

    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


class CronConfig(BaseModel):
    """Cron schedule configuration."""

    minute: str = Field("*", description="Minute (0-59)")
    hour: str = Field("*", description="Hour (0-23)")
    day: str = Field("*", description="Day of month (1-31)")
    month: str = Field("*", description="Month (1-12)")
    day_of_week: str = Field("*", description="Day of week (0-6, mon-sun)")


class IntervalConfig(BaseModel):
    """Interval schedule configuration."""

    seconds: int = Field(0, ge=0, description="Seconds")
    minutes: int = Field(0, ge=0, description="Minutes")
    hours: int = Field(0, ge=0, description="Hours")
    days: int = Field(0, ge=0, description="Days")


class WorkflowSchedule(BaseModel):
    """A scheduled workflow definition."""

    id: str = Field(..., description="Schedule identifier")
    workflow_id: str = Field(..., description="Workflow to execute")
    name: str = Field(..., description="Schedule name")
    description: str = Field("", description="Schedule description")
    schedule_type: ScheduleType = Field(..., description="Type of schedule")
    cron_config: Optional[CronConfig] = Field(None, description="Cron configuration")
    interval_config: Optional[IntervalConfig] = Field(
        None, description="Interval configuration"
    )
    variables: Dict[str, Any] = Field(
        default_factory=dict, description="Workflow variables to pass"
    )
    status: ScheduleStatus = Field(ScheduleStatus.ACTIVE, description="Schedule status")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    last_run: Optional[datetime] = Field(None, description="Last execution time")
    next_run: Optional[datetime] = Field(None, description="Next scheduled execution")
    run_count: int = Field(0, ge=0, description="Total execution count")


class ScheduleExecutionLog(BaseModel):
    """Log entry for a scheduled execution."""

    schedule_id: str
    workflow_id: str
    executed_at: datetime
    status: str
    duration_seconds: float
    error: Optional[str] = None


class ScheduleManager:
    """Manages scheduled workflow execution."""

    def __init__(self):
        self.settings = get_settings()
        self.schedules_dir = self.settings.schedules_dir
        self.schedules_dir.mkdir(parents=True, exist_ok=True)
        self.workflow_engine = WorkflowEngine()
        self.scheduler = BackgroundScheduler()
        self._schedules: Dict[str, WorkflowSchedule] = {}

    def start(self):
        """Start the scheduler and load existing schedules."""
        self._load_all_schedules()
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler shutdown")

    def _load_all_schedules(self):
        """Load all schedules from disk and register active ones."""
        for file_path in self.schedules_dir.glob("*.json"):
            try:
                schedule = self._load_schedule_file(file_path)
                if schedule:
                    self._schedules[schedule.id] = schedule
                    if schedule.status == ScheduleStatus.ACTIVE:
                        self._register_job(schedule)
            except Exception as e:
                logger.error(f"Failed to load schedule {file_path}: {e}")

    def _load_schedule_file(self, file_path: Path) -> Optional[WorkflowSchedule]:
        """Load a schedule from file."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return WorkflowSchedule(**data)
        except Exception:
            return None

    def _save_schedule(self, schedule: WorkflowSchedule) -> bool:
        """Save a schedule to disk."""
        try:
            file_path = self.schedules_dir / f"{schedule.id}.json"
            with open(file_path, "w") as f:
                json.dump(schedule.model_dump(mode="json"), f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save schedule {schedule.id}: {e}")
            return False

    def _register_job(self, schedule: WorkflowSchedule):
        """Register a schedule with APScheduler."""
        job_id = f"schedule_{schedule.id}"

        # Remove existing job if present
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        if schedule.status != ScheduleStatus.ACTIVE:
            return

        trigger = self._create_trigger(schedule)
        if not trigger:
            logger.error(f"Failed to create trigger for schedule {schedule.id}")
            return

        self.scheduler.add_job(
            self._execute_scheduled_workflow,
            trigger=trigger,
            id=job_id,
            args=[schedule.id],
            name=schedule.name,
            replace_existing=True,
        )

        # Update next run time
        job = self.scheduler.get_job(job_id)
        if job and job.next_run_time:
            schedule.next_run = job.next_run_time
            self._save_schedule(schedule)

        logger.info(f"Registered job for schedule {schedule.id}")

    def _create_trigger(self, schedule: WorkflowSchedule):
        """Create APScheduler trigger from schedule config."""
        if schedule.schedule_type == ScheduleType.CRON and schedule.cron_config:
            return CronTrigger(
                minute=schedule.cron_config.minute,
                hour=schedule.cron_config.hour,
                day=schedule.cron_config.day,
                month=schedule.cron_config.month,
                day_of_week=schedule.cron_config.day_of_week,
            )
        elif (
            schedule.schedule_type == ScheduleType.INTERVAL and schedule.interval_config
        ):
            cfg = schedule.interval_config
            # Ensure at least some interval is set
            if (
                cfg.seconds == 0
                and cfg.minutes == 0
                and cfg.hours == 0
                and cfg.days == 0
            ):
                cfg.minutes = 1  # Default to 1 minute
            return IntervalTrigger(
                seconds=cfg.seconds,
                minutes=cfg.minutes,
                hours=cfg.hours,
                days=cfg.days,
            )
        return None

    def _execute_scheduled_workflow(self, schedule_id: str):
        """Execute a scheduled workflow."""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            logger.error(f"Schedule {schedule_id} not found")
            return

        logger.info(f"Executing scheduled workflow: {schedule.workflow_id}")
        start_time = datetime.now()
        error_msg = None

        try:
            workflow = self.workflow_engine.load_workflow(schedule.workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {schedule.workflow_id} not found")

            if schedule.variables:
                workflow.variables.update(schedule.variables)

            result = self.workflow_engine.execute_workflow(workflow)
            status = result.status

        except Exception as e:
            logger.error(f"Scheduled execution failed: {e}")
            status = "failed"
            error_msg = str(e)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Update schedule stats
        schedule.last_run = start_time
        schedule.run_count += 1

        # Update next run time
        job = self.scheduler.get_job(f"schedule_{schedule_id}")
        if job and job.next_run_time:
            schedule.next_run = job.next_run_time

        self._save_schedule(schedule)
        self._schedules[schedule_id] = schedule

        # Log execution
        self._save_execution_log(
            ScheduleExecutionLog(
                schedule_id=schedule_id,
                workflow_id=schedule.workflow_id,
                executed_at=start_time,
                status=status,
                duration_seconds=duration,
                error=error_msg,
            )
        )

    def _save_execution_log(self, log: ScheduleExecutionLog):
        """Save execution log entry."""
        logs_dir = self.settings.logs_dir / "scheduled"
        logs_dir.mkdir(parents=True, exist_ok=True)

        log_file = (
            logs_dir
            / f"{log.schedule_id}_{log.executed_at.strftime('%Y%m%d_%H%M%S')}.json"
        )
        try:
            with open(log_file, "w") as f:
                json.dump(log.model_dump(mode="json"), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save execution log: {e}")

    def create_schedule(self, schedule: WorkflowSchedule) -> bool:
        """Create a new schedule."""
        # Validate workflow exists
        workflow = self.workflow_engine.load_workflow(schedule.workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {schedule.workflow_id} not found")

        schedule.created_at = datetime.now()
        if self._save_schedule(schedule):
            self._schedules[schedule.id] = schedule
            if schedule.status == ScheduleStatus.ACTIVE:
                self._register_job(schedule)
            return True
        return False

    def update_schedule(self, schedule: WorkflowSchedule) -> bool:
        """Update an existing schedule."""
        if schedule.id not in self._schedules:
            raise ValueError(f"Schedule {schedule.id} not found")

        # Preserve creation time and run count
        existing = self._schedules[schedule.id]
        schedule.created_at = existing.created_at
        schedule.run_count = existing.run_count
        schedule.last_run = existing.last_run

        if self._save_schedule(schedule):
            self._schedules[schedule.id] = schedule
            self._register_job(schedule)  # Re-register with new config
            return True
        return False

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        if schedule_id not in self._schedules:
            return False

        # Remove from scheduler
        job_id = f"schedule_{schedule_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        # Remove file
        file_path = self.schedules_dir / f"{schedule_id}.json"
        try:
            file_path.unlink()
        except Exception:
            pass

        del self._schedules[schedule_id]
        return True

    def get_schedule(self, schedule_id: str) -> Optional[WorkflowSchedule]:
        """Get a schedule by ID."""
        return self._schedules.get(schedule_id)

    def list_schedules(self) -> List[Dict]:
        """List all schedules."""
        schedules = []
        for schedule in self._schedules.values():
            # Update next run time from scheduler
            job = self.scheduler.get_job(f"schedule_{schedule.id}")
            if job and job.next_run_time:
                schedule.next_run = job.next_run_time

            schedules.append(
                {
                    "id": schedule.id,
                    "name": schedule.name,
                    "workflow_id": schedule.workflow_id,
                    "schedule_type": schedule.schedule_type.value,
                    "status": schedule.status.value,
                    "last_run": schedule.last_run.isoformat()
                    if schedule.last_run
                    else None,
                    "next_run": schedule.next_run.isoformat()
                    if schedule.next_run
                    else None,
                    "run_count": schedule.run_count,
                }
            )
        return schedules

    def pause_schedule(self, schedule_id: str) -> bool:
        """Pause a schedule."""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return False

        schedule.status = ScheduleStatus.PAUSED
        job_id = f"schedule_{schedule_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.pause_job(job_id)

        self._save_schedule(schedule)
        return True

    def resume_schedule(self, schedule_id: str) -> bool:
        """Resume a paused schedule."""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return False

        schedule.status = ScheduleStatus.ACTIVE
        job_id = f"schedule_{schedule_id}"
        job = self.scheduler.get_job(job_id)

        if job:
            self.scheduler.resume_job(job_id)
        else:
            self._register_job(schedule)

        # Update next run time
        job = self.scheduler.get_job(job_id)
        if job and job.next_run_time:
            schedule.next_run = job.next_run_time

        self._save_schedule(schedule)
        return True

    def trigger_now(self, schedule_id: str) -> bool:
        """Manually trigger a scheduled workflow immediately."""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return False

        # Execute in background
        self._execute_scheduled_workflow(schedule_id)
        return True

    def get_execution_history(
        self, schedule_id: str, limit: int = 10
    ) -> List[ScheduleExecutionLog]:
        """Get execution history for a schedule."""
        logs_dir = self.settings.logs_dir / "scheduled"
        if not logs_dir.exists():
            return []

        logs = []
        for file_path in sorted(logs_dir.glob(f"{schedule_id}_*.json"), reverse=True)[
            :limit
        ]:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                logs.append(ScheduleExecutionLog(**data))
            except Exception:
                continue

        return logs
