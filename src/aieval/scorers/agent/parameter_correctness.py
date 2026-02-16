"""Parameter correctness scorer for agent evaluation."""

from typing import Any

from aieval.scorers.base import Scorer
from aieval.core.types import Score


class ParameterCorrectnessScorer(Scorer):
    """Scorer for evaluating if tool parameters are correct."""

    def __init__(
        self, name: str = "parameter_correctness", eval_id: str = "parameter_correctness.v1"
    ):
        """
        Initialize parameter correctness scorer.

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
        Score parameter correctness.

        Args:
            generated: Generated tool call parameters (dict)
            expected: Expected tool call parameters (dict)
            metadata: Additional metadata

        Returns:
            Score object (float 0.0-1.0 for correctness)
        """
        if not isinstance(generated, dict) or not isinstance(expected, dict):
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment="Generated or expected is not a dictionary",
                metadata=metadata,
            )

        # Compare parameters
        correct_params = 0
        total_params = len(expected)

        for key, expected_value in expected.items():
            generated_value = generated.get(key)
            if generated_value == expected_value:
                correct_params += 1

        correctness = correct_params / total_params if total_params > 0 else 0.0

        return Score(
            name=self.name,
            value=correctness,
            eval_id=self.eval_id,
            comment=f"{correct_params}/{total_params} parameters correct",
            metadata=metadata,
        )
