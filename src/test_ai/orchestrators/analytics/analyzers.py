"""Data Analyzers for Analytics Pipelines.

Provides modular analysis components for processing collected data.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AnalysisResult:
    """Container for analysis results."""

    analyzer: str
    analyzed_at: datetime
    findings: list[dict[str, Any]]
    metrics: dict[str, Any]
    recommendations: list[str]
    severity: str  # "info", "warning", "critical"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_context_string(self) -> str:
        """Convert to string format for AI agent context."""
        lines = [
            f"# Analysis Results: {self.analyzer}",
            f"Analyzed: {self.analyzed_at.isoformat()}",
            f"Overall Severity: {self.severity.upper()}",
            "",
            "## Key Findings",
        ]

        for finding in self.findings:
            severity = finding.get("severity", "info")
            message = finding.get("message", "")
            lines.append(f"- [{severity.upper()}] {message}")

        lines.append("")
        lines.append("## Metrics")
        for key, value in self.metrics.items():
            lines.append(f"- {key}: {value}")

        if self.recommendations:
            lines.append("")
            lines.append("## Recommendations")
            for rec in self.recommendations:
                lines.append(f"- {rec}")

        return "\n".join(lines)


class DataAnalyzer(ABC):
    """Abstract base class for data analyzers."""

    @abstractmethod
    def analyze(self, data: Any, config: dict) -> AnalysisResult:
        """Analyze the collected data.

        Args:
            data: CollectedData or previous stage output
            config: Analyzer configuration

        Returns:
            AnalysisResult with findings and recommendations
        """
        pass


class TrendAnalyzer(DataAnalyzer):
    """Analyzer for identifying trends in metrics data."""

    def analyze(self, data: Any, config: dict) -> AnalysisResult:
        """Analyze metrics for trends.

        Config options:
            trend_window: int - Number of data points to consider (default: 10)
            change_threshold: float - Percent change to flag as significant (default: 0.2)
        """
        _change_threshold = config.get("change_threshold", 0.2)  # noqa: F841

        findings = []
        metrics = {}
        recommendations = []
        max_severity = "info"

        # Handle different input types
        if hasattr(data, "data"):
            source_data = data.data
        elif isinstance(data, dict):
            source_data = data
        else:
            source_data = {}

        # Analyze timing metrics for performance trends
        app_metrics = source_data.get("metrics", source_data.get("app_performance", {}))

        if isinstance(app_metrics, dict):
            timing = app_metrics.get("timing", {})

            for metric_name, timing_data in timing.items():
                if isinstance(timing_data, dict):
                    avg_ms = timing_data.get("avg_ms", 0)
                    max_ms = timing_data.get("max_ms", 0)
                    count = timing_data.get("count", 0)

                    metrics[f"{metric_name}_avg"] = avg_ms
                    metrics[f"{metric_name}_count"] = count

                    # Flag slow operations
                    if avg_ms > 1000:  # Over 1 second
                        if max_severity == "info":
                            max_severity = "warning"
                        findings.append(
                            {
                                "severity": "warning",
                                "category": "performance",
                                "message": f"Slow operation: {metric_name} averaging {avg_ms:.0f}ms",
                                "data": timing_data,
                            }
                        )
                        recommendations.append(
                            f"Investigate performance of {metric_name}"
                        )

                    # Flag high variance
                    if max_ms > avg_ms * 3 and count > 5:
                        findings.append(
                            {
                                "severity": "info",
                                "category": "variance",
                                "message": f"High variance in {metric_name}: max {max_ms:.0f}ms vs avg {avg_ms:.0f}ms",
                            }
                        )

            # Analyze counters for error trends
            counters = app_metrics.get("counters", {})
            for counter_name, value in counters.items():
                if "error" in counter_name.lower():
                    if value > 0:
                        findings.append(
                            {
                                "severity": "warning",
                                "category": "errors",
                                "message": f"Error counter {counter_name}: {value}",
                            }
                        )
                        if max_severity == "info":
                            max_severity = "warning"

        if not findings:
            findings.append(
                {
                    "severity": "info",
                    "category": "trends",
                    "message": "No significant trends detected",
                }
            )

        return AnalysisResult(
            analyzer="trends",
            analyzed_at=datetime.now(timezone.utc),
            findings=findings,
            metrics=metrics,
            recommendations=recommendations,
            severity=max_severity,
        )


class ThresholdAnalyzer(DataAnalyzer):
    """Analyzer that checks metrics against configurable thresholds."""

    def analyze(self, data: Any, config: dict) -> AnalysisResult:
        """Analyze data against threshold rules.

        Config options:
            thresholds: dict[str, dict] - Threshold definitions
                key: metric path (dot notation)
                value: {"warning": float, "critical": float, "direction": "above"|"below"}
        """
        thresholds = config.get("thresholds", {})

        findings = []
        metrics = {}
        recommendations = []
        max_severity = "info"

        # Handle different input types
        if hasattr(data, "data"):
            source_data = data.data
        elif isinstance(data, dict):
            source_data = data
        else:
            source_data = {}

        def get_nested(d: dict, path: str) -> Any:
            """Get value from nested dict using dot notation."""
            keys = path.split(".")
            current = d
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            return current

        for metric_path, threshold_config in thresholds.items():
            value = get_nested(source_data, metric_path)
            if value is None:
                continue

            metrics[metric_path] = value

            warning_threshold = threshold_config.get("warning")
            critical_threshold = threshold_config.get("critical")
            direction = threshold_config.get("direction", "above")

            if direction == "above":
                if critical_threshold is not None and value >= critical_threshold:
                    max_severity = "critical"
                    findings.append(
                        {
                            "severity": "critical",
                            "category": "threshold",
                            "message": f"{metric_path} = {value} exceeds critical threshold {critical_threshold}",
                        }
                    )
                    recommendations.append(f"Investigate critical {metric_path}")
                elif warning_threshold is not None and value >= warning_threshold:
                    if max_severity != "critical":
                        max_severity = "warning"
                    findings.append(
                        {
                            "severity": "warning",
                            "category": "threshold",
                            "message": f"{metric_path} = {value} exceeds warning threshold {warning_threshold}",
                        }
                    )
            else:  # direction == "below"
                if critical_threshold is not None and value <= critical_threshold:
                    max_severity = "critical"
                    findings.append(
                        {
                            "severity": "critical",
                            "category": "threshold",
                            "message": f"{metric_path} = {value} below critical threshold {critical_threshold}",
                        }
                    )
                    recommendations.append(f"Investigate critical {metric_path}")
                elif warning_threshold is not None and value <= warning_threshold:
                    if max_severity != "critical":
                        max_severity = "warning"
                    findings.append(
                        {
                            "severity": "warning",
                            "category": "threshold",
                            "message": f"{metric_path} = {value} below warning threshold {warning_threshold}",
                        }
                    )

        if not findings:
            findings.append(
                {
                    "severity": "info",
                    "category": "thresholds",
                    "message": "All metrics within acceptable thresholds",
                }
            )

        return AnalysisResult(
            analyzer="threshold",
            analyzed_at=datetime.now(timezone.utc),
            findings=findings,
            metrics=metrics,
            recommendations=recommendations,
            severity=max_severity,
        )


class CompositeAnalyzer(DataAnalyzer):
    """Analyzer that combines results from multiple analyzers."""

    def __init__(self, analyzers: list[DataAnalyzer]):
        self.analyzers = analyzers

    def analyze(self, data: Any, config: dict) -> AnalysisResult:
        """Run all analyzers and combine results.

        Config options:
            analyzer_configs: dict[int, dict] - Config for each analyzer by index
        """
        analyzer_configs = config.get("analyzer_configs", {})

        all_findings = []
        all_metrics = {}
        all_recommendations = []
        max_severity = "info"

        severity_order = {"info": 0, "warning": 1, "critical": 2}

        for i, analyzer in enumerate(self.analyzers):
            analyzer_config = analyzer_configs.get(i, {})
            result = analyzer.analyze(data, analyzer_config)

            all_findings.extend(result.findings)
            all_metrics.update(result.metrics)
            all_recommendations.extend(result.recommendations)

            if severity_order.get(result.severity, 0) > severity_order.get(
                max_severity, 0
            ):
                max_severity = result.severity

        # Deduplicate recommendations
        unique_recommendations = list(dict.fromkeys(all_recommendations))

        return AnalysisResult(
            analyzer="composite",
            analyzed_at=datetime.now(timezone.utc),
            findings=all_findings,
            metrics=all_metrics,
            recommendations=unique_recommendations,
            severity=max_severity,
            metadata={"analyzer_count": len(self.analyzers)},
        )
