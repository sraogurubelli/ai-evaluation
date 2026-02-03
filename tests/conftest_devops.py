"""pytest fixtures for DevOps consumer unit testing.

This module provides reusable pytest fixtures for DevOps/Harness teams to use
when writing unit-level evaluation tests with ai-evolution.
"""

import os
import pytest
from pathlib import Path

from aieval import (
    Experiment,
    DeepDiffScorer,
    HTTPAdapter,
    load_index_csv_dataset,
)
from aieval.core.types import DatasetItem


@pytest.fixture
def devops_adapter() -> HTTPAdapter:
    """Fixture for DevOps HTTP adapter.

    Uses environment variables for configuration:
    - CHAT_BASE_URL: Base URL for server (default: http://localhost:8000)
    - CHAT_PLATFORM_AUTH_TOKEN: Authentication token (default: empty)
    - ACCOUNT_ID, ORG_ID, PROJECT_ID: Context (default: default)

    Example:
        @pytest.mark.asyncio
        async def test_pipeline_create(devops_adapter):
            ...
    """
    return HTTPAdapter(
        base_url=os.getenv("CHAT_BASE_URL", "http://localhost:8000"),
        auth_token=os.getenv("CHAT_PLATFORM_AUTH_TOKEN", ""),
        context_field_name="harness_context",
        context_data={
            "account_id": os.getenv("ACCOUNT_ID", "default"),
            "org_id": os.getenv("ORG_ID", "default"),
            "project_id": os.getenv("PROJECT_ID", "default"),
        },
    )


# Backward-compat alias for tests/examples that still reference ml_infra_adapter
@pytest.fixture
def ml_infra_adapter(devops_adapter) -> HTTPAdapter:
    """Alias for devops_adapter (backward compatibility)."""
    return devops_adapter


@pytest.fixture
def deep_diff_scorer_v3() -> DeepDiffScorer:
    """Fixture for DeepDiff v3 scorer."""
    return DeepDiffScorer(
        name="deep_diff_v3",
        eval_id="deep_diff_v3.v1",
        version="v3",
    )


@pytest.fixture
def deep_diff_scorer_v2() -> DeepDiffScorer:
    """Fixture for DeepDiff v2 scorer."""
    return DeepDiffScorer(
        name="deep_diff_v2",
        eval_id="deep_diff_v2.v1",
        version="v2",
    )


@pytest.fixture
def deep_diff_scorer_v1() -> DeepDiffScorer:
    """Fixture for DeepDiff v1 scorer."""
    return DeepDiffScorer(
        name="deep_diff_v1",
        eval_id="deep_diff_v1.v1",
        version="v1",
    )


@pytest.fixture
def index_file_path() -> str:
    """Fixture for index.csv file path."""
    return os.getenv("INDEX_FILE", "benchmarks/datasets/index.csv")


@pytest.fixture
def base_dir_path() -> str:
    """Fixture for base directory path."""
    return os.getenv("BASE_DIR", "benchmarks/datasets")


@pytest.fixture
def test_dataset(request: pytest.FixtureRequest) -> list[DatasetItem]:
    """Fixture to load test dataset by test_id."""
    test_id = None
    if hasattr(request, "param"):
        test_id = request.param
    if test_id is None and hasattr(request, "function"):
        pytest.skip("test_id not provided - use pytest.mark.parametrize or pass test_id")
    index_file = request.getfixturevalue("index_file_path")
    base_dir = request.getfixturevalue("base_dir_path")
    return load_index_csv_dataset(
        index_file=index_file,
        base_dir=base_dir,
        test_id=test_id,
    )


@pytest.fixture
def load_test_case_by_id():
    """Fixture factory for loading test cases by ID (uses DevOps consumer)."""
    def _load_test_case(test_id: str, index_file: str | None = None, base_dir: str | None = None) -> DatasetItem:
        from samples_sdk.consumers.devops import load_single_test_case
        if index_file is None:
            index_file = os.getenv("INDEX_FILE", "benchmarks/datasets/index.csv")
        if base_dir is None:
            base_dir = os.getenv("BASE_DIR", "benchmarks/datasets")
        return load_single_test_case(
            index_file=index_file,
            test_id=test_id,
            base_dir=base_dir,
        )
    return _load_test_case


@pytest.fixture
def experiment_factory():
    """Fixture factory for creating experiments."""
    def _create_experiment(
        name: str,
        dataset: list[DatasetItem],
        scorers: list[DeepDiffScorer],
    ) -> Experiment:
        return Experiment(name=name, dataset=dataset, scorers=scorers)
    return _create_experiment


@pytest.fixture
def default_model() -> str:
    """Fixture for default model name."""
    return os.getenv("MODEL", "claude-3-7-sonnet")


@pytest.fixture(scope="session")
def test_results_dir() -> str:
    """Fixture for test results directory."""
    results_dir = os.getenv("TEST_RESULTS_DIR", "test_results")
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    return results_dir
