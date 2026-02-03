"""DeepDiff-based scorers for YAML comparison."""

import warnings
from typing import Any, Callable

import numpy as np
import yaml
from deepdiff import DeepDiff

from aieval.scorers.base import Scorer
from aieval.core.types import Score


def _detect_entity_type(data_dict: dict[str, Any]) -> tuple[str | None, str | None]:
    """Detect entity type from dictionary."""
    entity_keys = {
        "pipeline": "pipeline",
        "stage": "stage",
        "service": "service",
        "environment": "environment",
        "connector": "connector",
        "secret": "secret",
    }
    
    for entity_type, entity_key in entity_keys.items():
        if entity_key in data_dict:
            return entity_type, entity_key
    
    return None, None


def _remove_optional_keys(obj: Any, keys_to_remove: set[str]) -> Any:
    """Recursively remove specified keys from nested dict/list."""
    if isinstance(obj, dict):
        return {
            k: _remove_optional_keys(v, keys_to_remove)
            for k, v in obj.items()
            if k not in keys_to_remove
        }
    elif isinstance(obj, list):
        return [_remove_optional_keys(item, keys_to_remove) for item in obj]
    return obj


class DeepDiffScorer(Scorer):
    """Base DeepDiff scorer."""
    
    def __init__(
        self,
        name: str = "deep_diff",
        eval_id: str = "deep_diff.v1",
        version: str = "v1",
        entity_type: str | None = None,
        validation_func: Callable[[str], dict[str, Any]] | None = None,
    ):
        """
        Initialize DeepDiff scorer.
        
        Args:
            name: Score name
            eval_id: Evaluation ID
            version: Version (v1, v2, v3)
            entity_type: Entity type hint (optional)
            validation_func: Validation function for schema validation (optional)
        """
        super().__init__(name, eval_id)
        self.version = version
        self.entity_type = entity_type
        self.validation_func = validation_func
    
    def _parse_yaml(self, yaml_str: str) -> tuple[dict[str, Any] | None, str | None]:
        """Parse YAML string to dict."""
        try:
            return yaml.safe_load(yaml_str), None
        except Exception as e:
            return None, str(e)
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """Score generated output against expected."""
        # Parse YAML strings to dicts if needed
        if isinstance(generated, str):
            gen_dict, err = self._parse_yaml(generated)
            if err:
                return Score(
                    name=self.name,
                    value=0.0,
                    eval_id=self.eval_id,
                    comment=f"Failed to parse generated YAML: {err}",
                    metadata=metadata,
                )
            generated = gen_dict
        
        if isinstance(expected, str):
            exp_dict, err = self._parse_yaml(expected)
            if err:
                return Score(
                    name=self.name,
                    value=0.0,
                    eval_id=self.eval_id,
                    comment=f"Failed to parse expected YAML: {err}",
                    metadata=metadata,
                )
            expected = exp_dict
        
        # Handle dict with yaml key (from index_csv format)
        if isinstance(expected, dict) and "yaml" in expected:
            exp_dict, err = self._parse_yaml(expected["yaml"])
            if err:
                return Score(
                    name=self.name,
                    value=0.0,
                    eval_id=self.eval_id,
                    comment=f"Failed to parse expected YAML: {err}",
                    metadata=metadata,
                )
            expected = exp_dict
            # Get entity type from expected dict if available
            if not self.entity_type and "entity_type" in expected:
                self.entity_type = expected["entity_type"]
        
        # Handle expected as string (direct YAML string)
        elif isinstance(expected, str):
            exp_dict, err = self._parse_yaml(expected)
            if err:
                return Score(
                    name=self.name,
                    value=0.0,
                    eval_id=self.eval_id,
                    comment=f"Failed to parse expected YAML: {err}",
                    metadata=metadata,
                )
            expected = exp_dict
        
        # Get entity type from metadata
        if not self.entity_type:
            self.entity_type = metadata.get("entity_type")
        
        # Call version-specific scoring
        if self.version == "v1":
            score_value, diff, comment = self._score_v1(generated, expected)
        elif self.version == "v2":
            score_value, diff, comment = self._score_v2(generated, expected)
        elif self.version == "v3":
            score_value, diff, comment = self._score_v3(generated, expected)
        else:
            raise ValueError(f"Unknown version: {self.version}")
        
        return Score(
            name=self.name,
            value=score_value,
            eval_id=self.eval_id,
            comment=comment,
            metadata={**metadata, "diff": str(diff) if diff else None},
        )
    
    def _score_v1(
        self, dict1: dict[str, Any] | None, dict2: dict[str, Any] | None
    ) -> tuple[float, Any, str]:
        """
        Score using DeepDiff v1 (basic).
        
        Matches ml-infra/evals deep_diff_v1 implementation:
        - Basic DeepDiff without entity awareness
        - No optional key removal
        - No top-level exclusion
        """
        if dict1 is None:
            return float("nan"), None, "Reference dictionary is None."
        if dict2 is None:
            return float("nan"), None, "Generated dictionary is None."
        
        try:
            # Use same DeepDiff parameters as ml-infra/evals
            diff = DeepDiff(dict1, dict2, get_deep_distance=True, ignore_order=True)
        except Exception as e:
            warnings.warn(f"DeepDiff could not calculate distance: {e}")
            return float("nan"), None, str(e)
        
        if diff:
            try:
                distance = diff.get("deep_distance", 0.0)
                if distance is None:
                    distance = 0.0
            except Exception as e:
                warnings.warn(f"DeepDiff did not return deep distance: {e}")
                return float("nan"), diff, str(e)
        else:
            distance = 0.0
        
        # Round to 2 decimal places (matching ml-infra/evals behavior)
        score = round(1.0 - distance, 2)
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
        return score, diff, ""
    
    def _score_v2(
        self, dict1: dict[str, Any] | None, dict2: dict[str, Any] | None
    ) -> tuple[float, Any, str]:
        """Score using DeepDiff v2 (with required field validation)."""
        if dict1 is None:
            return float("nan"), None, "Reference dictionary is None."
        if dict2 is None:
            return float("nan"), None, "Generated dictionary is None."
        
        # Detect entity type
        entity_type = self.entity_type
        if entity_type is None:
            entity_type, entity_key = _detect_entity_type(dict2)
            if entity_type is None:
                return (
                    0.0,
                    None,
                    "Unable to detect entity type. Expected one of: pipeline, service, environment, connector, secret.",
                )
        else:
            entity_key = entity_type
            if entity_key not in dict2:
                return 0.0, None, f"The input is not a {entity_type}."
        
        # Validate required fields
        required_fields_map = {
            "pipeline": ["name", "identifier", "stages"],
            "stage": ["name", "identifier", "type", "spec"],
            "service": ["name", "identifier"],
            "environment": ["name", "identifier", "type"],
            "connector": ["name", "identifier", "type", "spec"],
            "secret": ["name", "identifier", "type", "spec"],
        }
        
        required_fields = required_fields_map.get(entity_type, ["name", "identifier"])
        
        try:
            entity_data = dict2[entity_key]
            missing_fields = [
                field for field in required_fields if field not in entity_data
            ]
            
            if missing_fields:
                return (
                    0.0,
                    None,
                    f"Missing required {entity_type} fields: {missing_fields}",
                )
        except Exception as e:
            warnings.warn(f"{entity_type.capitalize()} Structure Validation Failed: {e}")
            return float("nan"), None, str(e)
        
        # Remove optional keys
        optional_keys = {"name", "identifier", "description"}
        dict1_cleaned = _remove_optional_keys(dict1, optional_keys)
        dict2_cleaned = _remove_optional_keys(dict2, optional_keys)
        
        # Exclude top-level keys (matching ml-infra/evals behavior)
        top_level_keys = ["projectIdentifier", "orgIdentifier", "accountIdentifier"]
        # Build exclude paths - handle both root level and nested entity level
        exclude_paths = []
        for key in top_level_keys:
            # Try both patterns: root level and entity level
            exclude_paths.append(f"root['{key}']")
            exclude_paths.append(f"root['{entity_key}']['{key}']")
        
        try:
            diff = DeepDiff(
                dict1_cleaned,
                dict2_cleaned,
                get_deep_distance=True,
                ignore_order=True,
                exclude_paths=exclude_paths,
            )
        except Exception as e:
            warnings.warn(f"DeepDiff could not calculate distance: {e}")
            return float("nan"), None, str(e)
        
        # Handle added items (matching ml-infra/evals retry logic)
        # Note: ml-infra/evals may retry with added items excluded, but we'll keep it simple
        # If needed, we can add retry logic here
        
        if diff:
            try:
                distance = diff.get("deep_distance", 0.0)
            except Exception as e:
                warnings.warn(f"DeepDiff did not return deep distance: {e}")
                return float("nan"), diff, str(e)
        else:
            distance = 0.0
        
        # Round to 2 decimal places (matching ml-infra/evals behavior)
        score = round(1.0 - distance, 2)
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
        return score, diff, ""
    
    def _score_v3(
        self, dict1: dict[str, Any] | None, dict2: dict[str, Any] | None
    ) -> tuple[float, Any, str]:
        """Score using DeepDiff v3 (with schema validation)."""
        if dict1 is None:
            return float("nan"), None, "Reference dictionary is None."
        if dict2 is None:
            return float("nan"), None, "Generated dictionary is None."
        
        # Detect entity type
        entity_type = self.entity_type
        if entity_type is None:
            entity_type, entity_key = _detect_entity_type(dict2)
            if entity_type is None:
                return (
                    0.0,
                    None,
                    "Unable to detect entity type. Expected one of: pipeline, service, environment, connector, secret.",
                )
        else:
            entity_key = entity_type
            if entity_key not in dict2:
                return 0.0, None, f"The input is not a {entity_type}."
        
        # Perform schema validation if validation function provided
        if self.validation_func:
            try:
                validation_results = self.validation_func(yaml.dump(dict2))
                is_valid = validation_results.get("valid", False)
                errors = validation_results.get("errors", [])
                
                if not is_valid:
                    return (
                        0.0,
                        None,
                        f"{entity_type.capitalize()} schema validation failed: {errors}",
                    )
            except Exception as e:
                warnings.warn(f"{entity_type.capitalize()} Schema Validation Failed: {e}")
                return float("nan"), None, str(e)
        
        # Remove optional keys
        optional_keys = {"name", "identifier", "description"}
        dict1_cleaned = _remove_optional_keys(dict1, optional_keys)
        dict2_cleaned = _remove_optional_keys(dict2, optional_keys)
        
        # Exclude top-level keys (matching ml-infra/evals behavior)
        top_level_keys = ["projectIdentifier", "orgIdentifier", "accountIdentifier"]
        # Build exclude paths - handle both root level and nested entity level
        exclude_paths = []
        for key in top_level_keys:
            # Try both patterns: root level and entity level
            exclude_paths.append(f"root['{key}']")
            exclude_paths.append(f"root['{entity_key}']['{key}']")
        
        # Calculate deep diff
        try:
            diff = DeepDiff(
                dict1_cleaned,
                dict2_cleaned,
                get_deep_distance=True,
                ignore_order=True,
                exclude_paths=exclude_paths,
            )
        except Exception as e:
            warnings.warn(f"DeepDiff could not calculate distance: {e}")
            return float("nan"), None, str(e)
        
        if diff:
            try:
                distance = diff.get("deep_distance", 0.0)
            except Exception as e:
                warnings.warn(f"DeepDiff did not return deep distance: {e}")
                return float("nan"), diff, str(e)
        else:
            distance = 0.0
        
        # Round to 2 decimal places (matching ml-infra/evals behavior)
        score = round(1.0 - distance, 2)
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
        return score, diff, ""
