"""Step selection scorer for agent evaluation."""

from typing import Any

from aieval.scorers.base import Scorer
from aieval.core.types import Score


class StepSelectionScorer(Scorer):
    """Scorer for evaluating if agent selected the correct next step."""

    def __init__(self, name: str = "step_selection", eval_id: str = "step_selection.v1"):
        """
        Initialize step selection scorer.

        Args:
            name: Scorer name
            eval_id: Evaluation ID
        """
        super().__init__(name=name, eval_id=eval_id)

    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score step selection correctness.

        Args:
            generated: Generated next step (string or dict)
            expected: Expected next step (string or dict)
            metadata: Additional metadata

        Returns:
            Score object (True if correct step, False otherwise)
        """
        # Extract step identifiers
        generated_step = None
        expected_step = None

        if isinstance(generated, dict):
            generated_step = (
                generated.get("step") or generated.get("action") or generated.get("name")
            )
        elif isinstance(generated, str):
            generated_step = generated

        if isinstance(expected, dict):
            expected_step = expected.get("step") or expected.get("action") or expected.get("name")
        elif isinstance(expected, str):
            expected_step = expected

        # Compare
        is_correct = generated_step == expected_step

        return Score(
            name=self.name,
            value=is_correct,
            eval_id=self.eval_id,
            comment=f"Expected: {expected_step}, Got: {generated_step}",
            metadata=metadata,
        )
