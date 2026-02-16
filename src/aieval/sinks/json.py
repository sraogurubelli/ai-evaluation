"""JSON sink for file output."""

import json
from pathlib import Path

from aieval.sinks.base import Sink
from aieval.core.types import Score, EvalResult


class JSONSink(Sink):
    """Sink that outputs to JSON file."""
    
    def __init__(self, path: str | Path):
        """
        Initialize JSON sink.
        
        Args:
            path: Path to JSON file
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.runs: list[dict] = []
    
    def emit(self, score: Score) -> None:
        """No-op for individual scores (use emit_run instead)."""
        pass
    
    def emit_run(self, run: EvalResult) -> None:
        """Add run to buffer."""
        self.runs.append(run.to_dict())
    
    def flush(self) -> None:
        """Write runs to JSON file."""
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.runs, f, indent=2, default=str)
        
        print(f"Wrote {len(self.runs)} runs to {self.path}")
