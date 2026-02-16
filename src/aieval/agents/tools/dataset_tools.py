"""Dataset-related tools."""

from typing import Any
from pathlib import Path

from aieval.agents.tools.base import Tool, ToolResult
from aieval.core.types import DatasetItem
from aieval.datasets import load_jsonl_dataset, load_index_csv_dataset


class LoadDatasetTool(Tool):
    """Tool for loading datasets from various formats."""
    
    def __init__(self):
        super().__init__(
            name="load_dataset",
            description="Load a dataset from JSONL or index CSV format",
            parameters_schema={
                "type": "object",
                "properties": {
                    "dataset_type": {
                        "type": "string",
                        "enum": ["jsonl", "index_csv"],
                        "description": "Dataset format type",
                    },
                    "path": {
                        "type": "string",
                        "description": "Path to dataset file (for jsonl) or index CSV file (for index_csv)",
                    },
                    "base_dir": {
                        "type": "string",
                        "description": "Base directory for index_csv datasets (default: benchmarks/datasets)",
                        "default": "benchmarks/datasets",
                    },
                    "entity_type": {
                        "type": "string",
                        "description": "Filter by entity type (for index_csv)",
                    },
                    "operation_type": {
                        "type": "string",
                        "description": "Filter by operation type (for index_csv)",
                    },
                    "test_id": {
                        "type": "string",
                        "description": "Filter by specific test_id (for index_csv)",
                    },
                    "offline": {
                        "type": "boolean",
                        "description": "Load pre-generated outputs (for index_csv)",
                        "default": False,
                    },
                    "actual_suffix": {
                        "type": "string",
                        "description": "Suffix for actual files (for index_csv offline mode)",
                        "default": "actual",
                    },
                },
                "required": ["dataset_type", "path"],
            },
        )
    
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute dataset loading."""
        try:
            self.validate_parameters(**kwargs)
            
            dataset_type = kwargs["dataset_type"]
            path = kwargs["path"]
            
            if dataset_type == "jsonl":
                dataset = load_jsonl_dataset(path)
            elif dataset_type == "index_csv":
                dataset = load_index_csv_dataset(
                    index_file=path,
                    base_dir=kwargs.get("base_dir", "benchmarks/datasets"),
                    entity_type=kwargs.get("entity_type"),
                    operation_type=kwargs.get("operation_type"),
                    test_id=kwargs.get("test_id"),
                    offline=kwargs.get("offline", False),
                    actual_suffix=kwargs.get("actual_suffix", "actual"),
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown dataset type: {dataset_type}",
                )
            
            return ToolResult(
                success=True,
                data={
                    "dataset": [item.to_dict() for item in dataset],
                    "count": len(dataset),
                },
                metadata={"dataset_type": dataset_type, "path": str(path)},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )
