"""Data models for AI Ops Scorecard."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ProjectType(str, Enum):
    """Project categories for ops events."""

    CAREER = "career"
    LEGAL = "legal"
    CHEFWISE = "chefwise"
    GORGON = "gorgon"
    OTHER = "other"


class ArtifactType(str, Enum):
    """Types of artifacts that can be created."""

    DOC = "doc"
    PROMPT = "prompt"
    SCRIPT = "script"
    CODE = "code"
    TEMPLATE = "template"
    OTHER = "other"


class OpsEvent(BaseModel):
    """
    An ops event representing a meaningful session outcome.

    OpsEvents are manually logged to record human judgment about
    what was accomplished in a session. They capture:
    - Whether an artifact was produced
    - Whether a decision was closed
    - Whether execution was completed
    - Time saved
    - Impact across different areas
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the ops event",
    )
    session_id: str = Field(..., description="Associated session ID")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the ops event was logged",
    )
    project: ProjectType = Field(
        ProjectType.OTHER,
        description="Project category",
    )

    # Output flags
    artifact: bool = Field(False, description="Was an artifact produced?")
    artifact_type: Optional[ArtifactType] = Field(
        None,
        description="Type of artifact (required if artifact=True)",
    )
    reusable: bool = Field(False, description="Is the artifact reusable?")

    # Outcome flags
    decision_closed: bool = Field(False, description="Was a decision closed?")
    execution_done: bool = Field(False, description="Was execution completed?")

    # Efficiency metrics
    minutes_saved: int = Field(
        0,
        ge=0,
        description="Estimated minutes saved",
    )
    loop: bool = Field(
        False,
        description="Was this a loop/redo (negative signal)?",
    )

    # Impact points by area
    impact_career: int = Field(0, ge=0, description="Career impact points")
    impact_legal: int = Field(0, ge=0, description="Legal impact points")
    impact_revenue: int = Field(0, ge=0, description="Revenue impact points")

    @field_validator("artifact_type")
    @classmethod
    def validate_artifact_type(
        cls, v: Optional[ArtifactType], info
    ) -> Optional[ArtifactType]:
        """Artifact type is required if artifact is True."""
        # Note: We can't fully validate this here since we need artifact field
        # The manager will handle cross-field validation
        return v

    @property
    def impact_total(self) -> int:
        """Total impact points across all areas."""
        return self.impact_career + self.impact_legal + self.impact_revenue

    class Config:
        """Pydantic config."""

        use_enum_values = True


class WeeklyAgg(BaseModel):
    """
    Weekly aggregate of ops metrics and computed scores.

    Computed from sessions and ops events in a week window.
    Used for the weekly AI Ops scorecard display.
    """

    week_start: str = Field(..., description="Week start date (YYYY-MM-DD)")
    week_end: str = Field(..., description="Week end date (YYYY-MM-DD)")

    # Raw counts
    sessions: int = Field(0, ge=0, description="Total sessions in the week")
    artifacts: int = Field(0, ge=0, description="Count of artifacts produced")
    decisions: int = Field(0, ge=0, description="Count of decisions closed")
    executions: int = Field(0, ge=0, description="Count of executions completed")
    loops: int = Field(0, ge=0, description="Count of loops (negative)")

    # Time metrics
    hours_saved: float = Field(0.0, ge=0.0, description="Hours saved")

    # Impact by area
    career_points: int = Field(0, ge=0, description="Career impact points")
    legal_points: int = Field(0, ge=0, description="Legal impact points")
    revenue_points: int = Field(0, ge=0, description="Revenue impact points")
    impact_points: int = Field(0, ge=0, description="Total impact points")

    # Derived metrics
    loop_rate: float = Field(0.0, ge=0.0, description="Loops / sessions ratio")
    snr: float = Field(
        0.0, ge=0.0, description="Signal-to-noise ratio (outputs / sessions)"
    )

    # Component scores (0-100)
    output_score: float = Field(0.0, ge=0.0, le=100.0, description="Output score")
    efficiency_score: float = Field(
        0.0, ge=0.0, le=100.0, description="Efficiency score"
    )
    impact_score: float = Field(0.0, ge=0.0, le=100.0, description="Impact score")
    quality_score: float = Field(0.0, ge=0.0, le=100.0, description="Quality score")

    # Final score
    weekly_score: int = Field(0, ge=0, le=100, description="Final weekly score (0-100)")

    class Config:
        """Pydantic config."""

        use_enum_values = True
