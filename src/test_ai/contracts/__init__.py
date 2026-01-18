"""Agent Contracts and Validation.

Provides structured handoff formats between agents with JSON Schema validation.
"""

from .base import AgentContract, AgentRole, ContractViolation
from .definitions import (
    PLANNER_CONTRACT,
    BUILDER_CONTRACT,
    TESTER_CONTRACT,
    REVIEWER_CONTRACT,
    get_contract,
)
from .validator import ContractValidator

__all__ = [
    "AgentContract",
    "AgentRole",
    "ContractViolation",
    "ContractValidator",
    "PLANNER_CONTRACT",
    "BUILDER_CONTRACT",
    "TESTER_CONTRACT",
    "REVIEWER_CONTRACT",
    "get_contract",
]
