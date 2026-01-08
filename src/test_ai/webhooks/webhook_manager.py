"""Webhook trigger manager for event-driven workflow execution."""

import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from test_ai.config import get_settings
from test_ai.orchestrator import WorkflowEngine

logger = logging.getLogger(__name__)


class WebhookStatus(str, Enum):
    """Webhook status."""

    ACTIVE = "active"
    DISABLED = "disabled"


class PayloadMapping(BaseModel):
    """Maps incoming webhook payload fields to workflow variables."""

    source_path: str = Field(
        ..., description="JSON path in payload (e.g., 'data.user.id')"
    )
    target_variable: str = Field(..., description="Workflow variable name")
    default: Optional[Any] = Field(None, description="Default value if path not found")


class Webhook(BaseModel):
    """A webhook definition."""

    id: str = Field(..., description="Webhook identifier (used in URL)")
    name: str = Field(..., description="Webhook name")
    description: str = Field("", description="Webhook description")
    workflow_id: str = Field(..., description="Workflow to trigger")
    secret: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret for signature verification",
    )
    payload_mappings: List[PayloadMapping] = Field(
        default_factory=list, description="Map payload fields to workflow variables"
    )
    static_variables: Dict[str, Any] = Field(
        default_factory=dict, description="Static variables to pass to workflow"
    )
    status: WebhookStatus = Field(WebhookStatus.ACTIVE, description="Webhook status")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    last_triggered: Optional[datetime] = Field(
        None, description="Last trigger timestamp"
    )
    trigger_count: int = Field(0, ge=0, description="Total trigger count")


class WebhookTriggerLog(BaseModel):
    """Log entry for a webhook trigger."""

    webhook_id: str
    workflow_id: str
    triggered_at: datetime
    source_ip: Optional[str] = None
    payload_size: int
    status: str
    duration_seconds: float
    error: Optional[str] = None


