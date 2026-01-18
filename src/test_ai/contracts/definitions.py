"""Predefined agent contracts for standard roles."""

from __future__ import annotations

from .base import AgentContract, AgentRole


PLANNER_CONTRACT = AgentContract(
    role=AgentRole.PLANNER,
    description="Plans implementation by breaking down requests into tasks",
    input_schema={
        "type": "object",
        "required": ["request", "context"],
        "properties": {
            "request": {
                "type": "string",
                "minLength": 1,
                "description": "The user's request or feature description",
            },
            "context": {
                "type": "object",
                "description": "Current codebase/project context",
            },
            "constraints": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Constraints or requirements to consider",
            },
        },
    },
    output_schema={
        "type": "object",
        "required": ["tasks", "architecture", "success_criteria"],
        "properties": {
            "tasks": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["id", "description", "dependencies"],
                    "properties": {
                        "id": {"type": "string"},
                        "description": {"type": "string"},
                        "dependencies": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "estimated_complexity": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                    },
                },
            },
            "architecture": {
                "type": "string",
                "description": "High-level architecture description",
            },
            "success_criteria": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
            },
            "risks": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
    required_context=["codebase_summary"],
)


BUILDER_CONTRACT = AgentContract(
    role=AgentRole.BUILDER,
    description="Implements code based on the plan",
    input_schema={
        "type": "object",
        "required": ["plan", "task_id"],
        "properties": {
            "plan": {
                "type": "object",
                "description": "The plan from the planner agent",
            },
            "task_id": {
                "type": "string",
                "description": "ID of the task to implement",
            },
            "previous_attempts": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Previous failed attempts with feedback",
            },
            "feedback": {
                "type": "string",
                "description": "Feedback from tester/reviewer",
            },
        },
    },
    output_schema={
        "type": "object",
        "required": ["code", "files_created", "status"],
        "properties": {
            "code": {
                "type": "string",
                "description": "The implemented code",
            },
            "files_created": {
                "type": "array",
                "items": {"type": "string"},
            },
            "files_modified": {
                "type": "array",
                "items": {"type": "string"},
            },
            "status": {
                "type": "string",
                "enum": ["complete", "partial", "blocked"],
            },
            "notes": {
                "type": "string",
            },
            "dependencies_added": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
    required_context=["plan"],
)


TESTER_CONTRACT = AgentContract(
    role=AgentRole.TESTER,
    description="Tests the implemented code",
    input_schema={
        "type": "object",
        "required": ["code", "success_criteria"],
        "properties": {
            "code": {
                "type": "string",
                "description": "Code to test",
            },
            "files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Files to test",
            },
            "success_criteria": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
            },
            "test_types": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["unit", "integration", "e2e"],
                },
            },
        },
    },
    output_schema={
        "type": "object",
        "required": ["passed", "tests_run", "results"],
        "properties": {
            "passed": {
                "type": "boolean",
            },
            "tests_run": {
                "type": "integer",
                "minimum": 0,
            },
            "tests_passed": {
                "type": "integer",
                "minimum": 0,
            },
            "tests_failed": {
                "type": "integer",
                "minimum": 0,
            },
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "passed"],
                    "properties": {
                        "name": {"type": "string"},
                        "passed": {"type": "boolean"},
                        "error": {"type": "string"},
                        "feedback_for_builder": {"type": "string"},
                    },
                },
            },
            "coverage": {
                "type": "number",
                "minimum": 0,
                "maximum": 100,
            },
            "recommendations": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
    required_context=["code", "success_criteria"],
)


REVIEWER_CONTRACT = AgentContract(
    role=AgentRole.REVIEWER,
    description="Reviews code quality and approves for merge",
    input_schema={
        "type": "object",
        "required": ["code", "plan", "test_results"],
        "properties": {
            "code": {
                "type": "string",
            },
            "plan": {
                "type": "object",
            },
            "test_results": {
                "type": "object",
            },
            "review_focus": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific areas to focus review on",
            },
        },
    },
    output_schema={
        "type": "object",
        "required": ["approved", "score", "findings"],
        "properties": {
            "approved": {
                "type": "boolean",
            },
            "score": {
                "type": "integer",
                "minimum": 1,
                "maximum": 10,
            },
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["severity", "category", "description"],
                    "properties": {
                        "severity": {
                            "type": "string",
                            "enum": ["critical", "major", "minor", "suggestion"],
                        },
                        "category": {"type": "string"},
                        "description": {"type": "string"},
                        "line_number": {"type": "integer"},
                        "suggested_fix": {"type": "string"},
                    },
                },
            },
            "summary": {
                "type": "string",
            },
            "requires_rework": {
                "type": "boolean",
            },
            "rework_instructions": {
                "type": "string",
            },
        },
    },
    required_context=["code", "plan", "test_results"],
)


# Registry of all contracts by role
_CONTRACT_REGISTRY: dict[AgentRole, AgentContract] = {
    AgentRole.PLANNER: PLANNER_CONTRACT,
    AgentRole.BUILDER: BUILDER_CONTRACT,
    AgentRole.TESTER: TESTER_CONTRACT,
    AgentRole.REVIEWER: REVIEWER_CONTRACT,
}


def get_contract(role: AgentRole | str) -> AgentContract:
    """Get the contract for a given role.

    Args:
        role: AgentRole enum or string role name

    Returns:
        The AgentContract for that role

    Raises:
        ValueError: If role is not found
    """
    if isinstance(role, str):
        try:
            role = AgentRole(role)
        except ValueError:
            raise ValueError(f"Unknown role: {role}")

    if role not in _CONTRACT_REGISTRY:
        raise ValueError(f"No contract defined for role: {role.value}")

    return _CONTRACT_REGISTRY[role]


def register_contract(contract: AgentContract) -> None:
    """Register a custom contract for a role.

    Args:
        contract: The AgentContract to register
    """
    _CONTRACT_REGISTRY[contract.role] = contract


def list_contracts() -> list[dict]:
    """List all registered contracts.

    Returns:
        List of contract summaries
    """
    return [
        {
            "role": role.value,
            "description": contract.description,
            "required_context": contract.required_context,
        }
        for role, contract in _CONTRACT_REGISTRY.items()
    ]
