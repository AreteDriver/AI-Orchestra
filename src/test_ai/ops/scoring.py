"""Scoring logic for weekly AI Ops scorecard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


TARGETS_DEFAULT: Dict[str, float] = {
    "output": 18,  # artifacts + decisions + executions cap
    "hours_saved": 6,
    "impact": 10,
    "loop_rate": 0.2,
    "snr": 0.6,
}


def clamp01(x: float) -> float:
    """Clamp value between 0 and 1."""
    if x < 0:
        return 0.0
    if x > 1:
        return 1.0
    return x


@dataclass(frozen=True)
class WeeklyInputs:
    """Input metrics for weekly score computation."""

    sessions: int
    artifacts: int
    decisions: int
    executions: int
    hours_saved: float
    loops: int
    impact_points: int


@dataclass(frozen=True)
class WeeklyScores:
    """Computed weekly scores and derived metrics."""

    loop_rate: float
    snr: float
    output_score: float
    efficiency_score: float
    impact_score: float
    quality_score: float
    weekly_score: int


def compute_weekly_scores(
    inp: WeeklyInputs,
    targets: Dict[str, float] | None = None,
) -> WeeklyScores:
    """
    Compute weekly scores from input metrics.

    Args:
        inp: Weekly input metrics
        targets: Optional custom targets (uses TARGETS_DEFAULT if not provided)

    Returns:
        WeeklyScores with all derived metrics and component scores
    """
    if targets is None:
        targets = TARGETS_DEFAULT

    # Avoid division by zero
    denom_sessions = max(inp.sessions, 1)

    # Derived metrics
    loop_rate = inp.loops / denom_sessions
    total_outputs = inp.artifacts + inp.decisions + inp.executions
    snr = total_outputs / denom_sessions

    # Component scores (0-100)
    output_score = clamp01(total_outputs / targets["output"]) * 100.0

    efficiency_score = (
        clamp01(inp.hours_saved / targets["hours_saved"])
        + clamp01(1.0 - (loop_rate / targets["loop_rate"]))
    ) / 2.0 * 100.0

    impact_score = clamp01(inp.impact_points / targets["impact"]) * 100.0

    quality_score = clamp01(snr / targets["snr"]) * 100.0

    # Final weighted score (0-100)
    weekly_score = round(
        0.35 * output_score
        + 0.20 * efficiency_score
        + 0.35 * impact_score
        + 0.10 * quality_score
    )

    return WeeklyScores(
        loop_rate=loop_rate,
        snr=snr,
        output_score=output_score,
        efficiency_score=efficiency_score,
        impact_score=impact_score,
        quality_score=quality_score,
        weekly_score=weekly_score,
    )
