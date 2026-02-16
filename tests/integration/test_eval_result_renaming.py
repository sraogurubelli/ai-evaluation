"""Integration tests for EvalResult renaming from Run."""

import pytest
from aieval.core.types import EvalResult, Score, DatasetItem
from aieval.sdk.comparison import compare_eval_results, EvalResultComparison, get_regressions
from aieval.agents.tools import EvalTool, CompareEvalResultsTool, execute_tool


class TestEvalResultRenaming:
    """Test that all Run references have been renamed to EvalResult."""
    
    def test_eval_result_creation(self):
        """Test creating EvalResult objects."""
        eval_result = EvalResult(
            eval_id="test-eval",
            run_id="test-run-001",
            dataset_id="test-dataset",
            scores=[
                Score(name="score1", value=0.9, eval_id="score1.v1"),
            ],
            metadata={"model": "gpt-4o"},
        )
        
        assert eval_result.eval_id == "test-eval"
        assert eval_result.run_id == "test-run-001"
        assert len(eval_result.scores) == 1
        assert eval_result.metadata["model"] == "gpt-4o"
    
    def test_compare_eval_results(self):
        """Test comparing two eval results."""
        eval_result1 = EvalResult(
            eval_id="eval-001",
            run_id="run-001",
            dataset_id="dataset-001",
            scores=[
                Score(name="score1", value=0.8, eval_id="score1.v1", metadata={"dataset_item_id": "item-001"}),
            ],
        )
        
        eval_result2 = EvalResult(
            eval_id="eval-001",
            run_id="run-002",
            dataset_id="dataset-001",
            scores=[
                Score(name="score1", value=0.9, eval_id="score1.v1", metadata={"dataset_item_id": "item-001"}),
            ],
        )
        
        comparison = compare_eval_results(eval_result1, eval_result2)
        
        assert isinstance(comparison, EvalResultComparison)
        assert comparison.eval_result1_id == "run-001"
        assert comparison.eval_result2_id == "run-002"
        assert "score1" in comparison.improvements or "score1" in comparison.regressions
    
    def test_eval_tool_class(self):
        """Test that EvalTool class exists and can be instantiated."""
        tool = EvalTool()
        assert tool.name == "eval"
        assert "Run an evaluation" in tool.description or "evaluation" in tool.description.lower()
    
    def test_compare_eval_results_tool_class(self):
        """Test that CompareEvalResultsTool class exists."""
        tool = CompareEvalResultsTool()
        assert tool.name == "compare_eval_results"
        assert "compare" in tool.description.lower()
    
    def test_execute_tool_function(self):
        """Test that execute_tool function exists."""
        # Just verify it's callable and has correct signature
        assert callable(execute_tool)
        import inspect
        sig = inspect.signature(execute_tool)
        assert "tool_name" in sig.parameters


