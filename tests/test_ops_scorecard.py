"""Tests for AI Ops Scorecard module."""

import os
import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

# Add src to path with priority over existing imports
src_path = os.path.join(os.path.dirname(__file__), "..", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import directly from ops submodules to avoid triggering test_ai.__init__
# which has transitive dependencies on openai, etc.
import importlib.util


def _load_module_direct(name, path):
    """Load a module directly from path without triggering parent __init__."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Load ops modules directly
_ops_models = _load_module_direct(
    "test_ai.ops.models",
    os.path.join(src_path, "test_ai", "ops", "models.py")
)
_ops_scoring = _load_module_direct(
    "test_ai.ops.scoring",
    os.path.join(src_path, "test_ai", "ops", "scoring.py")
)
_ops_aggregate = _load_module_direct(
    "test_ai.ops.aggregate",
    os.path.join(src_path, "test_ai", "ops", "aggregate.py")
)

OpsEvent = _ops_models.OpsEvent
WeeklyAgg = _ops_models.WeeklyAgg
ProjectType = _ops_models.ProjectType
ArtifactType = _ops_models.ArtifactType

WeeklyInputs = _ops_scoring.WeeklyInputs
WeeklyScores = _ops_scoring.WeeklyScores
compute_weekly_scores = _ops_scoring.compute_weekly_scores
clamp01 = _ops_scoring.clamp01
TARGETS_DEFAULT = _ops_scoring.TARGETS_DEFAULT

aggregate_week = _ops_aggregate.aggregate_week
week_window = _ops_aggregate.week_window


class TestScoring:
    """Tests for scoring.py"""

    def test_clamp01_lower_bound(self):
        """clamp01 returns 0 for negative values."""
        assert clamp01(-0.5) == 0.0
        assert clamp01(-100) == 0.0

    def test_clamp01_upper_bound(self):
        """clamp01 returns 1 for values > 1."""
        assert clamp01(1.5) == 1.0
        assert clamp01(100) == 1.0

    def test_clamp01_pass_through(self):
        """clamp01 returns value as-is for 0-1 range."""
        assert clamp01(0.0) == 0.0
        assert clamp01(0.5) == 0.5
        assert clamp01(1.0) == 1.0

    def test_compute_weekly_scores_basic(self):
        """compute_weekly_scores returns correct structure."""
        inp = WeeklyInputs(
            sessions=10,
            artifacts=3,
            decisions=2,
            executions=1,
            hours_saved=3.0,
            loops=1,
            impact_points=5,
        )
        scores = compute_weekly_scores(inp)

        assert isinstance(scores, WeeklyScores)
        assert 0 <= scores.output_score <= 100
        assert 0 <= scores.efficiency_score <= 100
        assert 0 <= scores.impact_score <= 100
        assert 0 <= scores.quality_score <= 100
        assert 0 <= scores.weekly_score <= 100

    def test_compute_weekly_scores_zero_sessions(self):
        """Handles zero sessions without division error."""
        inp = WeeklyInputs(
            sessions=0,
            artifacts=0,
            decisions=0,
            executions=0,
            hours_saved=0.0,
            loops=0,
            impact_points=0,
        )
        scores = compute_weekly_scores(inp)

        # Should not crash and produce deterministic result
        assert scores.loop_rate == 0.0
        assert scores.snr == 0.0
        assert scores.weekly_score >= 0

    def test_compute_weekly_scores_spec_example(self):
        """Test with exact values from spec acceptance criteria."""
        inp = WeeklyInputs(
            sessions=50,
            artifacts=6,
            decisions=5,
            executions=4,
            hours_saved=6.0,
            loops=5,
            impact_points=10,
        )
        scores = compute_weekly_scores(inp)

        # Verify derived metrics
        assert scores.loop_rate == pytest.approx(5 / 50)  # 0.1
        assert scores.snr == pytest.approx((6 + 5 + 4) / 50)  # 0.3

        # Output: (6+5+4)/18 = 15/18 = 0.833... * 100 = 83.33
        assert scores.output_score == pytest.approx(83.33, rel=0.01)

        # Efficiency: (6/6 + (1 - 0.1/0.2))/2 * 100 = (1 + 0.5)/2 * 100 = 75
        assert scores.efficiency_score == pytest.approx(75.0, rel=0.01)

        # Impact: 10/10 * 100 = 100
        assert scores.impact_score == pytest.approx(100.0)

        # Quality: 0.3/0.6 * 100 = 50
        assert scores.quality_score == pytest.approx(50.0)

        # Final: 0.35*83.33 + 0.20*75 + 0.35*100 + 0.10*50
        # = 29.17 + 15 + 35 + 5 = 84.17 -> 84
        expected_final = round(
            0.35 * scores.output_score
            + 0.20 * scores.efficiency_score
            + 0.35 * scores.impact_score
            + 0.10 * scores.quality_score
        )
        assert scores.weekly_score == expected_final

    def test_compute_weekly_scores_max_values(self):
        """Scores cap at 100."""
        inp = WeeklyInputs(
            sessions=10,
            artifacts=100,  # Way over target
            decisions=100,
            executions=100,
            hours_saved=100.0,
            loops=0,
            impact_points=100,
        )
        scores = compute_weekly_scores(inp)

        assert scores.output_score == 100.0
        assert scores.efficiency_score == 100.0
        assert scores.impact_score == 100.0
        assert scores.weekly_score == 100

    def test_compute_weekly_scores_custom_targets(self):
        """Custom targets are applied correctly."""
        custom_targets = {
            "output": 10,  # Lower target
            "hours_saved": 3,
            "impact": 5,
            "loop_rate": 0.1,
            "snr": 0.3,
        }

        inp = WeeklyInputs(
            sessions=10,
            artifacts=5,
            decisions=3,
            executions=2,
            hours_saved=3.0,
            loops=0,
            impact_points=5,
        )

        scores = compute_weekly_scores(inp, targets=custom_targets)

        # With lower targets, scores should be higher/capped
        assert scores.output_score == 100.0  # 10/10 = 1.0
        assert scores.impact_score == 100.0  # 5/5 = 1.0

    def test_compute_weekly_scores_deterministic(self):
        """Same inputs produce same outputs across multiple calls."""
        inp = WeeklyInputs(
            sessions=25,
            artifacts=4,
            decisions=3,
            executions=2,
            hours_saved=4.5,
            loops=2,
            impact_points=7,
        )

        scores1 = compute_weekly_scores(inp)
        scores2 = compute_weekly_scores(inp)
        scores3 = compute_weekly_scores(inp)

        assert scores1.weekly_score == scores2.weekly_score == scores3.weekly_score


class TestWeekWindow:
    """Tests for week_window function."""

    def test_week_window_monday(self):
        """week_window for a Monday returns same day as start."""
        monday = date(2025, 1, 20)  # A Monday
        start, end = week_window(monday)
        assert start == monday
        assert end == date(2025, 1, 27)  # Following Monday

    def test_week_window_wednesday(self):
        """week_window for a Wednesday returns previous Monday."""
        wednesday = date(2025, 1, 22)  # A Wednesday
        start, end = week_window(wednesday)
        assert start == date(2025, 1, 20)
        assert end == date(2025, 1, 27)

    def test_week_window_sunday(self):
        """week_window for a Sunday returns previous Monday."""
        sunday = date(2025, 1, 26)  # A Sunday
        start, end = week_window(sunday)
        assert start == date(2025, 1, 20)
        assert end == date(2025, 1, 27)


class TestAggregateWeek:
    """Tests for aggregate_week function."""

    def test_aggregate_week_empty_events(self):
        """Aggregates correctly with no events."""
        result = aggregate_week(sessions_count=10, ops_events=[])

        assert result["sessions"] == 10
        assert result["artifacts"] == 0
        assert result["decisions"] == 0
        assert result["executions"] == 0
        assert result["loops"] == 0
        assert result["hours_saved"] == 0.0
        assert result["impact_points"] == 0
        assert result["weekly_score"] >= 0

    def test_aggregate_week_with_events(self):
        """Aggregates events correctly."""
        events = [
            {
                "artifact": True,
                "decision_closed": True,
                "execution_done": False,
                "minutes_saved": 30,
                "loop": False,
                "impact_career": 3,
                "impact_legal": 0,
                "impact_revenue": 2,
            },
            {
                "artifact": True,
                "decision_closed": False,
                "execution_done": True,
                "minutes_saved": 60,
                "loop": False,
                "impact_career": 0,
                "impact_legal": 5,
                "impact_revenue": 0,
            },
            {
                "artifact": False,
                "decision_closed": False,
                "execution_done": False,
                "minutes_saved": 0,
                "loop": True,
                "impact_career": 0,
                "impact_legal": 0,
                "impact_revenue": 0,
            },
        ]

        result = aggregate_week(sessions_count=5, ops_events=events)

        assert result["sessions"] == 5
        assert result["artifacts"] == 2
        assert result["decisions"] == 1
        assert result["executions"] == 1
        assert result["loops"] == 1
        assert result["hours_saved"] == 1.5  # 90 minutes
        assert result["career_points"] == 3
        assert result["legal_points"] == 5
        assert result["revenue_points"] == 2
        assert result["impact_points"] == 10

    def test_aggregate_week_impact_dict_format(self):
        """Handles impact as nested dict."""
        events = [
            {
                "artifact": True,
                "decision_closed": False,
                "execution_done": False,
                "minutes_saved": 15,
                "loop": False,
                "impact": {"career": 2, "legal": 1, "revenue": 3},
            },
        ]

        result = aggregate_week(sessions_count=1, ops_events=events)

        assert result["career_points"] == 2
        assert result["legal_points"] == 1
        assert result["revenue_points"] == 3
        assert result["impact_points"] == 6


class TestOpsEventModel:
    """Tests for OpsEvent Pydantic model."""

    def test_ops_event_creation(self):
        """OpsEvent creates with required fields."""
        event = OpsEvent(session_id="test-session")

        assert event.id is not None
        assert event.session_id == "test-session"
        assert event.artifact is False
        assert event.decision_closed is False
        assert event.execution_done is False
        assert event.minutes_saved == 0
        assert event.loop is False

    def test_ops_event_negative_minutes_rejected(self):
        """OpsEvent rejects negative minutes_saved."""
        with pytest.raises(ValueError):
            OpsEvent(session_id="test", minutes_saved=-5)

    def test_ops_event_negative_impact_rejected(self):
        """OpsEvent rejects negative impact values."""
        with pytest.raises(ValueError):
            OpsEvent(session_id="test", impact_career=-1)

    def test_ops_event_impact_total(self):
        """impact_total property sums all impact areas."""
        event = OpsEvent(
            session_id="test",
            impact_career=3,
            impact_legal=2,
            impact_revenue=5,
        )
        assert event.impact_total == 10


@pytest.mark.skipif(
    "openai" not in sys.modules and importlib.util.find_spec("openai") is None,
    reason="Skipping OpsEventManager tests - openai/full dependencies not installed"
)
class TestOpsEventManager:
    """Tests for OpsEventManager database operations."""

    @pytest.fixture
    def backend(self):
        """Create a temporary SQLite backend."""
        # Import here to avoid module-level dependency issues
        from test_ai.state.backends import SQLiteBackend

        tmpdir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(tmpdir, "test.db")
            backend = SQLiteBackend(db_path=db_path)
            yield backend
            backend.close()
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.fixture
    def manager(self, backend):
        """Create an OpsEventManager."""
        from test_ai.ops.ops_manager import OpsEventManager

        with patch("test_ai.ops.ops_manager.get_database", return_value=backend):
            manager = OpsEventManager(backend=backend)
            yield manager

    def test_init_creates_schema(self, backend):
        """OpsEventManager creates tables on init."""
        from test_ai.ops.ops_manager import OpsEventManager

        with patch("test_ai.ops.ops_manager.get_database", return_value=backend):
            OpsEventManager(backend=backend)

        # Verify tables exist
        ops_table = backend.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ops_events'"
        )
        assert ops_table is not None

        weekly_table = backend.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='weekly_aggs'"
        )
        assert weekly_table is not None

    def test_create_ops_event(self, manager, backend):
        """create_ops_event persists to database."""
        event = OpsEvent(
            session_id="session-123",
            artifact=True,
            artifact_type=ArtifactType.CODE,
            minutes_saved=30,
            impact_career=5,
        )

        created = manager.create_ops_event(event)

        assert created.id == event.id
        assert created.session_id == "session-123"

        # Verify in database
        row = backend.fetchone(
            "SELECT * FROM ops_events WHERE id = ?", (event.id,)
        )
        assert row is not None
        assert row["session_id"] == "session-123"
        assert row["artifact"] == 1
        assert row["minutes_saved"] == 30

    def test_create_ops_event_requires_artifact_type(self, manager):
        """create_ops_event requires artifact_type when artifact=True."""
        event = OpsEvent(
            session_id="session-123",
            artifact=True,
            artifact_type=None,  # Missing
        )

        with pytest.raises(ValueError) as exc:
            manager.create_ops_event(event)

        assert "artifact_type is required" in str(exc.value)

    def test_get_ops_event(self, manager):
        """get_ops_event returns event by ID."""
        event = OpsEvent(session_id="session-123")
        manager.create_ops_event(event)

        retrieved = manager.get_ops_event(event.id)

        assert retrieved is not None
        assert retrieved.id == event.id
        assert retrieved.session_id == "session-123"

    def test_get_ops_event_not_found(self, manager):
        """get_ops_event returns None for missing ID."""
        result = manager.get_ops_event("nonexistent-id")
        assert result is None

    def test_update_ops_event(self, manager):
        """update_ops_event modifies fields."""
        event = OpsEvent(session_id="session-123", minutes_saved=10)
        manager.create_ops_event(event)

        updated = manager.update_ops_event(
            event.id,
            {"minutes_saved": 30, "decision_closed": True},
        )

        assert updated is not None
        assert updated.minutes_saved == 30
        assert updated.decision_closed is True

    def test_delete_ops_event(self, manager, backend):
        """delete_ops_event removes from database."""
        event = OpsEvent(session_id="session-123")
        manager.create_ops_event(event)

        result = manager.delete_ops_event(event.id)

        assert result is True

        row = backend.fetchone(
            "SELECT * FROM ops_events WHERE id = ?", (event.id,)
        )
        assert row is None

    def test_list_ops_events(self, manager):
        """list_ops_events returns all events."""
        for i in range(5):
            manager.create_ops_event(OpsEvent(session_id=f"session-{i}"))

        events = manager.list_ops_events()

        assert len(events) == 5

    def test_list_ops_events_by_project(self, manager):
        """list_ops_events filters by project."""
        manager.create_ops_event(
            OpsEvent(session_id="s1", project=ProjectType.CAREER)
        )
        manager.create_ops_event(
            OpsEvent(session_id="s2", project=ProjectType.LEGAL)
        )
        manager.create_ops_event(
            OpsEvent(session_id="s3", project=ProjectType.CAREER)
        )

        career_events = manager.list_ops_events(project=ProjectType.CAREER)

        assert len(career_events) == 2

    def test_compute_weekly_aggregate(self, manager):
        """compute_weekly_aggregate creates WeeklyAgg."""
        # Create some events
        for i in range(3):
            manager.create_ops_event(
                OpsEvent(
                    session_id=f"session-{i}",
                    artifact=True,
                    artifact_type=ArtifactType.CODE,
                    minutes_saved=30,
                    impact_career=2,
                )
            )

        today = date.today()
        agg = manager.compute_weekly_aggregate(today, sessions_count=10)

        assert agg is not None
        assert agg.sessions == 10
        assert agg.artifacts == 3
        assert agg.hours_saved == 1.5  # 90 minutes
        assert agg.career_points == 6
        assert agg.weekly_score >= 0

    def test_compute_weekly_aggregate_upserts(self, manager):
        """compute_weekly_aggregate updates existing record."""
        today = date.today()

        # First computation
        agg1 = manager.compute_weekly_aggregate(today, sessions_count=5)

        # Add more events
        manager.create_ops_event(
            OpsEvent(
                session_id="new-session",
                artifact=True,
                artifact_type=ArtifactType.DOC,
                minutes_saved=60,
            )
        )

        # Second computation
        agg2 = manager.compute_weekly_aggregate(today, sessions_count=10)

        assert agg2.sessions == 10
        assert agg2.artifacts >= agg1.artifacts

    def test_list_weekly_aggregates(self, manager):
        """list_weekly_aggregates returns recent weeks."""
        today = date.today()

        # Create aggregates for multiple weeks
        for i in range(3):
            week_date = today - timedelta(weeks=i)
            manager.compute_weekly_aggregate(week_date, sessions_count=10 + i)

        aggregates = manager.list_weekly_aggregates(limit=10)

        assert len(aggregates) == 3

    def test_get_ops_stats(self, manager):
        """get_ops_stats returns summary statistics."""
        # Create some events
        manager.create_ops_event(
            OpsEvent(session_id="s1", project=ProjectType.CAREER)
        )
        manager.create_ops_event(
            OpsEvent(session_id="s2", project=ProjectType.LEGAL)
        )

        stats = manager.get_ops_stats()

        assert stats["total_events"] == 2
        assert "events_by_project" in stats
        assert stats["events_by_project"].get("career", 0) == 1
        assert stats["events_by_project"].get("legal", 0) == 1
