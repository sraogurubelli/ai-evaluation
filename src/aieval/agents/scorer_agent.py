"""Scorer agent for managing scoring logic and scorer creation."""

from typing import Any

from aieval.agents.base import BaseEvaluationAgent
from aieval.core.types import DatasetItem, Score
from aieval.scorers.base import Scorer
from aieval.scorers import (
    DeepDiffScorer,
    SchemaValidationScorer,
    DashboardQualityScorer,
    KnowledgeGraphQualityScorer,
    LLMJudgeScorer,
)


class ScorerAgent(BaseEvaluationAgent):
    """Agent for scoring logic and scorer creation."""
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize scorer agent."""
        super().__init__(config)
        self._scorers: dict[str, Scorer] = {}
    
    async def run(self, query: str, **kwargs: Any) -> Any:
        """
        Run scorer operation based on query.
        
        Supported queries:
        - "create": Create a scorer
        - "score": Score a single item
        - "list": List available scorers
        
        Args:
            query: Operation to perform
            **kwargs: Operation-specific parameters
            
        Returns:
            Operation result
        """
        if query == "create":
            return await self.create_scorer(**kwargs)
        elif query == "score":
            return await self.score_item(**kwargs)
        elif query == "list":
            return await self.list_scorers(**kwargs)
        else:
            raise ValueError(f"Unknown query: {query}")
    
    async def create_scorer(
        self,
        scorer_type: str,
        name: str | None = None,
        **kwargs: Any,
    ) -> Scorer:
        """
        Create a scorer.
        
        Args:
            scorer_type: Type of scorer ("deep_diff", "schema_validation", "dashboard_quality", "kg_quality", "llm_judge")
            name: Optional name for the scorer (for caching)
            **kwargs: Scorer-specific configuration
            
        Returns:
            Created scorer instance
        """
        self.logger.info(f"Creating scorer of type: {scorer_type}")
        
        scorer_id = name or f"{scorer_type}_{id(kwargs)}"
        
        # Check cache
        if scorer_id in self._scorers:
            self.logger.info(f"Returning cached scorer: {scorer_id}")
            return self._scorers[scorer_id]
        
        scorer: Scorer
        
        if scorer_type == "deep_diff":
            version = kwargs.get("version", "v3")
            entity_type = kwargs.get("entity_type")
            validation_func = kwargs.get("validation_func")
            
            scorer = DeepDiffScorer(
                name=name or f"deep_diff_{version}",
                eval_id=f"deep_diff_{version}.v1",
                version=version,
                entity_type=entity_type,
                validation_func=validation_func,
            )
        
        elif scorer_type == "schema_validation":
            validation_func = kwargs.get("validation_func")
            scorer = SchemaValidationScorer(validation_func=validation_func)
        
        elif scorer_type == "dashboard_quality":
            scorer = DashboardQualityScorer()
        
        elif scorer_type == "kg_quality":
            scorer = KnowledgeGraphQualityScorer()
        
        elif scorer_type == "llm_judge":
            model = kwargs.get("model", "gpt-4o-mini")
            rubric = kwargs.get("rubric") or kwargs.get("prompt_template")  # Support both for compatibility
            api_key = kwargs.get("api_key")
            scorer = LLMJudgeScorer(
                model=model,
                rubric=rubric,
                api_key=api_key,
            )
        
        else:
            raise ValueError(f"Unknown scorer type: {scorer_type}")
        
        # Cache scorer
        self._scorers[scorer_id] = scorer
        
        self.logger.info(f"Created scorer: {scorer.name}")
        return scorer
    
    async def score_item(
        self,
        scorer: Scorer | str,
        item: DatasetItem,
        output: Any | None = None,
        **kwargs: Any,
    ) -> Score:
        """
        Score a single dataset item.
        
        Args:
            scorer: Scorer instance or scorer ID (if cached)
            item: Dataset item to score
            output: Generated output (if not in item.output)
            **kwargs: Additional parameters
            
        Returns:
            Score result
        """
        # Resolve scorer if ID provided
        if isinstance(scorer, str):
            if scorer not in self._scorers:
                raise ValueError(f"Scorer {scorer} not found. Create it first.")
            scorer = self._scorers[scorer]
        
        # Use output from item if not provided
        if output is None:
            output = item.output
        
        if output is None:
            raise ValueError("Output is required for scoring")
        
        # Get expected output
        expected = item.expected
        if expected is None:
            raise ValueError("Expected output is required for scoring")
        
        # Extract expected value (could be dict with 'yaml' key or direct value)
        if isinstance(expected, dict) and "yaml" in expected:
            expected_value = expected["yaml"]
        else:
            expected_value = expected
        
        # Build metadata from item
        metadata = {**item.metadata, "item_id": item.id}
        
        self.logger.info(f"Scoring item {item.id} with scorer {scorer.name}")
        
        score = scorer.score(
            generated=output,
            expected=expected_value,
            metadata=metadata,
        )
        
        self.logger.info(f"Item {item.id} scored: {score.name}={score.value}")
        return score
    
    async def list_scorers(self, **kwargs: Any) -> list[dict[str, Any]]:
        """
        List available scorers.
        
        Returns:
            List of scorer metadata
        """
        scorers = []
        
        # List cached scorers
        for scorer_id, scorer in self._scorers.items():
            scorers.append({
                "id": scorer_id,
                "name": scorer.name,
                "type": type(scorer).__name__,
            })
        
        # List available scorer types
        available_types = [
            {
                "type": "deep_diff",
                "description": "DeepDiff-based comparison scorer",
                "versions": ["v1", "v2", "v3"],
            },
            {
                "type": "schema_validation",
                "description": "Schema validation scorer",
            },
            {
                "type": "dashboard_quality",
                "description": "Dashboard quality metrics scorer",
            },
            {
                "type": "kg_quality",
                "description": "Knowledge graph quality metrics scorer",
            },
            {
                "type": "llm_judge",
                "description": "LLM-based judge scorer",
            },
        ]
        
        return {
            "cached": scorers,
            "available_types": available_types,
        }
