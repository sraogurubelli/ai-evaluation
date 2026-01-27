"""Tests for core types."""

import pytest
from ai_evolution.core.types import Score, ExperimentRun, DatasetItem
from datetime import datetime


def test_score_creation():
    """Test Score creation."""
    score = Score(
        name="test_score",
        value=0.85,
        eval_id="test.v1",
        comment="Test comment",
    )
    
    assert score.name == "test_score"
    assert score.value == 0.85
    assert score.eval_id == "test.v1"
    assert score.comment == "Test comment"


def test_score_to_dict():
    """Test Score to_dict conversion."""
    score = Score(
        name="test_score",
        value=0.85,
        eval_id="test.v1",
    )
    
    score_dict = score.to_dict()
    assert score_dict["name"] == "test_score"
    assert score_dict["value"] == 0.85


def test_experiment_run_creation():
    """Test ExperimentRun creation."""
    scores = [
        Score(name="score1", value=0.8, eval_id="test.v1"),
        Score(name="score2", value=0.9, eval_id="test.v1"),
    ]
    
    run = ExperimentRun(
        experiment_id="exp1",
        run_id="run1",
        dataset_id="dataset1",
        scores=scores,
    )
    
    assert run.experiment_id == "exp1"
    assert len(run.scores) == 2


def test_dataset_item_creation():
    """Test DatasetItem creation."""
    item = DatasetItem(
        id="test-001",
        input={"prompt": "Test prompt"},
        expected={"yaml": "test: yaml"},
    )
    
    assert item.id == "test-001"
    assert item.input["prompt"] == "Test prompt"
