"""Data Collectors for Analytics Pipelines.

Provides modular data collection components that can be used in analytics pipelines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class CollectedData:
    """Container for collected data."""

    source: str
    collected_at: datetime
    data: dict[str, Any]
    metadata: dict[str, Any]

    def to_context_string(self) -> str:
        """Convert to string format for AI agent context."""
        lines = [
            f"# Data Collection: {self.source}",
            f"Collected: {self.collected_at.isoformat()}",
            "",
        ]

        for key, value in self.data.items():
            lines.append(f"## {key}")
            if isinstance(value, dict):
                for k, v in value.items():
                    lines.append(f"- {k}: {v}")
            elif isinstance(value, list):
                for item in value[:10]:  # Limit to 10 items
                    lines.append(f"- {item}")
                if len(value) > 10:
                    lines.append(f"- ... and {len(value) - 10} more")
            else:
                lines.append(str(value))
            lines.append("")

        return "\n".join(lines)


class DataCollector(ABC):
    """Abstract base class for data collectors."""

    @abstractmethod
    def collect(self, context: Any, config: dict) -> CollectedData:
        """Collect data from the source.

        Args:
            context: Previous stage output or initial context
            config: Collector configuration

        Returns:
            CollectedData with collected information
        """
        pass


class JSONCollector(DataCollector):
    """Collector that accepts JSON data directly (for testing/manual input)."""

    def collect(self, context: Any, config: dict) -> CollectedData:
        """Pass through JSON data.

        Config options:
            data: dict - The data to pass through
            source_name: str - Name for the data source
        """
        data = config.get("data", context if isinstance(context, dict) else {})
        source_name = config.get("source_name", "json_input")

        return CollectedData(
            source=source_name,
            collected_at=datetime.now(timezone.utc),
            data=data,
            metadata={"type": "json_passthrough"},
        )


class AggregateCollector(DataCollector):
    """Collector that aggregates data from multiple collectors."""

    def __init__(self, collectors: list[DataCollector]):
        self.collectors = collectors

    def collect(self, context: Any, config: dict) -> CollectedData:
        """Collect and aggregate data from all child collectors.

        Config options:
            collector_configs: dict[int, dict] - Config for each collector by index
        """
        collector_configs = config.get("collector_configs", {})

        aggregated_data = {}

        for i, collector in enumerate(self.collectors):
            collector_config = collector_configs.get(i, {})
            result = collector.collect(context, collector_config)
            aggregated_data[result.source] = result.data

        return CollectedData(
            source="aggregate",
            collected_at=datetime.now(timezone.utc),
            data=aggregated_data,
            metadata={"collector_count": len(self.collectors)},
        )
