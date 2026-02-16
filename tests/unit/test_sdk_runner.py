"""Tests for EvaluationRunner."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aieval.sdk.runner import EvaluationRunner
from aieval.core.types import DatasetItem, Score
from aieval.sinks.stdout import StdoutSink
from tests.fixtures.mock_adapter import MockAdapter


class TestEvaluationRunner:
    """Tests for EvaluationRunner."""

    @pytest.mark.asyncio
    async def test_run_basic(self):
        """Test basic evaluation run."""
        runner = EvaluationRunner()

        dataset = [
            DatasetItem(
                id="test-001",
                input={"prompt": "test"},
                expected={"yaml": "key: value"},
            ),
        ]

        adapter = MockAdapter()

        from aieval.scorers.deep_diff import DeepDiffScorer

        scorers = [DeepDiffScorer(version="v1")]

        result = await runner.run(
            dataset=dataset,
            adapter=adapter,
            scorers=scorers,
            model="gpt-4o",
            eval_name="test_eval",
        )

        assert result is not None
        assert len(result.scores) > 0

    @pytest.mark.asyncio
    async def test_run_with_sinks(self):
        """Test run with custom sinks."""
        runner = EvaluationRunner()

        dataset = [
            DatasetItem(
                id="test-001",
                input={"prompt": "test"},
                expected={"yaml": "key: value"},
            ),
        ]

        adapter = MockAdapter()

        from aieval.scorers.deep_diff import DeepDiffScorer

        scorers = [DeepDiffScorer(version="v1")]

        sinks = [StdoutSink()]

        result = await runner.run(
            dataset=dataset,
            adapter=adapter,
            scorers=scorers,
            sinks=sinks,
        )

        assert result is not None

    def test_run_requires_scorers(self):
        """Test that run requires scorers."""
        runner = EvaluationRunner()

        dataset = [DatasetItem(id="test-001", input={}, expected={})]
        adapter = MockAdapter()

        with pytest.raises(ValueError, match="scorers must be provided"):
            # This will fail at runtime, but we test the validation
            import asyncio

            asyncio.run(runner.run(dataset=dataset, adapter=adapter, scorers=None))
