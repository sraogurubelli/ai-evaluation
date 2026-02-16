"""Stdout sink for console output."""

from aieval.sinks.base import Sink
from aieval.core.types import Score, EvalResult


class StdoutSink(Sink):
    """Sink that outputs to stdout."""

    def emit(self, score: Score) -> None:
        """Print score to stdout."""
        print(f"Score: {score.name}={score.value} (eval_id={score.eval_id})")
        if score.comment:
            print(f"  Comment: {score.comment}")

    def emit_run(self, run: EvalResult) -> None:
        """Print run summary to stdout."""
        print(f"\nRun: {run.run_id}")
        print(f"  Eval: {run.eval_id}")
        print(f"  Scores: {len(run.scores)}")

        # Group scores by name
        score_groups: dict[str, list[float]] = {}
        for score in run.scores:
            if score.name not in score_groups:
                score_groups[score.name] = []
            val = score.value
            if isinstance(val, bool):
                val = float(val)
            score_groups[score.name].append(val)

        # Print summary
        for name, values in score_groups.items():
            avg = sum(values) / len(values) if values else 0.0
            print(f"  {name}: avg={avg:.3f} (n={len(values)})")

    def flush(self) -> None:
        """No-op for stdout."""
        pass
