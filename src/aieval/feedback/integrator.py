"""Feedback integrator for using feedback to improve evaluation."""

from typing import Any
import structlog

from aieval.feedback.collector import FeedbackCollector
from aieval.core.types import Score

logger = structlog.get_logger(__name__)


class FeedbackIntegrator:
    """
    Integrates user feedback into evaluation results.
    
    Can weight scores by feedback, learn from feedback patterns, etc.
    """
    
    def __init__(self, feedback_collector: FeedbackCollector | None = None):
        """
        Initialize feedback integrator.
        
        Args:
            feedback_collector: FeedbackCollector instance (creates new if None)
        """
        self.collector = feedback_collector or FeedbackCollector()
        self.logger = structlog.get_logger(__name__)
    
    def weight_score_by_feedback(
        self,
        score: Score,
        trace_id: str | None = None,
        run_id: str | None = None,
        weight_factor: float = 0.5,
    ) -> Score:
        """
        Weight a score by user feedback.
        
        Args:
            score: Original score
            trace_id: Optional trace ID for feedback lookup
            run_id: Optional run ID for feedback lookup
            weight_factor: Weight factor for feedback (0.0 to 1.0)
            
        Returns:
            Weighted score
        """
        feedback = self.collector.get_feedback(trace_id=trace_id, run_id=run_id)
        
        if not feedback:
            return score
        
        # Calculate feedback score (average of ratings/thumbs)
        feedback_score = 0.0
        feedback_count = 0
        
        for entry in feedback:
            if entry.get("rating") is not None:
                # Normalize rating (1-5) to 0-1
                feedback_score += (entry["rating"] - 1) / 4.0
                feedback_count += 1
            elif entry.get("thumbs_up") is not None:
                feedback_score += 1.0 if entry["thumbs_up"] else 0.0
                feedback_count += 1
        
        if feedback_count == 0:
            return score
        
        avg_feedback = feedback_score / feedback_count
        
        # Weight original score with feedback
        original_value = float(score.value) if isinstance(score.value, (int, float)) else (1.0 if score.value else 0.0)
        weighted_value = (1.0 - weight_factor) * original_value + weight_factor * avg_feedback
        
        # Create new score with weighted value
        new_score = Score(
            name=score.name,
            value=weighted_value,
            eval_id=score.eval_id,
            comment=score.comment,
            metadata={
                **score.metadata,
                "feedback_weighted": True,
                "original_value": original_value,
                "feedback_score": avg_feedback,
                "weight_factor": weight_factor,
            },
            trace_id=score.trace_id,
            observation_id=score.observation_id,
        )
        
        return new_score
    
    def learn_from_feedback_patterns(
        self,
        scores: list[Score],
        feedback_threshold: float = 0.7,
    ) -> dict[str, Any]:
        """
        Learn patterns from feedback to improve evaluation.
        
        Args:
            scores: List of scores
            feedback_threshold: Threshold for considering feedback significant
            
        Returns:
            Dictionary with learned patterns
        """
        patterns = {
            "high_feedback_low_score": [],
            "low_feedback_high_score": [],
            "consistent_feedback": [],
        }
        
        for score in scores:
            trace_id = score.trace_id
            run_id = score.metadata.get("run_id")
            
            feedback = self.collector.get_feedback(trace_id=trace_id, run_id=run_id)
            if not feedback:
                continue
            
            avg_rating = self.collector.get_average_rating(trace_id=trace_id, run_id=run_id)
            if avg_rating is None:
                continue
            
            score_value = float(score.value) if isinstance(score.value, (int, float)) else (1.0 if score.value else 0.0)
            
            # Identify patterns
            if avg_rating >= feedback_threshold and score_value < 0.5:
                patterns["high_feedback_low_score"].append({
                    "score_name": score.name,
                    "score_value": score_value,
                    "feedback_rating": avg_rating,
                    "trace_id": trace_id,
                })
            elif avg_rating < (1.0 - feedback_threshold) and score_value >= 0.5:
                patterns["low_feedback_high_score"].append({
                    "score_name": score.name,
                    "score_value": score_value,
                    "feedback_rating": avg_rating,
                    "trace_id": trace_id,
                })
            elif abs(avg_rating - score_value) < 0.2:
                patterns["consistent_feedback"].append({
                    "score_name": score.name,
                    "score_value": score_value,
                    "feedback_rating": avg_rating,
                    "trace_id": trace_id,
                })
        
        return patterns
