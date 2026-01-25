"""Tests for workflow models and adapter."""

import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from test_ai.orchestrator.workflow_engine import (
    StepType,
    WorkflowStep,
    Workflow,
    WorkflowResult,
)
from test_ai.orchestrator import WorkflowEngineAdapter


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for workflows and logs."""
    workflows_dir = tmp_path / "workflows"
    logs_dir = tmp_path / "logs"
    workflows_dir.mkdir()
    logs_dir.mkdir()
    return {"workflows_dir": workflows_dir, "logs_dir": logs_dir}


@pytest.fixture
def mock_settings(temp_dirs):
    """Create mock settings."""
    settings = MagicMock()
    settings.workflows_dir = temp_dirs["workflows_dir"]
    settings.logs_dir = temp_dirs["logs_dir"]
    return settings


@pytest.fixture
def workflow_adapter(mock_settings):
    """Create workflow adapter with mocked settings."""
    with patch(
        "test_ai.orchestrator.workflow_engine_adapter.get_settings"
    ) as mock_get_settings:
        mock_get_settings.return_value = mock_settings
        with patch("test_ai.workflow.executor.WorkflowExecutor"):
            adapter = WorkflowEngineAdapter(dry_run=True)
            # Manually set settings for testing
            adapter._test_settings = mock_settings
            yield adapter


@pytest.fixture
def simple_workflow():
    """Create a simple workflow."""
    return Workflow(
        id="test-workflow",
        name="Test Workflow",
        description="A test workflow",
        steps=[
            WorkflowStep(
                id="step1",
                type=StepType.TRANSFORM,
                action="format",
                params={"template": "Hello, {name}!"},
                next_step="step2",
            ),
            WorkflowStep(
                id="step2",
                type=StepType.TRANSFORM,
                action="extract",
                params={"source": "data", "key": "value"},
            ),
        ],
        variables={"name": "World", "data": {"value": 42}},
    )


# =============================================================================
# Test StepType Enum
# =============================================================================


class TestStepType:
    """Tests for StepType enum."""

    def test_openai_value(self):
        """Test OPENAI type value."""
        assert StepType.OPENAI.value == "openai"

    def test_github_value(self):
        """Test GITHUB type value."""
        assert StepType.GITHUB.value == "github"

    def test_notion_value(self):
        """Test NOTION type value."""
        assert StepType.NOTION.value == "notion"

    def test_gmail_value(self):
        """Test GMAIL type value."""
        assert StepType.GMAIL.value == "gmail"

    def test_transform_value(self):
        """Test TRANSFORM type value."""
        assert StepType.TRANSFORM.value == "transform"

    def test_claude_code_value(self):
        """Test CLAUDE_CODE type value."""
        assert StepType.CLAUDE_CODE.value == "claude_code"

    def test_from_string(self):
        """Test creating from string value."""
        assert StepType("openai") == StepType.OPENAI
        assert StepType("github") == StepType.GITHUB


# =============================================================================
# Test WorkflowStep Model
# =============================================================================


class TestWorkflowStep:
    """Tests for WorkflowStep model."""

    def test_create_step(self):
        """Test creating a workflow step."""
        step = WorkflowStep(
            id="test-step",
            type=StepType.OPENAI,
            action="generate_completion",
        )
        assert step.id == "test-step"
        assert step.type == StepType.OPENAI
        assert step.action == "generate_completion"

    def test_step_with_params(self):
        """Test step with parameters."""
        step = WorkflowStep(
            id="test",
            type=StepType.OPENAI,
            action="generate_completion",
            params={"prompt": "Hello", "max_tokens": 100},
        )
        assert step.params["prompt"] == "Hello"
        assert step.params["max_tokens"] == 100

    def test_step_with_next(self):
        """Test step with next_step."""
        step = WorkflowStep(
            id="step1",
            type=StepType.TRANSFORM,
            action="format",
            next_step="step2",
        )
        assert step.next_step == "step2"

    def test_default_params(self):
        """Test default params is empty dict."""
        step = WorkflowStep(
            id="test",
            type=StepType.TRANSFORM,
            action="extract",
        )
        assert step.params == {}

    def test_default_next_step(self):
        """Test default next_step is None."""
        step = WorkflowStep(
            id="test",
            type=StepType.TRANSFORM,
            action="extract",
        )
        assert step.next_step is None

    def test_step_serialization(self):
        """Test step can be serialized."""
        step = WorkflowStep(
            id="test",
            type=StepType.OPENAI,
            action="generate_completion",
            params={"prompt": "test"},
        )
        data = step.model_dump()
        assert data["id"] == "test"
        assert data["type"] == "openai"


# =============================================================================
# Test Workflow Model
# =============================================================================


class TestWorkflow:
    """Tests for Workflow model."""

    def test_create_workflow(self):
        """Test creating a workflow."""
        workflow = Workflow(
            id="test",
            name="Test Workflow",
            description="A test",
        )
        assert workflow.id == "test"
        assert workflow.name == "Test Workflow"
        assert workflow.steps == []
        assert workflow.variables == {}

    def test_workflow_with_steps(self, simple_workflow):
        """Test workflow with steps."""
        assert len(simple_workflow.steps) == 2
        assert simple_workflow.steps[0].id == "step1"
        assert simple_workflow.steps[1].id == "step2"

    def test_workflow_with_variables(self, simple_workflow):
        """Test workflow with variables."""
        assert simple_workflow.variables["name"] == "World"
        assert simple_workflow.variables["data"]["value"] == 42

    def test_workflow_serialization(self, simple_workflow):
        """Test workflow can be serialized."""
        data = simple_workflow.model_dump()
        assert data["id"] == "test-workflow"
        assert data["name"] == "Test Workflow"
        assert len(data["steps"]) == 2


# =============================================================================
# Test WorkflowResult Model
# =============================================================================


class TestWorkflowResult:
    """Tests for WorkflowResult model."""

    def test_create_result(self):
        """Test creating a workflow result."""
        result = WorkflowResult(
            workflow_id="test",
            status="running",
            started_at=datetime.now(),
        )
        assert result.workflow_id == "test"
        assert result.status == "running"
        assert result.completed_at is None

    def test_result_with_outputs(self):
        """Test result with outputs."""
        result = WorkflowResult(
            workflow_id="test",
            status="completed",
            started_at=datetime.now(),
            steps_executed=["step1", "step2"],
            outputs={"step1": "result1", "step2": "result2"},
        )
        assert len(result.steps_executed) == 2
        assert result.outputs["step1"] == "result1"

    def test_result_with_errors(self):
        """Test result with errors."""
        result = WorkflowResult(
            workflow_id="test",
            status="failed",
            started_at=datetime.now(),
            errors=["Error 1", "Error 2"],
        )
        assert result.status == "failed"
        assert len(result.errors) == 2

    def test_result_serialization(self):
        """Test result can be serialized."""
        result = WorkflowResult(
            workflow_id="test",
            status="completed",
            started_at=datetime.now(),
            completed_at=datetime.now(),
        )
        data = result.model_dump(mode="json")
        assert data["workflow_id"] == "test"
        assert "started_at" in data


# =============================================================================
# Test WorkflowEngineAdapter Initialization
# =============================================================================


class TestWorkflowEngineAdapterInit:
    """Tests for WorkflowEngineAdapter initialization."""

    def test_adapter_init(self):
        """Test adapter initializes correctly."""
        with patch("test_ai.orchestrator.workflow_engine_adapter.WorkflowExecutor"):
            adapter = WorkflowEngineAdapter(dry_run=True)
            assert adapter is not None

    def test_adapter_has_executor(self):
        """Test adapter has internal executor."""
        with patch("test_ai.orchestrator.workflow_engine_adapter.WorkflowExecutor"):
            adapter = WorkflowEngineAdapter()
            assert adapter._executor is not None


# =============================================================================
# Test Workflow Persistence
# =============================================================================


class TestWorkflowPersistence:
    """Tests for workflow save/load/list operations."""

    def test_save_workflow(self, mock_settings, simple_workflow):
        """Test saving a workflow."""
        with patch(
            "test_ai.orchestrator.workflow_engine_adapter.get_settings"
        ) as mock_get:
            mock_get.return_value = mock_settings
            with patch("test_ai.orchestrator.workflow_engine_adapter.WorkflowExecutor"):
                adapter = WorkflowEngineAdapter()
                result = adapter.save_workflow(simple_workflow)
                assert result is True
                file_path = mock_settings.workflows_dir / f"{simple_workflow.id}.json"
                assert file_path.exists()

    def test_save_workflow_creates_valid_json(self, mock_settings, simple_workflow):
        """Test saved workflow is valid JSON."""
        with patch(
            "test_ai.orchestrator.workflow_engine_adapter.get_settings"
        ) as mock_get:
            mock_get.return_value = mock_settings
            with patch("test_ai.orchestrator.workflow_engine_adapter.WorkflowExecutor"):
                adapter = WorkflowEngineAdapter()
                adapter.save_workflow(simple_workflow)
                file_path = mock_settings.workflows_dir / f"{simple_workflow.id}.json"
                with open(file_path) as f:
                    data = json.load(f)
                assert data["id"] == "test-workflow"
                assert len(data["steps"]) == 2

    def test_load_workflow(self, mock_settings, simple_workflow):
        """Test loading a workflow."""
        with patch(
            "test_ai.orchestrator.workflow_engine_adapter.get_settings"
        ) as mock_get:
            mock_get.return_value = mock_settings
            with patch("test_ai.orchestrator.workflow_engine_adapter.WorkflowExecutor"):
                adapter = WorkflowEngineAdapter()
                adapter.save_workflow(simple_workflow)
                loaded = adapter.load_workflow(simple_workflow.id)
                assert loaded is not None
                assert loaded.id == simple_workflow.id
                assert len(loaded.steps) == 2

    def test_load_nonexistent_workflow(self, mock_settings):
        """Test loading nonexistent workflow returns None."""
        with patch(
            "test_ai.orchestrator.workflow_engine_adapter.get_settings"
        ) as mock_get:
            mock_get.return_value = mock_settings
            with patch("test_ai.orchestrator.workflow_engine_adapter.WorkflowExecutor"):
                adapter = WorkflowEngineAdapter()
                result = adapter.load_workflow("nonexistent")
                assert result is None

    def test_list_workflows_empty(self, mock_settings):
        """Test listing workflows when none exist."""
        with patch(
            "test_ai.orchestrator.workflow_engine_adapter.get_settings"
        ) as mock_get:
            mock_get.return_value = mock_settings
            with patch("test_ai.orchestrator.workflow_engine_adapter.WorkflowExecutor"):
                adapter = WorkflowEngineAdapter()
                result = adapter.list_workflows()
                assert result == []

    def test_list_workflows(self, mock_settings):
        """Test listing workflows."""
        with patch(
            "test_ai.orchestrator.workflow_engine_adapter.get_settings"
        ) as mock_get:
            mock_get.return_value = mock_settings
            with patch("test_ai.orchestrator.workflow_engine_adapter.WorkflowExecutor"):
                adapter = WorkflowEngineAdapter()
                # Save some workflows
                for i in range(3):
                    workflow = Workflow(
                        id=f"workflow-{i}",
                        name=f"Workflow {i}",
                        description=f"Description {i}",
                    )
                    adapter.save_workflow(workflow)

                result = adapter.list_workflows()
                assert len(result) == 3
                ids = [w["id"] for w in result]
                assert "workflow-0" in ids
                assert "workflow-1" in ids
                assert "workflow-2" in ids

    def test_list_workflows_handles_invalid_files(self, mock_settings):
        """Test list_workflows handles invalid JSON files."""
        with patch(
            "test_ai.orchestrator.workflow_engine_adapter.get_settings"
        ) as mock_get:
            mock_get.return_value = mock_settings
            with patch("test_ai.orchestrator.workflow_engine_adapter.WorkflowExecutor"):
                adapter = WorkflowEngineAdapter()
                # Create valid workflow
                workflow = Workflow(
                    id="valid", name="Valid", description="Valid workflow"
                )
                adapter.save_workflow(workflow)

                # Create invalid JSON file
                invalid_path = mock_settings.workflows_dir / "invalid.json"
                with open(invalid_path, "w") as f:
                    f.write("not valid json")

                result = adapter.list_workflows()
                assert len(result) == 1
                assert result[0]["id"] == "valid"

    def test_settings_property(self, mock_settings):
        """Test settings property returns settings."""
        with patch(
            "test_ai.orchestrator.workflow_engine_adapter.get_settings"
        ) as mock_get:
            mock_get.return_value = mock_settings
            with patch("test_ai.orchestrator.workflow_engine_adapter.WorkflowExecutor"):
                adapter = WorkflowEngineAdapter()
                assert adapter.settings is not None


# =============================================================================
# Test Workflow Execution
# =============================================================================


class TestWorkflowExecution:
    """Tests for workflow execution through adapter."""

    def test_execute_workflow_calls_executor(self, mock_settings, simple_workflow):
        """Test execute_workflow uses internal executor."""
        with patch(
            "test_ai.orchestrator.workflow_engine_adapter.get_settings"
        ) as mock_get:
            mock_get.return_value = mock_settings
            with patch(
                "test_ai.orchestrator.workflow_engine_adapter.WorkflowExecutor"
            ) as mock_executor_class:
                mock_executor = MagicMock()
                mock_result = MagicMock()
                mock_result.status = "completed"
                mock_result.started_at = datetime.now()
                mock_result.completed_at = datetime.now()
                mock_result.steps = []
                mock_result.outputs = {}
                mock_result.error = None
                mock_executor.execute.return_value = mock_result
                mock_executor_class.return_value = mock_executor

                adapter = WorkflowEngineAdapter()
                result = adapter.execute_workflow(simple_workflow)

                assert result.status == "completed"
                mock_executor.execute.assert_called_once()

    def test_execute_workflow_returns_workflow_result(
        self, mock_settings, simple_workflow
    ):
        """Test execute_workflow returns WorkflowResult."""
        with patch(
            "test_ai.orchestrator.workflow_engine_adapter.get_settings"
        ) as mock_get:
            mock_get.return_value = mock_settings
            with patch(
                "test_ai.orchestrator.workflow_engine_adapter.WorkflowExecutor"
            ) as mock_executor_class:
                mock_executor = MagicMock()
                mock_result = MagicMock()
                mock_result.status = "completed"
                mock_result.started_at = datetime.now()
                mock_result.completed_at = datetime.now()
                mock_result.steps = []
                mock_result.outputs = {"key": "value"}
                mock_result.error = None
                mock_executor.execute.return_value = mock_result
                mock_executor_class.return_value = mock_executor

                adapter = WorkflowEngineAdapter()
                result = adapter.execute_workflow(simple_workflow)

                assert isinstance(result, WorkflowResult)
                assert result.workflow_id == simple_workflow.id
