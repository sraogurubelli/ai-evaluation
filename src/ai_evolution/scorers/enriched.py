"""Enriched output scorer wrapper.

This wrapper allows existing scorers to work with enriched adapter output
that contains both the final YAML and collected metrics/events.
"""

import json
import logging
from typing import Any

from ai_evolution.scorers.base import Scorer
from ai_evolution.core.types import Score

logger = logging.getLogger(__name__)


class EnrichedOutputScorer(Scorer):
    """
    Wrapper scorer that extracts YAML from enriched adapter output.
    
    This wrapper enables existing scorers to work with enriched output from
    SSEStreamingAdapter. It:
    - Detects enriched JSON format vs raw YAML
    - Extracts final_yaml from enriched output
    - Enriches metadata with adapter metrics, tools, and events
    - Delegates to the wrapped scorer with extracted YAML
    - Falls back to direct delegation for non-enriched input
    
    Example:
        # Wrap an existing scorer
        deep_diff = DeepDiffScorer(name="structure", eval_id="structure.v3")
        wrapped_scorer = EnrichedOutputScorer(deep_diff)
        
        # Use with enriched output from SSEStreamingAdapter
        score = wrapped_scorer.score(enriched_output, expected, metadata)
    """
    
    def __init__(self, base_scorer: Scorer):
        """
        Initialize wrapper scorer.
        
        Args:
            base_scorer: Existing scorer to wrap (e.g., DeepDiffScorer)
        """
        # Inherit name and eval_id from base scorer
        super().__init__(
            name=base_scorer.name,
            eval_id=base_scorer.eval_id,
        )
        self.base_scorer = base_scorer
    
    def _extract_yaml_and_metrics(
        self,
        generated: Any,
    ) -> tuple[Any, dict[str, Any]]:
        """
        Extract YAML and metrics from generated output.
        
        Args:
            generated: Generated output (enriched JSON or raw YAML)
            
        Returns:
            Tuple of (yaml_content, adapter_metrics)
        """
        # If not a string, return as-is (already parsed dict)
        if not isinstance(generated, str):
            return generated, {}
        
        try:
            # Try to parse as JSON (enriched format)
            data = json.loads(generated)
            
            # Check if it's enriched format
            if isinstance(data, dict) and "final_yaml" in data:
                return data["final_yaml"], {
                    "metrics": data.get("metrics", {}),
                    "tools_called": data.get("tools_called", []),
                    "events": data.get("events", []),
                    "event_count": len(data.get("events", [])),
                }
        except (json.JSONDecodeError, KeyError):
            # Not enriched format, continue
            pass
        
        # Not enriched format, return as-is
        return generated, {}
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score with automatic format detection and extraction.
        
        Args:
            generated: Generated output (enriched JSON or raw YAML)
            expected: Expected output
            metadata: Additional metadata
            
        Returns:
            Score from base scorer with enriched metadata
        """
        try:
            # Extract YAML and metrics from enriched output
            yaml_content, adapter_metrics = self._extract_yaml_and_metrics(generated)
            
            # Enrich metadata with adapter metrics if available
            enriched_metadata = metadata.copy()
            if adapter_metrics:
                enriched_metadata["adapter_metrics"] = adapter_metrics.get("metrics", {})
                enriched_metadata["tools_called"] = adapter_metrics.get("tools_called", [])
                enriched_metadata["event_count"] = adapter_metrics.get("event_count", 0)
                
                # Add individual metric fields for easier access
                metrics = adapter_metrics.get("metrics", {})
                if "latency_ms" in metrics:
                    enriched_metadata["latency_ms"] = metrics["latency_ms"]
                if "total_tokens" in metrics:
                    enriched_metadata["total_tokens"] = metrics["total_tokens"]
            
            # Delegate to base scorer with extracted YAML
            return self.base_scorer.score(
                generated=yaml_content,
                expected=expected,
                metadata=enriched_metadata,
            )
        
        except Exception as e:
            # Fallback: try using base scorer directly
            # This handles cases where extraction fails or format is unexpected
            logger.debug(f"Enriched extraction failed, falling back to direct delegation: {e}")
            try:
                return self.base_scorer.score(generated, expected, metadata)
            except Exception as fallback_error:
                # If fallback also fails, return error score
                return Score(
                    name=self.name,
                    value=0.0,
                    eval_id=self.eval_id,
                    comment=f"Error parsing enriched output: {e}. Fallback error: {fallback_error}",
                    metadata=metadata,
                )
    
    def __repr__(self) -> str:
        return f"EnrichedOutputScorer(base_scorer={self.base_scorer})"
