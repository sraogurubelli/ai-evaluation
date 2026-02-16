"""Langfuse sink for observability integration."""

from typing import Any

from aieval.sinks.base import Sink
from aieval.core.types import Score, EvalResult


class LangfuseSink(Sink):
    """Sink that sends scores to Langfuse."""
    
    def __init__(
        self,
        secret_key: str | None = None,
        public_key: str | None = None,
        host: str | None = None,
        project: str = "ai-evolution",
    ):
        """
        Initialize Langfuse sink.
        
        Args:
            secret_key: Langfuse secret key (from env if not provided)
            public_key: Langfuse public key (from env if not provided)
            host: Langfuse host URL (from env if not provided)
            project: Langfuse project name
        """
        try:
            from langfuse import Langfuse
            import os
            
            self.client = Langfuse(
                secret_key=secret_key or os.getenv("LANGFUSE_SECRET_KEY", ""),
                public_key=public_key or os.getenv("LANGFUSE_PUBLIC_KEY", ""),
                host=host or os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
            )
            self.project = project
        except ImportError:
            self.client = None
            print("Warning: langfuse not installed. LangfuseSink will be disabled.")
    
    def emit(self, score: Score) -> None:
        """Send score to Langfuse."""
        if self.client is None:
            return
        
        try:
            self.client.score(
                name=score.name,
                value=score.value,
                trace_id=score.trace_id,
                observation_id=score.observation_id,
                comment=score.comment,
                metadata=score.metadata,
            )
        except Exception as e:
            print(f"Warning: Failed to send score to Langfuse: {e}")
    
    def emit_run(self, run: EvalResult) -> None:
        """Send all scores from run to Langfuse."""
        for score in run.scores:
            self.emit(score)
    
    def flush(self) -> None:
        """Flush Langfuse client."""
        if self.client:
            try:
                self.client.flush()
            except Exception as e:
                print(f"Warning: Failed to flush Langfuse: {e}")
