"""Cost and Token Budget Management.

Track, allocate, and enforce token budgets across workflow executions.
"""

from .manager import BudgetManager, BudgetConfig, UsageRecord, BudgetStatus
from .strategies import (
    AllocationStrategy,
    EqualAllocation,
    PriorityAllocation,
    AdaptiveAllocation,
)
from .preflight import (
    PreflightValidator,
    ValidationResult,
    ValidationStatus,
    WorkflowEstimate,
    StepEstimate,
    validate_workflow_budget,
)

# Singleton budget tracker instance
_budget_tracker: BudgetManager | None = None


def get_budget_tracker() -> BudgetManager:
    """Get the global budget tracker instance.

    Returns:
        BudgetManager singleton instance
    """
    global _budget_tracker
    if _budget_tracker is None:
        _budget_tracker = BudgetManager()
    return _budget_tracker


__all__ = [
    "BudgetManager",
    "BudgetConfig",
    "BudgetStatus",
    "UsageRecord",
    "AllocationStrategy",
    "EqualAllocation",
    "PriorityAllocation",
    "AdaptiveAllocation",
    "PreflightValidator",
    "ValidationResult",
    "ValidationStatus",
    "WorkflowEstimate",
    "StepEstimate",
    "validate_workflow_budget",
    "get_budget_tracker",
]
