"""Weekly aggregation logic for AI Ops scorecard."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Iterable

from test_ai.ops.scoring import WeeklyInputs, compute_weekly_scores


def week_window(d: date) -> tuple[date, date]:
    """
    Get the Monday-Sunday week window containing the given date.

    Args:
        d: Any date within the desired week

    Returns:
        Tuple of (week_start, week_end) where week_start is Monday
        and week_end is the following Monday (exclusive)
    """
    # Monday-start week: subtract weekday() to get Monday
    start = date.fromordinal(d.toordinal() - d.weekday())
    # End is the next Monday (exclusive)
    end = date.fromordinal(start.toordinal() + 7)
    return start, end


def parse_date(d: str | date | datetime) -> date:
    """Parse a date from various formats."""
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        return date.fromisoformat(d)
    raise ValueError(f"Cannot parse date from {type(d)}: {d}")


def aggregate_week(
    sessions_count: int,
    ops_events: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Aggregate ops events for a week and compute scores.

    Args:
        sessions_count: Total number of sessions in the week
        ops_events: Iterable of ops event dictionaries

    Returns:
        Dictionary with all aggregate metrics and computed scores
    """
    artifacts = 0
    decisions = 0
    executions = 0
    loops = 0
    minutes_saved = 0
    career = 0
    legal = 0
    revenue = 0

    for e in ops_events:
        artifacts += 1 if e.get("artifact") else 0
        decisions += 1 if e.get("decision_closed") else 0
        executions += 1 if e.get("execution_done") else 0
        loops += 1 if e.get("loop") else 0
        minutes_saved += int(e.get("minutes_saved") or 0)

        # Handle impact - could be dict or separate fields
        impact = e.get("impact")
        if isinstance(impact, dict):
            career += int(impact.get("career") or 0)
            legal += int(impact.get("legal") or 0)
            revenue += int(impact.get("revenue") or 0)
        else:
            # Separate fields
            career += int(e.get("impact_career") or 0)
            legal += int(e.get("impact_legal") or 0)
            revenue += int(e.get("impact_revenue") or 0)

    hours_saved = minutes_saved / 60.0
    impact_points = career + legal + revenue

    # Compute scores
    inp = WeeklyInputs(
        sessions=sessions_count,
        artifacts=artifacts,
        decisions=decisions,
        executions=executions,
        hours_saved=hours_saved,
        loops=loops,
        impact_points=impact_points,
    )
    scores = compute_weekly_scores(inp)

    return {
        "sessions": sessions_count,
        "artifacts": artifacts,
        "decisions": decisions,
        "executions": executions,
        "hours_saved": round(hours_saved, 2),
        "loops": loops,
        "career_points": career,
        "legal_points": legal,
        "revenue_points": revenue,
        "impact_points": impact_points,
        "loop_rate": round(scores.loop_rate, 4),
        "snr": round(scores.snr, 4),
        "output_score": round(scores.output_score, 1),
        "efficiency_score": round(scores.efficiency_score, 1),
        "impact_score": round(scores.impact_score, 1),
        "quality_score": round(scores.quality_score, 1),
        "weekly_score": scores.weekly_score,
    }
