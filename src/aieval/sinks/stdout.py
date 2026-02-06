"""Stdout sink for console output."""

from aieval.sinks.base import Sink
from aieval.core.types import Score, ExperimentRun


class StdoutSink(Sink):
    """Sink that outputs to stdout."""
    
    def emit(self, score: Score) -> None:
        """Print score to stdout."""
        print(f"Score: {score.name}={score.value} (eval_id={score.eval_id})")
        if score.comment:
            print(f"  Comment: {score.comment}")
    
    def emit_run(self, run: ExperimentRun) -> None:
        """Print experiment run summary to stdout."""
        print(f"\nExperiment Run: {run.run_id}")
        print(f"  Experiment: {run.experiment_id}")
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
            # Filter out NaN, inf, -inf values
            valid_scores = [
                s for s in values 
                if not (isinstance(s, float) and (s != s or s == float('inf') or s == float('-inf')))
            ]
            
            if valid_scores:
                avg = sum(valid_scores) / len(valid_scores)
            else:
                avg = float('nan')
            
            nan_count = len(values) - len(valid_scores)
            if nan_count > 0:
                print(f"  {name}: avg={avg:.3f} (n={len(valid_scores)}, failed={nan_count})")
            else:
                print(f"  {name}: avg={avg:.3f} (n={len(values)})")
    
    def flush(self) -> None:
        """No-op for stdout."""
        pass
