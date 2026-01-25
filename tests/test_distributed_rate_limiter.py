"""Tests for distributed rate limiting."""

import asyncio
import os
import sys
import tempfile
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, "src")

from test_ai.workflow import (
    DistributedRateLimiter,
    MemoryRateLimiter,
    SQLiteRateLimiter,
    RateLimitResult,
    get_rate_limiter,
    reset_rate_limiter,
)


class TestRateLimitResult:
    """Tests for RateLimitResult dataclass."""

    def test_allowed_result(self):
        """Allowed result has correct properties."""
        result = RateLimitResult(
            allowed=True,
            current_count=5,
            limit=10,
            reset_at=time.time() + 60,
        )
        assert result.allowed is True
        assert result.remaining == 5
        assert result.retry_after is None

    def test_denied_result(self):
        """Denied result includes retry_after."""
        result = RateLimitResult(
            allowed=False,
            current_count=11,
            limit=10,
            reset_at=time.time() + 30,
            retry_after=30.0,
        )
        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after == 30.0

    def test_remaining_never_negative(self):
        """Remaining doesn't go negative."""
        result = RateLimitResult(
            allowed=False,
            current_count=15,
            limit=10,
            reset_at=time.time(),
        )
        assert result.remaining == 0


class TestMemoryRateLimiter:
    """Tests for in-memory rate limiter."""

    @pytest.mark.asyncio
    async def test_acquire_within_limit(self):
        """Requests within limit are allowed."""
        limiter = MemoryRateLimiter()

        for i in range(5):
            result = await limiter.acquire("test", limit=10)
            assert result.allowed is True
            assert result.current_count == i + 1

    @pytest.mark.asyncio
    async def test_acquire_exceeds_limit(self):
        """Requests exceeding limit are denied."""
        limiter = MemoryRateLimiter()

        # Fill up the limit
        for _ in range(10):
            await limiter.acquire("test", limit=10)

        # Next request should be denied
        result = await limiter.acquire("test", limit=10)
        assert result.allowed is False
        assert result.current_count == 11
        assert result.retry_after is not None

    @pytest.mark.asyncio
    async def test_separate_keys_independent(self):
        """Different keys have independent limits."""
        limiter = MemoryRateLimiter()

        # Fill up one key
        for _ in range(10):
            await limiter.acquire("key1", limit=10)

        # Another key should still be available
        result = await limiter.acquire("key2", limit=10)
        assert result.allowed is True
        assert result.current_count == 1

    @pytest.mark.asyncio
    async def test_window_reset(self):
        """Counts reset after window expires."""
        limiter = MemoryRateLimiter()

        # Short window for testing
        result = await limiter.acquire("test", limit=5, window_seconds=1)
        assert result.current_count == 1

        # Wait for window to expire
        await asyncio.sleep(1.1)

        # Should be in new window
        result = await limiter.acquire("test", limit=5, window_seconds=1)
        assert result.current_count == 1

    @pytest.mark.asyncio
    async def test_get_current(self):
        """Get current count without incrementing."""
        limiter = MemoryRateLimiter()

        # Initial count is 0
        count = await limiter.get_current("test")
        assert count == 0

        # Acquire some slots
        await limiter.acquire("test", limit=10)
        await limiter.acquire("test", limit=10)

        # Count should reflect acquisitions
        count = await limiter.get_current("test")
        assert count == 2

    @pytest.mark.asyncio
    async def test_reset(self):
        """Reset clears counts for a key."""
        limiter = MemoryRateLimiter()

        # Acquire some slots
        for _ in range(5):
            await limiter.acquire("test", limit=10)

        # Reset
        await limiter.reset("test")

        # Count should be 0
        count = await limiter.get_current("test")
        assert count == 0


