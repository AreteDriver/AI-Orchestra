"""Manager for ops events and weekly aggregates."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from test_ai.config import get_settings
from test_ai.ops.aggregate import aggregate_week, week_window
from test_ai.ops.models import ArtifactType, OpsEvent, ProjectType, WeeklyAgg
from test_ai.state import DatabaseBackend, get_database

logger = logging.getLogger(__name__)


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Parse datetime from database value."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def _parse_date(value: Any) -> Optional[date]:
    """Parse date from database value."""
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(value)


class OpsEventManager:
    """Manages ops events and weekly aggregates with database persistence."""

    SCHEMA = """
        -- Ops events table
        CREATE TABLE IF NOT EXISTS ops_events (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            project TEXT DEFAULT 'other',
            artifact INTEGER DEFAULT 0,
            artifact_type TEXT,
            reusable INTEGER DEFAULT 0,
            decision_closed INTEGER DEFAULT 0,
            execution_done INTEGER DEFAULT 0,
            minutes_saved INTEGER DEFAULT 0 CHECK (minutes_saved >= 0),
            loop INTEGER DEFAULT 0,
            impact_career INTEGER DEFAULT 0 CHECK (impact_career >= 0),
            impact_legal INTEGER DEFAULT 0 CHECK (impact_legal >= 0),
            impact_revenue INTEGER DEFAULT 0 CHECK (impact_revenue >= 0)
        );

        CREATE INDEX IF NOT EXISTS idx_ops_events_session ON ops_events(session_id);
        CREATE INDEX IF NOT EXISTS idx_ops_events_timestamp ON ops_events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_ops_events_project ON ops_events(project);

        -- Weekly aggregates table
        CREATE TABLE IF NOT EXISTS weekly_aggs (
            week_start TEXT PRIMARY KEY,
            week_end TEXT NOT NULL,
            sessions INTEGER DEFAULT 0,
            artifacts INTEGER DEFAULT 0,
            decisions INTEGER DEFAULT 0,
            executions INTEGER DEFAULT 0,
            loops INTEGER DEFAULT 0,
            hours_saved REAL DEFAULT 0.0,
            career_points INTEGER DEFAULT 0,
            legal_points INTEGER DEFAULT 0,
            revenue_points INTEGER DEFAULT 0,
            impact_points INTEGER DEFAULT 0,
            loop_rate REAL DEFAULT 0.0,
            snr REAL DEFAULT 0.0,
            output_score REAL DEFAULT 0.0,
            efficiency_score REAL DEFAULT 0.0,
            impact_score REAL DEFAULT 0.0,
            quality_score REAL DEFAULT 0.0,
            weekly_score INTEGER DEFAULT 0,
            computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_weekly_aggs_week ON weekly_aggs(week_start DESC);
    """

    def __init__(self, backend: DatabaseBackend | None = None):
        """Initialize the ops event manager.

        Args:
            backend: Database backend (uses default if not provided)
        """
        self.settings = get_settings()
        self.backend = backend or get_database()
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        self.backend.executescript(self.SCHEMA)

    # ==================== OpsEvent CRUD ====================

    def create_ops_event(self, event: OpsEvent) -> OpsEvent:
        """Create a new ops event.

        Args:
            event: OpsEvent to create

        Returns:
            The created OpsEvent

        Raises:
            ValueError: If validation fails
        """
        # Validate artifact_type is set if artifact is True
        if event.artifact and not event.artifact_type:
            raise ValueError("artifact_type is required when artifact is True")

        try:
            with self.backend.transaction():
                self.backend.execute(
                    """
                    INSERT INTO ops_events
                    (id, session_id, timestamp, project, artifact, artifact_type,
                     reusable, decision_closed, execution_done, minutes_saved,
                     loop, impact_career, impact_legal, impact_revenue)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.id,
                        event.session_id,
                        event.timestamp.isoformat(),
                        event.project.value if isinstance(event.project, ProjectType) else event.project,
                        1 if event.artifact else 0,
                        event.artifact_type.value if isinstance(event.artifact_type, ArtifactType) else event.artifact_type,
                        1 if event.reusable else 0,
                        1 if event.decision_closed else 0,
                        1 if event.execution_done else 0,
                        event.minutes_saved,
                        1 if event.loop else 0,
                        event.impact_career,
                        event.impact_legal,
                        event.impact_revenue,
                    ),
                )
            logger.info(f"Created ops event {event.id} for session {event.session_id}")
            return event
        except Exception as e:
            logger.error(f"Failed to create ops event: {e}")
            raise

    def get_ops_event(self, event_id: str) -> Optional[OpsEvent]:
        """Get an ops event by ID.

        Args:
            event_id: Event ID to look up

        Returns:
            OpsEvent if found, None otherwise
        """
        row = self.backend.fetchone(
            "SELECT * FROM ops_events WHERE id = ?",
            (event_id,),
        )
        if not row:
            return None
        return self._row_to_ops_event(row)

    def get_ops_event_by_session(self, session_id: str) -> Optional[OpsEvent]:
        """Get the ops event for a session.

        Args:
            session_id: Session ID to look up

        Returns:
            OpsEvent if found, None otherwise
        """
        row = self.backend.fetchone(
            "SELECT * FROM ops_events WHERE session_id = ?",
            (session_id,),
        )
        if not row:
            return None
        return self._row_to_ops_event(row)

    def update_ops_event(self, event_id: str, updates: Dict[str, Any]) -> Optional[OpsEvent]:
        """Update an existing ops event.

        Args:
            event_id: Event ID to update
            updates: Dictionary of fields to update

        Returns:
            Updated OpsEvent if found, None otherwise
        """
        existing = self.get_ops_event(event_id)
        if not existing:
            return None

        # Build update query dynamically
        allowed_fields = {
            "project", "artifact", "artifact_type", "reusable",
            "decision_closed", "execution_done", "minutes_saved",
            "loop", "impact_career", "impact_legal", "impact_revenue",
        }

        update_fields = []
        values = []

        for field, value in updates.items():
            if field not in allowed_fields:
                continue

            # Handle boolean to int conversion
            if field in ("artifact", "reusable", "decision_closed", "execution_done", "loop"):
                value = 1 if value else 0
            elif field == "project" and isinstance(value, ProjectType):
                value = value.value
            elif field == "artifact_type" and isinstance(value, ArtifactType):
                value = value.value

            update_fields.append(f"{field} = ?")
            values.append(value)

        if not update_fields:
            return existing

        values.append(event_id)

        try:
            with self.backend.transaction():
                self.backend.execute(
                    f"UPDATE ops_events SET {', '.join(update_fields)} WHERE id = ?",
                    tuple(values),
                )
            logger.info(f"Updated ops event {event_id}")
            return self.get_ops_event(event_id)
        except Exception as e:
            logger.error(f"Failed to update ops event {event_id}: {e}")
            raise

    def delete_ops_event(self, event_id: str) -> bool:
        """Delete an ops event.

        Args:
            event_id: Event ID to delete

        Returns:
            True if deleted, False if not found
        """
        existing = self.get_ops_event(event_id)
        if not existing:
            return False

        try:
            with self.backend.transaction():
                self.backend.execute(
                    "DELETE FROM ops_events WHERE id = ?",
                    (event_id,),
                )
            logger.info(f"Deleted ops event {event_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete ops event {event_id}: {e}")
            return False

    def list_ops_events(
        self,
        week_start: Optional[date] = None,
        project: Optional[ProjectType] = None,
        limit: int = 100,
    ) -> List[OpsEvent]:
        """List ops events with optional filtering.

        Args:
            week_start: Filter to events in the week starting on this date
            project: Filter to specific project
            limit: Maximum number of events to return

        Returns:
            List of matching OpsEvents
        """
        conditions = []
        params: List[Any] = []

        if week_start:
            start, end = week_window(week_start)
            conditions.append("timestamp >= ? AND timestamp < ?")
            params.extend([
                datetime.combine(start, datetime.min.time()).isoformat(),
                datetime.combine(end, datetime.min.time()).isoformat(),
            ])

        if project:
            conditions.append("project = ?")
            params.append(project.value if isinstance(project, ProjectType) else project)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        params.append(limit)

        rows = self.backend.fetchall(
            f"""
            SELECT * FROM ops_events
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            tuple(params),
        )
        return [self._row_to_ops_event(row) for row in rows]

    def _row_to_ops_event(self, row: Dict[str, Any]) -> OpsEvent:
        """Convert a database row to an OpsEvent."""
        return OpsEvent(
            id=row["id"],
            session_id=row["session_id"],
            timestamp=_parse_datetime(row["timestamp"]) or datetime.now(),
            project=row.get("project", "other"),
            artifact=bool(row.get("artifact", 0)),
            artifact_type=row.get("artifact_type"),
            reusable=bool(row.get("reusable", 0)),
            decision_closed=bool(row.get("decision_closed", 0)),
            execution_done=bool(row.get("execution_done", 0)),
            minutes_saved=row.get("minutes_saved", 0),
            loop=bool(row.get("loop", 0)),
            impact_career=row.get("impact_career", 0),
            impact_legal=row.get("impact_legal", 0),
            impact_revenue=row.get("impact_revenue", 0),
        )

    # ==================== Weekly Aggregation ====================

    def compute_weekly_aggregate(
        self,
        week_start_date: date,
        sessions_count: Optional[int] = None,
    ) -> WeeklyAgg:
        """Compute and store weekly aggregate for a given week.

        Args:
            week_start_date: The Monday of the week to aggregate
            sessions_count: Optional session count (if not provided, queries database)

        Returns:
            Computed WeeklyAgg
        """
        start, end = week_window(week_start_date)

        # Get ops events for the week
        rows = self.backend.fetchall(
            """
            SELECT * FROM ops_events
            WHERE timestamp >= ? AND timestamp < ?
            """,
            (
                datetime.combine(start, datetime.min.time()).isoformat(),
                datetime.combine(end, datetime.min.time()).isoformat(),
            ),
        )

        # Convert to dicts for aggregate function
        events = [dict(row) for row in rows]

        # If sessions_count not provided, use ops events count as proxy
        # In production, this would query an actual sessions table
        if sessions_count is None:
            sessions_count = len(events) if events else 0

        # Compute aggregates
        agg_data = aggregate_week(sessions_count, events)

        # Create WeeklyAgg model
        weekly_agg = WeeklyAgg(
            week_start=start.isoformat(),
            week_end=end.isoformat(),
            **agg_data,
        )

        # Upsert to database
        self._upsert_weekly_agg(weekly_agg)

        return weekly_agg

    def _upsert_weekly_agg(self, agg: WeeklyAgg) -> None:
        """Insert or update a weekly aggregate."""
        try:
            with self.backend.transaction():
                # Check if exists
                existing = self.backend.fetchone(
                    "SELECT week_start FROM weekly_aggs WHERE week_start = ?",
                    (agg.week_start,),
                )

                if existing:
                    self.backend.execute(
                        """
                        UPDATE weekly_aggs SET
                            week_end = ?, sessions = ?, artifacts = ?, decisions = ?,
                            executions = ?, loops = ?, hours_saved = ?,
                            career_points = ?, legal_points = ?, revenue_points = ?,
                            impact_points = ?, loop_rate = ?, snr = ?,
                            output_score = ?, efficiency_score = ?, impact_score = ?,
                            quality_score = ?, weekly_score = ?, computed_at = ?
                        WHERE week_start = ?
                        """,
                        (
                            agg.week_end,
                            agg.sessions,
                            agg.artifacts,
                            agg.decisions,
                            agg.executions,
                            agg.loops,
                            agg.hours_saved,
                            agg.career_points,
                            agg.legal_points,
                            agg.revenue_points,
                            agg.impact_points,
                            agg.loop_rate,
                            agg.snr,
                            agg.output_score,
                            agg.efficiency_score,
                            agg.impact_score,
                            agg.quality_score,
                            agg.weekly_score,
                            datetime.now().isoformat(),
                            agg.week_start,
                        ),
                    )
                else:
                    self.backend.execute(
                        """
                        INSERT INTO weekly_aggs
                        (week_start, week_end, sessions, artifacts, decisions,
                         executions, loops, hours_saved, career_points, legal_points,
                         revenue_points, impact_points, loop_rate, snr,
                         output_score, efficiency_score, impact_score, quality_score,
                         weekly_score, computed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            agg.week_start,
                            agg.week_end,
                            agg.sessions,
                            agg.artifacts,
                            agg.decisions,
                            agg.executions,
                            agg.loops,
                            agg.hours_saved,
                            agg.career_points,
                            agg.legal_points,
                            agg.revenue_points,
                            agg.impact_points,
                            agg.loop_rate,
                            agg.snr,
                            agg.output_score,
                            agg.efficiency_score,
                            agg.impact_score,
                            agg.quality_score,
                            agg.weekly_score,
                            datetime.now().isoformat(),
                        ),
                    )
            logger.info(f"Upserted weekly aggregate for {agg.week_start}")
        except Exception as e:
            logger.error(f"Failed to upsert weekly aggregate: {e}")
            raise

    def get_weekly_aggregate(self, week_start_date: date) -> Optional[WeeklyAgg]:
        """Get a specific weekly aggregate.

        Args:
            week_start_date: The Monday of the week

        Returns:
            WeeklyAgg if found, None otherwise
        """
        start, _ = week_window(week_start_date)
        row = self.backend.fetchone(
            "SELECT * FROM weekly_aggs WHERE week_start = ?",
            (start.isoformat(),),
        )
        if not row:
            return None
        return self._row_to_weekly_agg(row)

    def list_weekly_aggregates(self, limit: int = 12) -> List[WeeklyAgg]:
        """List recent weekly aggregates.

        Args:
            limit: Maximum number of weeks to return

        Returns:
            List of WeeklyAgg, most recent first
        """
        rows = self.backend.fetchall(
            """
            SELECT * FROM weekly_aggs
            ORDER BY week_start DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [self._row_to_weekly_agg(row) for row in rows]

    def _row_to_weekly_agg(self, row: Dict[str, Any]) -> WeeklyAgg:
        """Convert a database row to a WeeklyAgg."""
        return WeeklyAgg(
            week_start=row["week_start"],
            week_end=row["week_end"],
            sessions=row.get("sessions", 0),
            artifacts=row.get("artifacts", 0),
            decisions=row.get("decisions", 0),
            executions=row.get("executions", 0),
            loops=row.get("loops", 0),
            hours_saved=float(row.get("hours_saved", 0.0)),
            career_points=row.get("career_points", 0),
            legal_points=row.get("legal_points", 0),
            revenue_points=row.get("revenue_points", 0),
            impact_points=row.get("impact_points", 0),
            loop_rate=float(row.get("loop_rate", 0.0)),
            snr=float(row.get("snr", 0.0)),
            output_score=float(row.get("output_score", 0.0)),
            efficiency_score=float(row.get("efficiency_score", 0.0)),
            impact_score=float(row.get("impact_score", 0.0)),
            quality_score=float(row.get("quality_score", 0.0)),
            weekly_score=row.get("weekly_score", 0),
        )

    def get_ops_stats(self) -> Dict[str, Any]:
        """Get overall ops statistics.

        Returns:
            Dictionary with total counts and averages
        """
        # Total ops events
        total_row = self.backend.fetchone(
            "SELECT COUNT(*) as count FROM ops_events",
            (),
        )
        total_events = total_row["count"] if total_row else 0

        # Events by project
        project_rows = self.backend.fetchall(
            """
            SELECT project, COUNT(*) as count
            FROM ops_events
            GROUP BY project
            """,
            (),
        )
        by_project = {row["project"]: row["count"] for row in project_rows}

        # Average weekly score
        avg_row = self.backend.fetchone(
            "SELECT AVG(weekly_score) as avg_score FROM weekly_aggs",
            (),
        )
        avg_score = avg_row["avg_score"] if avg_row and avg_row["avg_score"] else 0

        return {
            "total_events": total_events,
            "events_by_project": by_project,
            "average_weekly_score": round(avg_score, 1),
        }
