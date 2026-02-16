"""Deployment gates for quality thresholds and regression detection."""

from typing import Any
import structlog

from aieval.core.types import EvalResult

logger = structlog.get_logger(__name__)


class DeploymentGate:
    """
    Deployment gate that checks quality thresholds and detects regressions.
    
    Can block deployment on failures.
    """
    
    def __init__(
        self,
        score_thresholds: dict[str, float] | None = None,
        max_regressions: int = 0,
        regression_threshold: float = 0.01,
    ):
        """
        Initialize deployment gate.
        
        Args:
            score_thresholds: Dictionary of score_name -> minimum_value
            max_regressions: Maximum number of regressions allowed (default: 0)
            regression_threshold: Threshold for regression detection (default: 0.01)
        """
        self.score_thresholds = score_thresholds or {}
        self.max_regressions = max_regressions
        self.regression_threshold = regression_threshold
        self.logger = structlog.get_logger(__name__)
    
    def check(
        self,
        run: EvalResult,
        baseline_run: EvalResult | None = None,
    ) -> dict[str, Any]:
        """
        Check if deployment should be allowed.
        
        Args:
            run: Current run to check
            baseline_run: Optional baseline run for comparison
            
        Returns:
            Dictionary with:
            - allowed: bool - Whether deployment is allowed
            - reasons: list[str] - Reasons for blocking (if any)
            - score_checks: dict - Score threshold checks
            - regression_checks: dict - Regression checks (if baseline provided)
        """
        reasons = []
        score_checks = {}
        regression_checks = {}
        
        # Check score thresholds
        for score_name, threshold in self.score_thresholds.items():
            score_value = self._get_score_value(run, score_name)
            if score_value is None:
                score_checks[score_name] = {
                    "passed": False,
                    "reason": f"Score '{score_name}' not found",
                }
                reasons.append(f"Score '{score_name}' not found")
            elif score_value < threshold:
                score_checks[score_name] = {
                    "passed": False,
                    "value": score_value,
                    "threshold": threshold,
                    "reason": f"Score {score_value:.4f} below threshold {threshold:.4f}",
                }
                reasons.append(f"Score '{score_name}' ({score_value:.4f}) below threshold ({threshold:.4f})")
            else:
                score_checks[score_name] = {
                    "passed": True,
                    "value": score_value,
                    "threshold": threshold,
                }
        
        # Check regressions if baseline provided
        if baseline_run:
            from aieval.core.eval import Eval
            eval_ = Eval(name="gate_check", dataset=[], scorers=[])
            comparison = eval_.compare(baseline_run, run)
            
            regressions = comparison.get("regressions", [])
            regression_count = len(regressions)
            
            regression_checks = {
                "baseline_run_id": baseline_run.run_id,
                "regressions": regressions,
                "regression_count": regression_count,
                "max_allowed": self.max_regressions,
            }
            
            if regression_count > self.max_regressions:
                reasons.append(
                    f"Too many regressions: {regression_count} (max allowed: {self.max_regressions})"
                )
        
        allowed = len(reasons) == 0
        
        result = {
            "allowed": allowed,
            "reasons": reasons,
            "score_checks": score_checks,
        }
        
        if regression_checks:
            result["regression_checks"] = regression_checks
        
        return result
    
    def _get_score_value(self, run: EvalResult, score_name: str) -> float | None:
        """Get score value from run."""
        for score in run.scores:
            if score.name == score_name:
                value = score.value
                if isinstance(value, bool):
                    return 1.0 if value else 0.0
                elif isinstance(value, (int, float)):
                    return float(value)
        return None
    
    def generate_report(self, check_result: dict[str, Any]) -> str:
        """
        Generate human-readable report from check result.
        
        Args:
            check_result: Result from check() method
            
        Returns:
            Human-readable report string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("DEPLOYMENT GATE REPORT")
        lines.append("=" * 60)
        lines.append("")
        
        if check_result["allowed"]:
            lines.append("✅ DEPLOYMENT ALLOWED")
        else:
            lines.append("❌ DEPLOYMENT BLOCKED")
        
        lines.append("")
        
        if check_result["reasons"]:
            lines.append("Reasons:")
            for reason in check_result["reasons"]:
                lines.append(f"  - {reason}")
            lines.append("")
        
        # Score checks
        if check_result["score_checks"]:
            lines.append("Score Thresholds:")
            for score_name, check in check_result["score_checks"].items():
                status = "✅" if check["passed"] else "❌"
                if check["passed"]:
                    lines.append(f"  {status} {score_name}: {check['value']:.4f} >= {check['threshold']:.4f}")
                else:
                    lines.append(f"  {status} {score_name}: {check.get('reason', 'Failed')}")
            lines.append("")
        
        # Regression checks
        if "regression_checks" in check_result:
            reg_checks = check_result["regression_checks"]
            lines.append("Regression Checks:")
            lines.append(f"  Baseline: {reg_checks['baseline_run_id']}")
            lines.append(f"  Regressions: {reg_checks['regression_count']} (max allowed: {reg_checks['max_allowed']})")
            if reg_checks["regressions"]:
                lines.append("  Regression details:")
                for reg in reg_checks["regressions"]:
                    lines.append(f"    - {reg}")
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
