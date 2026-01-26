"""Outbound Notifications for Workflow Events.

Send notifications to Slack, Discord, Teams, Email, PagerDuty, and other services
when workflow events occur.
"""

from .notifier import (
    Notifier,
    NotificationEvent,
    NotificationChannel,
    EventType,
    SlackChannel,
    DiscordChannel,
    WebhookChannel,
    EmailChannel,
    TeamsChannel,
    PagerDutyChannel,
)

__all__ = [
    "Notifier",
    "NotificationEvent",
    "NotificationChannel",
    "EventType",
    "SlackChannel",
    "DiscordChannel",
    "WebhookChannel",
    "EmailChannel",
    "TeamsChannel",
    "PagerDutyChannel",
]