class WebhookManager:
    """Manages webhook definitions and triggers."""

    def __init__(self):
        self.settings = get_settings()
        self.webhooks_dir = self.settings.webhooks_dir
        self.webhooks_dir.mkdir(parents=True, exist_ok=True)
        self.workflow_engine = WorkflowEngine()
        self._webhooks: Dict[str, Webhook] = {}
        self._load_all_webhooks()

    def _load_all_webhooks(self):
        """Load all webhooks from disk."""
        for file_path in self.webhooks_dir.glob("*.json"):
            try:
                webhook = self._load_webhook_file(file_path)
                if webhook:
                    self._webhooks[webhook.id] = webhook
            except Exception as e:
                logger.error(f"Failed to load webhook {file_path}: {e}")

    def _load_webhook_file(self, file_path: Path) -> Optional[Webhook]:
        """Load a webhook from file."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return Webhook(**data)
        except Exception:
            return None

    def _save_webhook(self, webhook: Webhook) -> bool:
        """Save a webhook to disk."""
        try:
            file_path = self.webhooks_dir / f"{webhook.id}.json"
            with open(file_path, "w") as f:
                json.dump(webhook.model_dump(mode="json"), f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save webhook {webhook.id}: {e}")
            return False

    def create_webhook(self, webhook: Webhook) -> bool:
        """Create a new webhook."""
        # Validate workflow exists
        workflow = self.workflow_engine.load_workflow(webhook.workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {webhook.workflow_id} not found")

        # Check for duplicate ID
        if webhook.id in self._webhooks:
            raise ValueError(f"Webhook {webhook.id} already exists")

        webhook.created_at = datetime.now()
        if self._save_webhook(webhook):
            self._webhooks[webhook.id] = webhook
            return True
        return False

    def update_webhook(self, webhook: Webhook) -> bool:
        """Update an existing webhook."""
        if webhook.id not in self._webhooks:
            raise ValueError(f"Webhook {webhook.id} not found")

        # Preserve creation time, trigger count, and secret if not provided
        existing = self._webhooks[webhook.id]
        webhook.created_at = existing.created_at
        webhook.trigger_count = existing.trigger_count
        webhook.last_triggered = existing.last_triggered
        if webhook.secret == "":
            webhook.secret = existing.secret

        if self._save_webhook(webhook):
            self._webhooks[webhook.id] = webhook
            return True
        return False

    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        if webhook_id not in self._webhooks:
            return False

        file_path = self.webhooks_dir / f"{webhook_id}.json"
        try:
            file_path.unlink()
        except Exception:
            pass

        del self._webhooks[webhook_id]
        return True

    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get a webhook by ID."""
        return self._webhooks.get(webhook_id)

    def list_webhooks(self) -> List[Dict]:
        """List all webhooks (without secrets)."""
        webhooks = []
        for webhook in self._webhooks.values():
            webhooks.append(
                {
                    "id": webhook.id,
                    "name": webhook.name,
                    "workflow_id": webhook.workflow_id,
                    "status": webhook.status.value,
                    "last_triggered": webhook.last_triggered.isoformat()
                    if webhook.last_triggered
                    else None,
                    "trigger_count": webhook.trigger_count,
                }
            )
        return webhooks

    def verify_signature(self, webhook_id: str, payload: bytes, signature: str) -> bool:
        """Verify webhook signature using HMAC-SHA256."""
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            return False

        expected = hmac.new(
            webhook.secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        # Support both raw hex and prefixed formats
        if signature.startswith("sha256="):
            signature = signature[7:]

        return hmac.compare_digest(expected, signature)

    def generate_signature(self, webhook_id: str, payload: bytes) -> str:
        """Generate signature for a payload (useful for testing)."""
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            raise ValueError(f"Webhook {webhook_id} not found")

        return (
            "sha256="
            + hmac.new(webhook.secret.encode(), payload, hashlib.sha256).hexdigest()
        )

    def _extract_payload_value(self, payload: Dict, path: str) -> Any:
        """Extract value from payload using dot notation path."""
        keys = path.split(".")
        value = payload
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    def _map_payload_to_variables(
        self, webhook: Webhook, payload: Dict
    ) -> Dict[str, Any]:
        """Map webhook payload to workflow variables."""
        variables = webhook.static_variables.copy()

        for mapping in webhook.payload_mappings:
            value = self._extract_payload_value(payload, mapping.source_path)
            if value is not None:
                variables[mapping.target_variable] = value
            elif mapping.default is not None:
                variables[mapping.target_variable] = mapping.default

        return variables

    def trigger(
        self,
        webhook_id: str,
        payload: Dict,
        source_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Trigger a webhook and execute the associated workflow."""
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            raise ValueError(f"Webhook {webhook_id} not found")

        if webhook.status != WebhookStatus.ACTIVE:
            raise ValueError(f"Webhook {webhook_id} is disabled")

        logger.info(f"Triggering webhook: {webhook_id} -> {webhook.workflow_id}")
        start_time = datetime.now()
        error_msg = None
        status = "success"

        try:
            workflow = self.workflow_engine.load_workflow(webhook.workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {webhook.workflow_id} not found")

            # Map payload to variables
            variables = self._map_payload_to_variables(webhook, payload)
            workflow.variables.update(variables)

            result = self.workflow_engine.execute_workflow(workflow)
            status = result.status
            workflow_result = result.model_dump(mode="json")

        except Exception as e:
            logger.error(f"Webhook trigger failed: {e}")
            status = "failed"
            error_msg = str(e)
            workflow_result = None

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Update webhook stats
        webhook.last_triggered = start_time
        webhook.trigger_count += 1
        self._save_webhook(webhook)
        self._webhooks[webhook_id] = webhook

        # Log trigger
        self._save_trigger_log(
            WebhookTriggerLog(
                webhook_id=webhook_id,
                workflow_id=webhook.workflow_id,
                triggered_at=start_time,
                source_ip=source_ip,
                payload_size=len(json.dumps(payload)),
                status=status,
                duration_seconds=duration,
                error=error_msg,
            )
        )

        return {
            "status": status,
            "webhook_id": webhook_id,
            "workflow_id": webhook.workflow_id,
            "duration_seconds": duration,
            "result": workflow_result,
            "error": error_msg,
        }

    def _save_trigger_log(self, log: WebhookTriggerLog):
        """Save trigger log entry."""
        logs_dir = self.settings.logs_dir / "webhooks"
        logs_dir.mkdir(parents=True, exist_ok=True)

        log_file = (
            logs_dir
            / f"{log.webhook_id}_{log.triggered_at.strftime('%Y%m%d_%H%M%S')}.json"
        )
        try:
            with open(log_file, "w") as f:
                json.dump(log.model_dump(mode="json"), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save trigger log: {e}")

    def get_trigger_history(
        self, webhook_id: str, limit: int = 10
    ) -> List[WebhookTriggerLog]:
        """Get trigger history for a webhook."""
        logs_dir = self.settings.logs_dir / "webhooks"
        if not logs_dir.exists():
            return []

        logs = []
        for file_path in sorted(logs_dir.glob(f"{webhook_id}_*.json"), reverse=True)[
            :limit
        ]:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                logs.append(WebhookTriggerLog(**data))
            except Exception:
                continue

        return logs

    def regenerate_secret(self, webhook_id: str) -> str:
        """Regenerate the secret for a webhook."""
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            raise ValueError(f"Webhook {webhook_id} not found")

        webhook.secret = secrets.token_urlsafe(32)
        self._save_webhook(webhook)
        self._webhooks[webhook_id] = webhook
        return webhook.secret
