"""Dashboard-specific scorers.

This module contains scorers for evaluating dashboard quality.
The DashboardQualityScorer is currently designed for ml-infra dashboard format,
which uses "harness_query" as the query field name. This is a technical API
term, not branding - it's part of the ml-infra API contract.
"""

import json
from typing import Any

from deepdiff import DeepDiff

from aieval.scorers.base import Scorer
from aieval.core.types import Score


class DashboardQualityScorer(Scorer):
    """
    Scorer for dashboard generation quality.
    
    Evaluates dashboards based on:
    - Query validity (HQL format)
    - Widget count and type variety
    - Structural similarity
    
    Note: Currently designed for ml-infra dashboard format which uses
    "harness_query" field. Can be extended for other dashboard formats.
    """
    
    def __init__(
        self,
        name: str = "dashboard_quality",
        eval_id: str = "dashboard_quality.v1",
    ):
        """Initialize dashboard quality scorer."""
        super().__init__(name, eval_id)
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score dashboard quality.
        
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
        
        # Extract dashboard from response structure if needed
        if isinstance(generated, dict) and "dashboard" in generated:
            generated = generated["dashboard"]
        
        scores = self._evaluate_dashboard_quality(generated, expected)
        
        return Score(
            name=self.name,
            value=scores["overall"],
            eval_id=self.eval_id,
            comment=f"Dashboard quality: {scores['overall']:.2%}",
            metadata={**metadata, "metrics": scores},
        )
    
    def _evaluate_dashboard_quality(
        self, generated: dict[str, Any], expected: dict[str, Any]
    ) -> dict[str, float]:
        """Evaluate dashboard quality with multiple metrics."""
        scores = {}
        
        gen_widgets = generated.get("widgets", [])
        exp_widgets = expected.get("widgets", [])
        
        # Note: "harness_query" refers to the query format used by ml-infra dashboards
        # This is part of the ml-infra API contract for dashboard widgets
        gen_queries = [
            w.get("data_query", {}).get("harness_query", "") for w in gen_widgets
        ]
        
        # 1. HQL Query Validity
        valid_queries = sum(
            1
            for q in gen_queries
            if q and "find" in q and ("entity" in q or "event" in q or "metric" in q)
        )
        scores["query_validity"] = valid_queries / max(len(gen_queries), 1)
        
        # 2. Query Has Limit
        queries_with_limit = sum(1 for q in gen_queries if "limit" in q.lower())
        scores["query_has_limit"] = queries_with_limit / max(len(gen_queries), 1)
        
        # 3. Widget Count Match
        gen_count = len(gen_widgets)
        exp_count = len(exp_widgets)
        if exp_count == 0:
            scores["widget_count_match"] = 1.0 if gen_count == 0 else 0.0
        else:
            scores["widget_count_match"] = max(
                0, 1 - abs(gen_count - exp_count) / exp_count
            )
        
        # 4. Widget Type Variety
        gen_types = [w.get("type", "TABLE") for w in gen_widgets]
        unique_gen_types = len(set(gen_types))
        exp_types = [w.get("type", "TABLE") for w in exp_widgets]
        unique_exp_types = len(set(exp_types))
        
        if unique_exp_types == 0:
            scores["widget_type_variety"] = 1.0 if unique_gen_types == 0 else 0.5
        else:
            scores["widget_type_variety"] = min(1.0, unique_gen_types / unique_exp_types)
        
        # Penalize if everything is TABLE
        table_ratio = sum(1 for t in gen_types if t == "TABLE") / max(len(gen_types), 1)
        if table_ratio > 0.7:
            scores["widget_type_variety"] *= 0.5
        
        # 5. Widget Type Match
        type_matches = sum(
            1
            for i in range(min(len(gen_types), len(exp_types)))
            if gen_types[i] == exp_types[i]
        )
        scores["widget_type_match"] = type_matches / max(len(exp_types), 1)
        
        # 6. Structural Similarity
        def simplify_for_comparison(data: dict[str, Any]) -> dict[str, Any]:
            """Simplify dashboard for structural comparison."""
            simplified = data.copy()
            if "widgets" in simplified:
                widgets = []
                for w in simplified["widgets"]:
                    simplified_widget = {
                        "title": w.get("title", ""),
                        "type": w.get("type", ""),
                        # Note: "harness_query" is ml-infra specific query format
                        "has_query": bool(w.get("data_query", {}).get("harness_query", "")),
                        "column_count": len(w.get("columns", [])),
                    }
                    widgets.append(simplified_widget)
                simplified["widgets"] = widgets
            return simplified
        
        simplified_gen = simplify_for_comparison(generated)
        simplified_exp = simplify_for_comparison(expected)
        
        diff = DeepDiff(simplified_exp, simplified_gen, ignore_order=True, verbose_level=0)
        if not diff:
            scores["structural_similarity"] = 1.0
        else:
            diff_count = sum(
                len(v) if isinstance(v, (list, dict)) else 1 for v in diff.values()
            )
            scores["structural_similarity"] = max(0, 1 - (diff_count / 10))
        
        # 7. Column Mapping Quality
        widgets_with_columns = sum(1 for w in gen_widgets if w.get("columns"))
        scores["has_column_mapping"] = widgets_with_columns / max(len(gen_widgets), 1)
        
        # Overall score (weighted average)
        weights = {
            "query_validity": 0.30,
            "query_has_limit": 0.10,
            "widget_count_match": 0.15,
            "widget_type_variety": 0.15,
            "widget_type_match": 0.15,
            "structural_similarity": 0.10,
            "has_column_mapping": 0.05,
        }
        
        scores["overall"] = sum(scores[k] * weights[k] for k in weights.keys())
        
        return scores
