"""Scorer-related tools."""

from typing import Any
import os

from aieval.agents.tools.base import Tool, ToolResult
from aieval.scorers.base import Scorer
from aieval.scorers.deep_diff import DeepDiffScorer
from aieval.scorers.schema_validation import SchemaValidationScorer
from aieval.scorers.dashboard import DashboardQualityScorer
from aieval.scorers.knowledge_graph import KnowledgeGraphQualityScorer


class CreateScorerTool(Tool):
    """Tool for creating scorers."""

    def __init__(self):
        super().__init__(
            name="create_scorer",
            description="Create a scorer for evaluation",
            parameters_schema={
                "type": "object",
                "properties": {
                    "scorer_type": {
                        "type": "string",
                        "enum": [
                            "deep_diff",
                            "schema_validation",
                            "dashboard_quality",
                            "kg_quality",
                            "llm_judge",
                        ],
                        "description": "Type of scorer to create",
                    },
                    "name": {
                        "type": "string",
                        "description": "Scorer name (optional, defaults based on type)",
                    },
                    "eval_id": {
                        "type": "string",
                        "description": "Evaluation ID (optional, defaults based on type)",
                    },
                    # DeepDiff-specific
                    "version": {
                        "type": "string",
                        "description": "DeepDiff version (v1, v2, v3) - for deep_diff scorer",
                    },
                    "entity_type": {
                        "type": "string",
                        "description": "Entity type filter - for deep_diff scorer",
                    },
                    # LLM Judge-specific
                    "model": {
                        "type": "string",
                        "description": "Model name for LLM judge scorer",
                    },
                    "rubric": {
                        "type": "string",
                        "description": "Rubric for LLM judge scorer",
                    },
                    "api_key": {
                        "type": "string",
                        "description": "API key for LLM judge scorer",
                    },
                },
                "required": ["scorer_type"],
            },
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute scorer creation."""
        try:
            self.validate_parameters(**kwargs)

            scorer_type = kwargs["scorer_type"]
            scorer: Scorer | None = None

            if scorer_type == "deep_diff":
                version = kwargs.get("version", "v3")
                name = kwargs.get("name", f"deep_diff_{version}")
                eval_id = kwargs.get("eval_id", f"deep_diff_{version}.v1")
                scorer = DeepDiffScorer(
                    name=name,
                    eval_id=eval_id,
                    version=version,
                    entity_type=kwargs.get("entity_type"),
                )
            elif scorer_type == "schema_validation":
                name = kwargs.get("name", "schema_validation")
                eval_id = kwargs.get("eval_id", "schema_validation.v1")
                scorer = SchemaValidationScorer(
                    name=name,
                    eval_id=eval_id,
                )
            elif scorer_type == "dashboard_quality":
                name = kwargs.get("name", "dashboard_quality")
                eval_id = kwargs.get("eval_id", "dashboard_quality.v1")
                scorer = DashboardQualityScorer(
                    name=name,
                    eval_id=eval_id,
                )
            elif scorer_type == "kg_quality":
                name = kwargs.get("name", "kg_quality")
                eval_id = kwargs.get("eval_id", "kg_quality.v1")
                scorer = KnowledgeGraphQualityScorer(
                    name=name,
                    eval_id=eval_id,
                )
            elif scorer_type == "llm_judge":
                from aieval.scorers.llm_judge import LLMJudgeScorer

                model = kwargs.get("model", "gpt-4o-mini")
                rubric = kwargs.get("rubric")
                api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")

                if not api_key:
                    return ToolResult(
                        success=False,
                        data=None,
                        error="API key required for LLM judge scorer (provide api_key or set OPENAI_API_KEY)",
                    )

                name = kwargs.get("name", f"llm_judge_{model}")
                eval_id = kwargs.get("eval_id", f"llm_judge_{model}.v1")
                scorer = LLMJudgeScorer(
                    name=name,
                    eval_id=eval_id,
                    model=model,
                    rubric=rubric,
                    api_key=api_key,
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown scorer type: {scorer_type}",
                )

            return ToolResult(
                success=True,
                data={
                    "scorer": {
                        "name": scorer.name,
                        "eval_id": scorer.eval_id,
                        "type": scorer_type,
                    },
                },
                metadata={"scorer_type": scorer_type},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )
