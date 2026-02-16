"""Hallucination detection scorer.

Detects hallucinations by checking if claims in the generated text
are supported by the provided context (RAG context, source documents, etc.).
"""

import logging
from typing import Any

from aieval.scorers.guardrails.base import GuardrailScorer
from aieval.scorers.llm_judge import LLMJudgeScorer
from aieval.core.types import Score

logger = logging.getLogger(__name__)


class HallucinationScorer(GuardrailScorer):
    """Detects hallucinations by checking claims against context.

    Requires context (RAG context, source documents) to evaluate.
    Uses LLM-as-judge to determine if claims are supported.
    """

    def __init__(
        self,
        name: str = "hallucination",
        eval_id: str = "hallucination.v1",
        threshold: float = 0.5,
        action: str = "warn",
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
    ):
        """
        Initialize hallucination scorer.

        Args:
            name: Score name
            eval_id: Evaluation ID
            threshold: Threshold for pass/fail (0.0-1.0, higher = more strict)
            action: Action to take if threshold exceeded
            model: LLM model for judging
            api_key: API key for LLM
        """
        super().__init__(name, eval_id, "hallucination", threshold, action)
        self.llm_judge = LLMJudgeScorer(
            name=f"{name}_judge",
            eval_id=f"{eval_id}_judge",
            model=model,
            rubric=(
                "Evaluate whether the generated output contains any claims or statements "
                "that are NOT supported by the provided context. A hallucination is a "
                "claim that contradicts the context or adds information not present in "
                "the context. Score 1.0 if there are clear hallucinations, 0.0 if all "
                "claims are well-supported by the context."
            ),
            api_key=api_key,
        )

    def score(
        self,
        generated: Any,
        expected: Any | None = None,
        metadata: dict[str, Any] = {},
    ) -> Score:
        """
        Score for hallucinations.

        Args:
            generated: Generated text to check
            expected: Not used (for compatibility)
            metadata: Should contain 'context' key with source documents/context

        Returns:
            Score with value 0.0 (no hallucinations) to 1.0 (hallucinations detected)
        """
        # Extract context from metadata
        context = metadata.get("context", "")
        if not context:
            logger.warning("No context provided for hallucination check. Cannot evaluate.")
            return Score(
                name=self.name,
                value=1.0,  # Fail-safe: assume hallucination if no context
                eval_id=self.eval_id,
                comment="No context provided for hallucination evaluation",
                metadata=metadata,
            )

        # Convert generated to string if needed
        generated_text = str(generated) if not isinstance(generated, str) else generated

        # Add context to metadata for LLM judge
        judge_metadata = {
            **metadata,
            "input": {
                "prompt": f"Context:\n{context}\n\nGenerated Output:\n{generated_text}",
            },
        }

        # Use LLM judge to evaluate
        judge_score = self.llm_judge.score(
            generated=generated_text,
            expected=None,
            metadata=judge_metadata,
        )

        # Return score with hallucination-specific metadata
        return Score(
            name=self.name,
            value=judge_score.value if isinstance(judge_score.value, (int, float)) else 0.0,
            eval_id=self.eval_id,
            comment=judge_score.comment,
            metadata={
                **judge_score.metadata,
                "has_context": bool(context),
                "context_length": len(context),
            },
        )
