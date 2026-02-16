"""Base template for LLM-as-judge scorers."""

from typing import Any
import os

from aieval.scorers.base import Scorer
from aieval.core.types import Score


class LLMJudgeTemplateScorer(Scorer):
    """Base class for LLM-as-judge template scorers."""
    
    def __init__(
        self,
        name: str,
        eval_id: str,
        rubric: str,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
    ):
        """
        Initialize LLM judge template scorer.
        
        Args:
            name: Scorer name
            eval_id: Evaluation ID
            rubric: Scoring rubric
            model: Model name for LLM judge
            api_key: API key (uses OPENAI_API_KEY env var if None)
        """
        super().__init__(name=name, eval_id=eval_id)
        self.rubric = rubric
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("API key required (provide api_key or set OPENAI_API_KEY)")
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score using LLM-as-judge.
        
        Args:
            generated: Generated output
            expected: Expected output (may be None)
            metadata: Additional metadata
            
        Returns:
            Score object
        """
        from aieval.scorers.llm_judge import LLMJudgeScorer
        
        # Create LLM judge scorer with rubric
        judge = LLMJudgeScorer(
            name=self.name,
            eval_id=self.eval_id,
            model=self.model,
            rubric=self.rubric,
            api_key=self.api_key,
        )
        
        return judge.score(generated=generated, expected=expected, metadata=metadata)
