"""CSV sink for file output.

This sink outputs scores in CSV format compatible with ml-infra/evals.
The format includes all score metadata and can be used for comparison.
"""

import csv
import logging
import os
from pathlib import Path
from typing import Any

from ai_evolution.sinks.base import Sink
from ai_evolution.core.types import Score, ExperimentRun

logger = logging.getLogger(__name__)


class CSVSink(Sink):
    """Sink that outputs to CSV file."""
    
    def __init__(self, path: str | Path):
        """
        Initialize CSV sink.
        
        Args:
            path: Path to CSV file (will be created if doesn't exist)
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.scores: list[dict[str, Any]] = []
        self._header_written = False
    
    def emit(self, score: Score) -> None:
        """
        Add score to buffer.
        
        Flattens score metadata for CSV compatibility with ml-infra/evals format.
        """
        score_dict = score.to_dict()
        
        # Flatten metadata into top-level columns (ml-infra/evals format)
        metadata = score_dict.pop("metadata", {})
        for key, value in metadata.items():
            # Avoid overwriting existing keys
            if key not in score_dict:
                score_dict[key] = value
        
        self.scores.append(score_dict)
    
    def emit_run(self, run: ExperimentRun) -> None:
        """Emit all scores from run."""
        for score in run.scores:
            self.emit(score)
    
    def flush(self) -> None:
        """
        Write scores to CSV file.
        
        Output format is compatible with ml-infra/evals CSV structure:
        - All score fields as columns
        - Metadata flattened into columns
        - Consistent column ordering
        """
        if not self.scores:
            logger.warning(f"No scores to write to {self.path}")
            return
        
        # Determine columns (prioritize common fields first for readability)
        all_keys = set()
        for score_dict in self.scores:
            all_keys.update(score_dict.keys())
        
        # Order columns: core fields first, then metadata
        core_fields = ["name", "value", "eval_id", "test_id", "entity_type", "operation_type"]
        ordered_columns = []
        for field in core_fields:
            if field in all_keys:
                ordered_columns.append(field)
                all_keys.remove(field)
        
        # Add remaining fields sorted
        ordered_columns.extend(sorted(all_keys))
        
        # Write CSV
        try:
            with self.path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=ordered_columns, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(self.scores)
            
            logger.info(f"Wrote {len(self.scores)} scores to {self.path}")
        except Exception as e:
            logger.error(f"Failed to write CSV to {self.path}: {e}")
            raise
