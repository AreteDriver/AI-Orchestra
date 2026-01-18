"""Outbound Notifications for Workflow Events.

Send notifications to Slack, Discord, and other services when workflow events occur.
"""

from .notifier import (
    Notifier,
    NotificationEvent,
    NotificationChannel,
    EventType,
    SlackChannel,
    DiscordChannel,
    WebhookChannel,
)

__all__ = [
    "Notifier",
    "NotificationEvent",
    "NotificationChannel",
    "EventType",
    "SlackChannel",
    "DiscordChannel",
    "WebhookChannel",
]
