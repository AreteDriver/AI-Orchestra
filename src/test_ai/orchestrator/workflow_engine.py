"""Workflow models for orchestration.

These models define the structure of workflows, steps, and results.
For execution, use WorkflowEngineAdapter or WorkflowExecutor.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StepType(str, Enum):
    """Types of workflow steps."""

    OPENAI = "openai"
    GITHUB = "github"
    NOTION = "notion"
    GMAIL = "gmail"
    TRANSFORM = "transform"
    CLAUDE_CODE = "claude_code"


class WorkflowStep(BaseModel):
    """A single step in a workflow."""

    id: str = Field(..., description="Step identifier")
    type: StepType = Field(..., description="Step type")
    action: str = Field(..., description="Action to perform")
    params: Dict[str, Any] = Field(default_factory=dict, description="Step parameters")
    next_step: Optional[str] = Field(None, description="Next step ID")


class Workflow(BaseModel):
    """A workflow definition."""

    id: str = Field(..., description="Workflow identifier")
    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    steps: List[WorkflowStep] = Field(
        default_factory=list, description="Workflow steps"
    )
    variables: Dict[str, Any] = Field(
        default_factory=dict, description="Workflow variables"
    )


class WorkflowResult(BaseModel):
    """Result of a workflow execution."""

    workflow_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    steps_executed: List[str] = Field(default_factory=list)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
