"""Sample dataset fixtures for testing."""

from aieval.core.types import DatasetItem


def sample_dataset_items():
    """Return sample dataset items for testing."""
    return [
        DatasetItem(
            id="test-001",
            input={"prompt": "Create a pipeline"},
            expected={"yaml": "pipeline:\n  name: Test"},
            metadata={"entity_type": "pipeline"},
        ),
        DatasetItem(
            id="test-002",
            input={"prompt": "Create a stage"},
            expected={"yaml": "stage:\n  name: Test Stage"},
            metadata={"entity_type": "stage"},
        ),
    ]
