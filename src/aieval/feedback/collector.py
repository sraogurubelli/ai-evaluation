"""Feedback collector for user feedback."""

from typing import Any
from pathlib import Path
import json
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class FeedbackCollector:
    """
    Collects user feedback (thumbs up/down, ratings, etc.) and links it to traces/runs.
    """

    def __init__(self, storage_path: str | Path | None = None):
        """
        Initialize feedback collector.

        Args:
            storage_path: Path to JSON file for storing feedback.
                         If None, uses ~/.aieval/feedback.json
        """
        if storage_path is None:
            storage_path = Path.home() / ".aieval" / "feedback.json"
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = structlog.get_logger(__name__)
        self._feedback: list[dict[str, Any]] = []
        self._load_feedback()

    def _load_feedback(self) -> None:
        """Load feedback from storage file."""
        if self.storage_path.exists():
            try:
                with self.storage_path.open("r") as f:
                    self._feedback = json.load(f)
            except Exception:
                self._feedback = []

    def _save_feedback(self) -> None:
        """Save feedback to storage file."""
        try:
            with self.storage_path.open("w") as f:
                json.dump(self._feedback, f, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to save feedback: {e}")

    def collect_feedback(
        self,
        trace_id: str | None = None,
        run_id: str | None = None,
        rating: int | None = None,
        thumbs_up: bool | None = None,
        comment: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Collect user feedback.

        Args:
            trace_id: Optional trace ID
            run_id: Optional run ID
            rating: Optional rating (1-5)
            thumbs_up: Optional thumbs up/down
            comment: Optional comment
            metadata: Optional additional metadata

        Returns:
            Feedback ID
        """
        import uuid

        feedback_id = str(uuid.uuid4())

        feedback_entry = {
            "feedback_id": feedback_id,
            "trace_id": trace_id,
            "run_id": run_id,
            "rating": rating,
            "thumbs_up": thumbs_up,
            "comment": comment,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
        }

        self._feedback.append(feedback_entry)
        self._save_feedback()

        self.logger.info(
            "Feedback collected", feedback_id=feedback_id, trace_id=trace_id, run_id=run_id
        )

        return feedback_id

    def get_feedback(
        self,
        trace_id: str | None = None,
        run_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get feedback for a trace or run.

        Args:
            trace_id: Optional trace ID filter
            run_id: Optional run ID filter

        Returns:
            List of feedback entries
        """
        filtered = []
        for entry in self._feedback:
            if trace_id and entry.get("trace_id") != trace_id:
                continue
            if run_id and entry.get("run_id") != run_id:
                continue
            filtered.append(entry)
        return filtered

    def get_average_rating(
        self,
        trace_id: str | None = None,
        run_id: str | None = None,
    ) -> float | None:
        """
        Get average rating for a trace or run.

        Args:
            trace_id: Optional trace ID filter
            run_id: Optional run ID filter

        Returns:
            Average rating or None if no ratings
        """
        feedback = self.get_feedback(trace_id=trace_id, run_id=run_id)
        ratings = [f["rating"] for f in feedback if f.get("rating") is not None]

        if not ratings:
            return None

        return sum(ratings) / len(ratings)
