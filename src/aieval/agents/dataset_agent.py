"""Dataset agent for loading and managing datasets."""

import os
from typing import Any

from aieval.agents.base import BaseEvaluationAgent
from aieval.core.types import DatasetItem
from aieval.datasets import (
    load_jsonl_dataset,
    load_index_csv_dataset,
    FunctionDataset,
)


class DatasetAgent(BaseEvaluationAgent):
    """Agent for dataset loading and management."""
    
    async def run(self, query: str, **kwargs: Any) -> Any:
        """
        Run dataset operation based on query.
        
        Supported queries:
        - "load": Load a dataset
        - "validate": Validate dataset format
        - "list": List available datasets
        
        Args:
            query: Operation to perform
            **kwargs: Operation-specific parameters
            
        Returns:
            Operation result
        """
        if query == "load":
            return await self.load_dataset(**kwargs)
        elif query == "validate":
            return await self.validate_dataset(**kwargs)
        elif query == "list":
            return await self.list_datasets(**kwargs)
        else:
            raise ValueError(f"Unknown query: {query}")
    
    async def load_dataset(
        self,
        dataset_type: str,
        path: str | None = None,
        index_file: str | None = None,
        base_dir: str | None = None,
        filters: dict[str, Any] | None = None,
        offline: bool = False,
        actual_suffix: str = "actual",
        function: Any | None = None,
        **kwargs: Any,
    ) -> list[DatasetItem]:
        """
        Load a dataset.
        
        Args:
            dataset_type: Type of dataset ("jsonl", "index_csv", "function")
            path: Path to dataset file (for jsonl or index_csv)
            index_file: Path to index CSV file (for index_csv)
            base_dir: Base directory for index_csv datasets
            filters: Filters for index_csv datasets
            offline: Whether to use offline mode for index_csv
            actual_suffix: Suffix for actual files in index_csv
            function: Function for function-based datasets
            **kwargs: Additional parameters
            
        Returns:
            List of dataset items
        """
        self.logger.info(f"Loading dataset of type: {dataset_type}")
        
        if dataset_type == "jsonl":
            if not path:
                raise ValueError("path is required for jsonl datasets")
            dataset = load_jsonl_dataset(path)
            self.logger.info(f"Loaded {len(dataset)} items from {path}")
            return dataset
        
        elif dataset_type == "index_csv":
            if not index_file and not path:
                raise ValueError("index_file or path is required for index_csv datasets")
            index_file = index_file or path
            base_dir = base_dir or "benchmarks/datasets"
            filters = filters or {}
            
            dataset = load_index_csv_dataset(
                index_file=index_file,
                base_dir=base_dir,
                entity_type=filters.get("entity_type"),
                operation_type=filters.get("operation_type"),
                test_id=filters.get("test_id"),
                offline=offline,
                actual_suffix=actual_suffix,
            )
            self.logger.info(f"Loaded {len(dataset)} items from {index_file}")
            return dataset
        
        elif dataset_type == "function":
            if not function:
                raise ValueError("function is required for function-based datasets")
            func_dataset = FunctionDataset(function)
            dataset = func_dataset.load()
            self.logger.info(f"Loaded {len(dataset)} items from function")
            return dataset
        
        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")
    
    async def validate_dataset(
        self,
        dataset: list[DatasetItem] | None = None,
        dataset_type: str | None = None,
        path: str | None = None,
        schema: dict[str, Any] | None = None,
        schema_file: str | Path | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Validate dataset format.
        
        Args:
            dataset: Dataset items to validate (if already loaded)
            dataset_type: Type of dataset (if loading from file)
            path: Path to dataset file (if loading from file)
            schema: Optional JSON schema dict for schema validation
            schema_file: Optional path to JSON schema file
            **kwargs: Additional parameters
            
        Returns:
            Validation result with status and issues
        """
        if dataset is None:
            if not dataset_type or not path:
                raise ValueError("Either dataset or (dataset_type and path) must be provided")
            dataset = await self.load_dataset(dataset_type=dataset_type, path=path, **kwargs)
        
        issues = []
        
        # Check dataset is not empty
        if not dataset:
            issues.append("Dataset is empty")
            return {
                "valid": False,
                "item_count": 0,
                "issues": issues,
            }
        
        # Check each item has required fields
        for i, item in enumerate(dataset):
            if not hasattr(item, "id") or not item.id:
                issues.append(f"Item {i} missing id")
            if not hasattr(item, "input") or item.input is None:
                issues.append(f"Item {i} missing input")
            # Note: expected is optional (for production evals)
        
        # Schema validation if provided
        schema_validation = None
        if schema or schema_file:
            from aieval.datasets.validation import validate_dataset_schema
            try:
                schema_validation = validate_dataset_schema(dataset, schema=schema, schema_file=schema_file)
                if not schema_validation["valid"]:
                    issues.append(f"Schema validation failed: {schema_validation['invalid_count']} items invalid")
            except Exception as e:
                issues.append(f"Schema validation error: {str(e)}")
        
        is_valid = len(issues) == 0
        
        self.logger.info(f"Dataset validation: {'valid' if is_valid else 'invalid'} ({len(issues)} issues)")
        
        result = {
            "valid": is_valid,
            "item_count": len(dataset),
            "issues": issues,
        }
        
        if schema_validation:
            result["schema_validation"] = schema_validation
        
        return result
    
    async def list_datasets(self, base_dir: str | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        """
        List available datasets.
        
        Args:
            base_dir: Base directory to search (for index_csv)
            **kwargs: Additional parameters
            
        Returns:
            List of dataset metadata
        """
        datasets = []
        
        # List JSONL datasets (if base_dir provided)
        if base_dir:
            if os.path.exists(base_dir):
                for root, dirs, files in os.walk(base_dir):
                    for file in files:
                        if file.endswith(".jsonl"):
                            full_path = os.path.join(root, file)
                            datasets.append({
                                "type": "jsonl",
                                "path": full_path,
                                "name": file,
                            })
        
        # List index CSV datasets
        if base_dir:
            index_csv_path = os.path.join(base_dir, "index.csv")
            if os.path.exists(index_csv_path):
                datasets.append({
                    "type": "index_csv",
                    "path": index_csv_path,
                    "name": "index.csv",
                })
        
        self.logger.info(f"Found {len(datasets)} datasets")
        return datasets
