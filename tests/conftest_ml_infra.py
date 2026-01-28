"""pytest fixtures for ML Infra unit testing.

This module provides reusable pytest fixtures for ML Infra teams to use
when writing unit-level evaluation tests with ai-evolution.
"""

import os
import pytest
from pathlib import Path
from typing import Generator

from ai_evolution import (
    Experiment,
    DeepDiffScorer,
    HTTPAdapter,
    load_index_csv_dataset,
)
from ai_evolution.core.types import DatasetItem


@pytest.fixture
def ml_infra_adapter() -> HTTPAdapter:
    """Fixture for ML Infra HTTP adapter.
    
    Uses environment variables for configuration:
    - CHAT_BASE_URL: Base URL for ML Infra server (default: http://localhost:8000)
    - CHAT_PLATFORM_AUTH_TOKEN: Authentication token (default: empty)
    - ACCOUNT_ID: Account ID (default: default)
    - ORG_ID: Organization ID (default: default)
    - PROJECT_ID: Project ID (default: default)
    
    Example:
        @pytest.mark.asyncio
        async def test_pipeline_create(ml_infra_adapter):
            # Use adapter in test
            pass
    """
    return HTTPAdapter(
        base_url=os.getenv("CHAT_BASE_URL", "http://localhost:8000"),
        auth_token=os.getenv("CHAT_PLATFORM_AUTH_TOKEN", ""),
        account_id=os.getenv("ACCOUNT_ID", "default"),
        org_id=os.getenv("ORG_ID", "default"),
        project_id=os.getenv("PROJECT_ID", "default"),
    )


@pytest.fixture
def deep_diff_scorer_v3() -> DeepDiffScorer:
    """Fixture for DeepDiff v3 scorer.
    
    Example:
        @pytest.mark.asyncio
        async def test_pipeline_create(deep_diff_scorer_v3):
            # Use scorer in test
            pass
    """
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
    """Fixture for index.csv file path.
    
    Uses INDEX_FILE environment variable or defaults to benchmarks/datasets/index.csv.
    
    Example:
        @pytest.mark.asyncio
        async def test_pipeline_create(index_file_path):
            dataset = load_index_csv_dataset(index_file=index_file_path, ...)
    """
    return os.getenv("INDEX_FILE", "benchmarks/datasets/index.csv")


@pytest.fixture
def base_dir_path() -> str:
    """Fixture for base directory path.
    
    Uses BASE_DIR environment variable or defaults to benchmarks/datasets.
    """
    return os.getenv("BASE_DIR", "benchmarks/datasets")


@pytest.fixture
def test_dataset(request: pytest.FixtureRequest) -> list[DatasetItem]:
    """Fixture to load test dataset by test_id.
    
    Requires test_id to be provided via pytest.mark.parametrize or request.param.
    
    Example:
        @pytest.mark.parametrize("test_id", ["pipeline_create_001"])
        @pytest.mark.asyncio
        async def test_pipeline_create(test_id, test_dataset):
            # test_dataset will contain the loaded test case
            assert len(test_dataset) == 1
    """
    # Get test_id from parametrize or request.param
    test_id = None
    if hasattr(request, "param"):
        test_id = request.param
    elif hasattr(request, "node"):
        # Try to get from parametrize markers
        for marker in request.node.iter_markers("parametrize"):
            if marker.args and len(marker.args) > 0:
                # This is a simplified approach - in practice, test_id should be passed explicitly
                pass
    
    # If test_id not found, try to get from function name or skip
    if test_id is None:
        # Try to extract from test function name
        if hasattr(request, "function"):
            func_name = request.function.__name__
            # Look for test_id in function name or use a default
            # For now, skip if not provided
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
    """Fixture factory for loading test cases by ID.
    
    Returns a function that can be called with a test_id to load a specific test case.
    
    Example:
        @pytest.mark.asyncio
        async def test_pipeline_create(load_test_case_by_id):
            test_case = load_test_case_by_id("pipeline_create_001")
            assert test_case.id == "pipeline_create_001"
    """
    def _load_test_case(test_id: str, index_file: str | None = None, base_dir: str | None = None) -> DatasetItem:
        """Load a single test case by test_id."""
        from ai_evolution.sdk.ml_infra import load_single_test_case
        
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
    """Fixture factory for creating experiments.
    
    Returns a function that creates an Experiment with provided dataset and scorers.
    
    Example:
        @pytest.mark.asyncio
        async def test_pipeline_create(experiment_factory, test_dataset, deep_diff_scorer_v3):
            experiment = experiment_factory(
                name="test_pipeline_create",
                dataset=test_dataset,
                scorers=[deep_diff_scorer_v3],
            )
            result = await experiment.run(...)
    """
    def _create_experiment(
        name: str,
        dataset: list[DatasetItem],
        scorers: list[DeepDiffScorer],
    ) -> Experiment:
        """Create an Experiment instance."""
        return Experiment(
            name=name,
            dataset=dataset,
            scorers=scorers,
        )
    
    return _create_experiment


@pytest.fixture
def default_model() -> str:
    """Fixture for default model name.
    
    Uses MODEL environment variable or defaults to claude-3-7-sonnet.
    """
    return os.getenv("MODEL", "claude-3-7-sonnet")


@pytest.fixture(scope="session")
def test_results_dir() -> str:
    """Fixture for test results directory.
    
    Creates a temporary directory for test results if it doesn't exist.
    """
    import tempfile
    import shutil
    
    results_dir = os.getenv("TEST_RESULTS_DIR", "test_results")
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    
    yield results_dir
    
    # Cleanup (optional - comment out if you want to keep results)
    # if os.path.exists(results_dir) and results_dir.startswith(tempfile.gettempdir()):
    #     shutil.rmtree(results_dir)
