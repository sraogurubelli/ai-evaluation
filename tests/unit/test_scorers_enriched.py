"""Tests for EnrichedOutputScorer wrapper."""

import json
import pytest

from ai_evolution.scorers.enriched import EnrichedOutputScorer
from ai_evolution.scorers.deep_diff import DeepDiffScorer
from ai_evolution.core.types import Score


class TestEnrichedOutputScorer:
    """Tests for EnrichedOutputScorer wrapper."""
    
    def test_init_inherits_name_and_eval_id(self):
        """Test that wrapper inherits name and eval_id from base scorer."""
        base_scorer = DeepDiffScorer(
            name="test_scorer",
            eval_id="test.v1",
            version="v1"
        )
        wrapper = EnrichedOutputScorer(base_scorer)
        
        assert wrapper.name == "test_scorer"
        assert wrapper.eval_id == "test.v1"
        assert wrapper.base_scorer is base_scorer
    
    def test_extract_yaml_from_enriched_json(self):
        """Test extraction of YAML from enriched JSON output."""
        base_scorer = DeepDiffScorer(version="v1")
        wrapper = EnrichedOutputScorer(base_scorer)
        
        enriched_output = json.dumps({
            "final_yaml": "key: value",
            "events": [],
            "tools_called": [],
            "metrics": {"latency_ms": 1000}
        })
        
        yaml_content, metrics = wrapper._extract_yaml_and_metrics(enriched_output)
        
        assert yaml_content == "key: value"
        assert metrics["metrics"]["latency_ms"] == 1000
    
    def test_extract_yaml_from_raw_yaml(self):
        """Test that raw YAML passes through unchanged."""
        base_scorer = DeepDiffScorer(version="v1")
        wrapper = EnrichedOutputScorer(base_scorer)
        
        raw_yaml = "key: value"
        
        yaml_content, metrics = wrapper._extract_yaml_and_metrics(raw_yaml)
        
        assert yaml_content == "key: value"
        assert metrics == {}
    
    def test_extract_yaml_from_dict(self):
        """Test that dict input passes through unchanged."""
        base_scorer = DeepDiffScorer(version="v1")
        wrapper = EnrichedOutputScorer(base_scorer)
        
        dict_input = {"key": "value"}
        
        yaml_content, metrics = wrapper._extract_yaml_and_metrics(dict_input)
        
        assert yaml_content == {"key": "value"}
        assert metrics == {}
    
    def test_score_with_enriched_output(self):
        """Test scoring with enriched JSON output."""
        base_scorer = DeepDiffScorer(
            name="structure",
            eval_id="structure.v1",
            version="v1"
        )
        wrapper = EnrichedOutputScorer(base_scorer)
        
        enriched_output = json.dumps({
            "final_yaml": "key: value",
            "events": [{"event": "test", "data": {}}],
            "tools_called": [{"tool": "search"}],
            "metrics": {
                "latency_ms": 1000,
                "total_tokens": 500
            }
        })
        
        expected = "key: value"
        metadata = {"test_id": "test1"}
        
        score = wrapper.score(enriched_output, expected, metadata)
        
        # Should score the extracted YAML
        assert isinstance(score, Score)
        assert score.name == "structure"
        assert score.eval_id == "structure.v1"
        
        # Metadata should be enriched
        assert "adapter_metrics" in score.metadata
        assert score.metadata["adapter_metrics"]["latency_ms"] == 1000
        assert score.metadata["adapter_metrics"]["total_tokens"] == 500
        assert score.metadata["tools_called"] == [{"tool": "search"}]
        assert score.metadata["event_count"] == 1
        assert score.metadata["latency_ms"] == 1000
        assert score.metadata["total_tokens"] == 500
    
    def test_score_with_raw_yaml(self):
        """Test scoring with raw YAML (backward compatibility)."""
        base_scorer = DeepDiffScorer(
            name="structure",
            eval_id="structure.v1",
            version="v1"
        )
        wrapper = EnrichedOutputScorer(base_scorer)
        
        raw_yaml = "key: value"
        expected = "key: value"
        metadata = {"test_id": "test1"}
        
        score = wrapper.score(raw_yaml, expected, metadata)
        
        # Should score normally
        assert isinstance(score, Score)
        assert score.name == "structure"
        assert score.value == 1.0  # Perfect match
        
        # Metadata should not be enriched (no adapter_metrics)
        assert "adapter_metrics" not in score.metadata
    
    def test_score_with_malformed_json(self):
        """Test handling of malformed enriched JSON."""
        base_scorer = DeepDiffScorer(
            name="structure",
            eval_id="structure.v1",
            version="v1"
        )
        wrapper = EnrichedOutputScorer(base_scorer)
        
        malformed = "{invalid json"
        expected = "key: value"
        metadata = {"test_id": "test1"}
        
        # Should fall back to treating as raw YAML
        score = wrapper.score(malformed, expected, metadata)
        
        # Should return error or attempt to parse as YAML
        assert isinstance(score, Score)
        assert score.name == "structure"
    
    def test_score_preserves_original_metadata(self):
        """Test that original metadata is preserved and extended."""
        base_scorer = DeepDiffScorer(
            name="structure",
            eval_id="structure.v1",
            version="v1"
        )
        wrapper = EnrichedOutputScorer(base_scorer)
        
        enriched_output = json.dumps({
            "final_yaml": "key: value",
            "events": [],
            "tools_called": [],
            "metrics": {"latency_ms": 1000}
        })
        
        original_metadata = {
            "test_id": "test1",
            "entity_type": "pipeline",
            "custom_field": "custom_value"
        }
        
        score = wrapper.score(enriched_output, "key: value", original_metadata)
        
        # Original metadata should be preserved
        assert score.metadata["test_id"] == "test1"
        assert score.metadata["entity_type"] == "pipeline"
        assert score.metadata["custom_field"] == "custom_value"
        
        # Adapter metrics should be added
        assert "adapter_metrics" in score.metadata
    
    def test_score_with_different_base_scorers(self):
        """Test wrapper works with different base scorer types."""
        from ai_evolution.scorers.autoevals import LevenshteinScorer
        
        base_scorer = LevenshteinScorer(
            name="similarity",
            eval_id="lev.v1"
        )
        wrapper = EnrichedOutputScorer(base_scorer)
        
        enriched_output = json.dumps({
            "final_yaml": "test output",
            "events": [],
            "tools_called": [],
            "metrics": {}
        })
        
        score = wrapper.score(enriched_output, "test output", {})
        
        # Should work with different scorer types
        assert isinstance(score, Score)
        assert score.name == "similarity"
        assert score.eval_id == "lev.v1"
    
    def test_repr(self):
        """Test string representation."""
        base_scorer = DeepDiffScorer(version="v1")
        wrapper = EnrichedOutputScorer(base_scorer)
        
        repr_str = repr(wrapper)
        
        assert "EnrichedOutputScorer" in repr_str
        assert "base_scorer" in repr_str
