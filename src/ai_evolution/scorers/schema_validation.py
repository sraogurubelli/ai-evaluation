"""Schema validation scorer."""

import yaml
from typing import Any, Callable

from ai_evolution.scorers.base import Scorer
from ai_evolution.core.types import Score


class SchemaValidationScorer(Scorer):
    """Scorer that validates YAML against entity schemas."""
    
    def __init__(
        self,
        name: str = "schema_validation",
        eval_id: str = "schema_validation.v1",
        validation_func: Callable[[str], dict[str, Any]] | None = None,
    ):
        """
        Initialize schema validation scorer.
        
        Args:
            name: Score name
            eval_id: Evaluation ID
            validation_func: Validation function that takes YAML string and returns
                           {"valid": bool, "errors": list[str]}
        """
        super().__init__(name, eval_id)
        self.validation_func = validation_func
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Validate generated YAML against schema.
        
        Args:
            generated: Generated YAML (string or dict)
            expected: Expected output (not used for schema validation)
            metadata: Metadata with entity_type
            
        Returns:
            Score with validation result
        """
        if self.validation_func is None:
            return Score(
                name=self.name,
                value=True,  # Pass if no validation function provided
                eval_id=self.eval_id,
                comment="No validation function provided",
                metadata=metadata,
            )
        
        # Convert to YAML string if needed
        if isinstance(generated, dict):
            yaml_str = yaml.dump(generated)
        elif isinstance(generated, str):
            yaml_str = generated
        else:
            return Score(
                name=self.name,
                value=False,
                eval_id=self.eval_id,
                comment="Generated output is not YAML string or dict",
                metadata=metadata,
            )
        
        # Run validation
        try:
            validation_results = self.validation_func(yaml_str)
            is_valid = validation_results.get("valid", False)
            errors = validation_results.get("errors", [])
            
            return Score(
                name=self.name,
                value=is_valid,
                eval_id=self.eval_id,
                comment="Schema validation passed" if is_valid else f"Schema validation failed: {errors}",
                metadata={**metadata, "errors": errors if not is_valid else []},
            )
        except Exception as e:
            return Score(
                name=self.name,
                value=False,
                eval_id=self.eval_id,
                comment=f"Schema validation error: {str(e)}",
                metadata=metadata,
            )
