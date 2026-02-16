"""Knowledge Graph-specific scorers."""

import json
from typing import Any

from aieval.scorers.base import Scorer
from aieval.core.types import Score


class KnowledgeGraphQualityScorer(Scorer):
    """Scorer for knowledge graph response quality."""

    def __init__(
        self,
        name: str = "kg_quality",
        eval_id: str = "kg_quality.v1",
    ):
        """Initialize KG quality scorer."""
        super().__init__(name, eval_id)

    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score knowledge graph quality.

        Returns overall score (weighted average of all metrics).
        Individual metric scores are stored in metadata.
        """
        # Parse JSON if strings
        if isinstance(generated, str):
            try:
                generated = json.loads(generated)
            except json.JSONDecodeError:
                return Score(
                    name=self.name,
                    value=0.0,
                    eval_id=self.eval_id,
                    comment="Failed to parse generated JSON",
                    metadata=metadata,
                )

        if isinstance(expected, str):
            try:
                expected = json.loads(expected)
            except json.JSONDecodeError:
                return Score(
                    name=self.name,
                    value=0.0,
                    eval_id=self.eval_id,
                    comment="Failed to parse expected JSON",
                    metadata=metadata,
                )

        # Extract kg_response from response structure if needed
        if isinstance(generated, dict) and "kg_response" in generated:
            generated = generated["kg_response"]

        scores = self._evaluate_kg_quality(generated, expected)

        return Score(
            name=self.name,
            value=scores["overall"],
            eval_id=self.eval_id,
            comment=f"KG quality: {scores['overall']:.2%}",
            metadata={**metadata, "metrics": scores},
        )

    def _evaluate_kg_quality(
        self, generated: dict[str, Any], expected: dict[str, Any]
    ) -> dict[str, float]:
        """Evaluate KG quality with multiple metrics."""
        scores = {}

        gen_insights = generated.get("insights", [])
        exp_insights = expected.get("insights", [])
        gen_count = len(gen_insights)
        exp_count = len(exp_insights)

        # 1. Insight Count Match
        if exp_count == 0:
            scores["insight_count_match"] = 1.0 if gen_count == 0 else 0.0
        else:
            scores["insight_count_match"] = max(0, 1 - abs(gen_count - exp_count) / exp_count)

        # 2. HQL Query Validity
        gen_queries = []
        for insight in gen_insights:
            for query in insight.get("queries", []):
                hql = query.get("hql", "")
                if hql:
                    gen_queries.append(hql)

        valid_queries = sum(
            1
            for q in gen_queries
            if "find" in q and ("entity" in q or "event" in q or "metric" in q)
        )
        scores["query_validity"] = valid_queries / max(len(gen_queries), 1) if gen_queries else 0.0

        # Query has limit
        queries_with_limit = sum(1 for q in gen_queries if "limit" in q.lower())
        scores["query_has_limit"] = (
            queries_with_limit / max(len(gen_queries), 1) if gen_queries else 0.0
        )

        # 3. Graph Structure Presence
        gen_graph = generated.get("graphUpdates", {})
        exp_graph = expected.get("graphUpdates", {})

        gen_nodes = gen_graph.get("nodes", [])
        exp_nodes = exp_graph.get("nodes", [])

        if len(exp_nodes) == 0:
            scores["node_count_match"] = 1.0 if len(gen_nodes) == 0 else 0.5
        else:
            scores["node_count_match"] = max(
                0, 1 - abs(len(gen_nodes) - len(exp_nodes)) / len(exp_nodes)
            )

        gen_edges = gen_graph.get("edges", [])
        exp_edges = exp_graph.get("edges", [])

        if len(exp_edges) == 0:
            scores["edge_count_match"] = 1.0 if len(gen_edges) == 0 else 0.5
        else:
            scores["edge_count_match"] = max(
                0, 1 - abs(len(gen_edges) - len(exp_edges)) / len(exp_edges)
            )

        # 4. Explanation Quality
        gen_explanation = generated.get("explanation", [])
        exp_explanation = expected.get("explanation", [])

        scores["has_explanation"] = 1.0 if len(gen_explanation) > 0 else 0.0

        if len(exp_explanation) == 0:
            scores["explanation_steps_match"] = 1.0 if len(gen_explanation) == 0 else 0.5
        else:
            scores["explanation_steps_match"] = max(
                0,
                1 - abs(len(gen_explanation) - len(exp_explanation)) / len(exp_explanation),
            )

        # 5. Insight Completeness
        complete_insights = sum(
            1
            for insight in gen_insights
            if insight.get("title") and insight.get("detail") and insight.get("queries")
        )
        scores["insight_completeness"] = (
            complete_insights / max(len(gen_insights), 1) if gen_insights else 0.0
        )

        # 6. Severity Levels Present
        insights_with_severity = sum(1 for insight in gen_insights if insight.get("severity"))
        scores["has_severity"] = (
            insights_with_severity / max(len(gen_insights), 1) if gen_insights else 0.0
        )

        # 7. Follow-up Questions and Suggestions
        scores["has_follow_up"] = 1.0 if generated.get("follow_up_questions") else 0.0
        scores["has_suggestions"] = 1.0 if generated.get("suggestions") else 0.0

        # Overall score (weighted average)
        weights = {
            "insight_count_match": 0.15,
            "query_validity": 0.25,
            "query_has_limit": 0.10,
            "node_count_match": 0.10,
            "edge_count_match": 0.05,
            "has_explanation": 0.10,
            "explanation_steps_match": 0.05,
            "insight_completeness": 0.10,
            "has_severity": 0.05,
            "has_follow_up": 0.025,
            "has_suggestions": 0.025,
        }

        scores["overall"] = sum(scores[k] * weights[k] for k in weights.keys())

        return scores