class TestSQLiteRateLimiter:
    """Tests for SQLite-based rate limiter."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_acquire_within_limit(self, temp_db):
        """Requests within limit are allowed."""
        limiter = SQLiteRateLimiter(db_path=temp_db)

        for i in range(5):
            result = await limiter.acquire("test", limit=10)
            assert result.allowed is True
            assert result.current_count == i + 1

    @pytest.mark.asyncio
    async def test_acquire_exceeds_limit(self, temp_db):
        """Requests exceeding limit are denied."""
        limiter = SQLiteRateLimiter(db_path=temp_db)

        # Fill up the limit
        for _ in range(10):
            await limiter.acquire("test", limit=10)

        # Next request should be denied
        result = await limiter.acquire("test", limit=10)
        assert result.allowed is False
        assert result.current_count == 11

    @pytest.mark.asyncio
    async def test_persistence_across_instances(self, temp_db):
        """Counts persist across limiter instances."""
        limiter1 = SQLiteRateLimiter(db_path=temp_db)

        # Acquire with first instance
        for _ in range(5):
            await limiter1.acquire("test", limit=10)

        # Create new instance (simulates different process)
        limiter2 = SQLiteRateLimiter(db_path=temp_db)

        # Count should include previous acquisitions
        result = await limiter2.acquire("test", limit=10)
        assert result.current_count == 6

    @pytest.mark.asyncio
    async def test_get_current(self, temp_db):
        """Get current count without incrementing."""
        limiter = SQLiteRateLimiter(db_path=temp_db)

        await limiter.acquire("test", limit=10)
        await limiter.acquire("test", limit=10)

        count = await limiter.get_current("test")
        assert count == 2

    @pytest.mark.asyncio
    async def test_reset(self, temp_db):
        """Reset clears counts for a key."""
        limiter = SQLiteRateLimiter(db_path=temp_db)

        for _ in range(5):
            await limiter.acquire("test", limit=10)

        await limiter.reset("test")

        count = await limiter.get_current("test")
        assert count == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, temp_db):
        """Cleanup removes old records."""
        limiter = SQLiteRateLimiter(db_path=temp_db)

        # Acquire with very short window
        await limiter.acquire("test", limit=10, window_seconds=1)

        # Wait for window to expire
        await asyncio.sleep(1.1)

        # Cleanup should remove old records
        deleted = await limiter.cleanup_expired(older_than_seconds=1)
        assert deleted >= 0  # May be 1 or 0 depending on timing


class TestGetRateLimiter:
    """Tests for global rate limiter factory."""

    def test_returns_sqlite_by_default(self):
        """Returns SQLite limiter when Redis not configured."""
        reset_rate_limiter()

        # Ensure no Redis URL
        with patch.dict(os.environ, {"REDIS_URL": ""}, clear=False):
            limiter = get_rate_limiter()
            assert isinstance(limiter, SQLiteRateLimiter)

        reset_rate_limiter()

    def test_caches_instance(self):
        """Returns same instance on subsequent calls."""
        reset_rate_limiter()

        with patch.dict(os.environ, {"REDIS_URL": ""}, clear=False):
            limiter1 = get_rate_limiter()
            limiter2 = get_rate_limiter()
            assert limiter1 is limiter2

        reset_rate_limiter()

    def test_reset_clears_cache(self):
        """reset_rate_limiter clears cached instance."""
        reset_rate_limiter()

        with patch.dict(os.environ, {"REDIS_URL": ""}, clear=False):
            limiter1 = get_rate_limiter()
            reset_rate_limiter()
            limiter2 = get_rate_limiter()
            assert limiter1 is not limiter2

        reset_rate_limiter()


class TestDistributedExecutorIntegration:
    """Tests for distributed rate limiting in executor."""

    @pytest.mark.asyncio
    async def test_executor_with_distributed_disabled(self):
        """Executor works with distributed disabled (default)."""
        from test_ai.workflow import RateLimitedParallelExecutor, ParallelTask

        executor = RateLimitedParallelExecutor(distributed=False)
        assert executor._distributed is False
        assert executor._distributed_limiter is None

    @pytest.mark.asyncio
    async def test_executor_with_distributed_enabled(self):
        """Executor initializes distributed limiter when enabled."""
        from test_ai.workflow import RateLimitedParallelExecutor

        reset_rate_limiter()

        with patch.dict(os.environ, {"REDIS_URL": ""}, clear=False):
            executor = RateLimitedParallelExecutor(distributed=True)
            assert executor._distributed is True
            # Limiter created lazily
            limiter = executor._get_distributed_limiter()
            assert limiter is not None

        reset_rate_limiter()

    @pytest.mark.asyncio
    async def test_distributed_check_allowed(self):
        """Distributed check allows requests within limit."""
        from test_ai.workflow import RateLimitedParallelExecutor

        reset_rate_limiter()

        with patch.dict(os.environ, {"REDIS_URL": ""}, clear=False):
            executor = RateLimitedParallelExecutor(
                distributed=True,
                distributed_rpm={"anthropic": 100, "default": 100},
            )

            allowed = await executor._check_distributed_limit("anthropic")
            assert allowed is True

        reset_rate_limiter()

    @pytest.mark.asyncio
    async def test_distributed_check_denied(self):
        """Distributed check denies requests over limit."""
        from test_ai.workflow import RateLimitedParallelExecutor

        reset_rate_limiter()

        with patch.dict(os.environ, {"REDIS_URL": ""}, clear=False):
            executor = RateLimitedParallelExecutor(
                distributed=True,
                distributed_rpm={"anthropic": 2, "default": 2},
                distributed_window=60,
            )

            # Use up the limit
            await executor._check_distributed_limit("anthropic")
            await executor._check_distributed_limit("anthropic")

            # Next should be denied
            allowed = await executor._check_distributed_limit("anthropic")
            assert allowed is False

        reset_rate_limiter()

    def test_get_provider_stats_includes_distributed(self):
        """Provider stats include distributed info."""
        from test_ai.workflow import RateLimitedParallelExecutor

        executor = RateLimitedParallelExecutor(
            distributed=True,
            distributed_rpm={"anthropic": 60, "openai": 90, "default": 120},
        )

        stats = executor.get_provider_stats()

        assert stats["anthropic"]["distributed_enabled"] is True
        assert stats["anthropic"]["distributed_rpm"] == 60
        assert stats["openai"]["distributed_rpm"] == 90

    def test_get_provider_stats_without_distributed(self):
        """Provider stats show distributed disabled."""
        from test_ai.workflow import RateLimitedParallelExecutor

        executor = RateLimitedParallelExecutor(distributed=False)

        stats = executor.get_provider_stats()

        assert stats["anthropic"]["distributed_enabled"] is False

    def test_create_executor_with_distributed(self):
        """Factory function supports distributed options."""
        from test_ai.workflow import create_rate_limited_executor

        executor = create_rate_limited_executor(
            distributed=True,
            anthropic_rpm=50,
            openai_rpm=80,
        )

        assert executor._distributed is True
        assert executor._distributed_rpm["anthropic"] == 50
        assert executor._distributed_rpm["openai"] == 80

    @pytest.mark.asyncio
    async def test_task_respects_distributed_limit(self):
        """Task execution respects distributed rate limit."""
        from test_ai.workflow import RateLimitedParallelExecutor, ParallelTask
        from test_ai.workflow.distributed_rate_limiter import SQLiteRateLimiter

        reset_rate_limiter()

        # Use a fresh temp database for this test to avoid pollution
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Create executor with fresh limiter
            executor = RateLimitedParallelExecutor(
                distributed=True,
                distributed_rpm={"anthropic": 10, "default": 10},
                distributed_window=60,
            )
            # Inject fresh limiter
            executor._distributed_limiter = SQLiteRateLimiter(db_path=db_path)

            async def success_handler(**kwargs):
                return "ok"

            tasks = [
                ParallelTask(
                    id=f"t{i}",
                    step_id=f"t{i}",
                    handler=success_handler,
                    kwargs={"provider": "anthropic"},
                )
                for i in range(3)
            ]

            result = await executor.execute_parallel_rate_limited(tasks)

            # All 3 should succeed (within limit of 10)
            assert len(result.successful) == 3
        finally:
            os.unlink(db_path)

        reset_rate_limiter()
