"""HTML report sink for human-readable eval results.

Generates a single HTML file with summary (total/passed/failed) and a table
of test cases and scores. Open in a browser for Surefire-style viewing.
"""

import html
import logging
from pathlib import Path
from typing import Any

from aieval.sinks.base import Sink
from aieval.core.types import Score, EvalResult

logger = logging.getLogger(__name__)


def _scores_by_test_id(run: EvalResult) -> dict[str, list[Score]]:
    """Group scores by test_id from metadata."""
    by_id: dict[str, list[Score]] = {}
    for score in run.scores:
        test_id = score.metadata.get("test_id") or "unknown"
        by_id.setdefault(test_id, []).append(score)
    return by_id


def _test_passed(scores: list[Score]) -> bool:
    """True if no generation_error and no 0/False score."""
    for s in scores:
        if s.name == "generation_error" and s.value is False:
            return False
        if s.name == "generation_error":
            continue
        val = s.value
        if val is False or (isinstance(val, (int, float)) and val == 0.0):
            return False
    return True


def _scorer_names(run: EvalResult) -> list[str]:
    """Unique scorer names in order of first appearance."""
    seen: set[str] = set()
    names: list[str] = []
    for s in run.scores:
        if s.name not in seen:
            seen.add(s.name)
            names.append(s.name)
    return names


def render_run_to_html(run: EvalResult | dict[str, Any], title: str = "Evaluation Report") -> str:
    """
    Render a single run (Run or run dict from to_dict()) to HTML string.
    Used by API GET /runs/{run_id}/report.
    """
    if isinstance(run, dict):
        scores_raw = run.get("scores", [])
        run_id = run.get("run_id", "")
        eval_id = run.get("eval_id", "")
        metadata = run.get("metadata", {})
        created_at = run.get("created_at", "")
        # Normalize to list of score-like objects with .name, .value, .metadata
        class _Score:
            def __init__(self, d: dict):
                self.name = d.get("name", "")
                self.value = d.get("value", 0)
                self.metadata = d.get("metadata", {})
        scores = [_Score(s) for s in scores_raw]
        by_test: dict[str, list] = {}
        for s in scores:
            tid = s.metadata.get("test_id") or "unknown"
            by_test.setdefault(tid, []).append(s)
        scorer_names = list({s.name for s in scores})
        total = len(by_test) or 1
        passed = sum(1 for tidscores in by_test.values() if all(
            sc.value is True or (isinstance(sc.value, (int, float)) and float(sc.value) >= 0.99) for sc in tidscores
        ))
        failed = total - passed
        agent_id = metadata.get("agent_id", "")
        eval_name = metadata.get("name", eval_id)
    else:
        by_test = _scores_by_test_id(run)
        scorer_names = _scorer_names(run)
        total = len(by_test)
        passed = sum(1 for scores in by_test.values() if _test_passed(scores))
        failed = total - passed
        run_id = run.run_id
        eval_id = run.eval_id
        metadata = run.metadata or {}
        agent_id = metadata.get("agent_id", "")
        eval_name = metadata.get("name", run.eval_id)
        scores = run.scores

    rows_list: list[str] = []
    for test_id, tidscores in sorted(by_test.items()):
        score_map = {s.name: s for s in tidscores}
        ok = all(
            s.value is True or (isinstance(s.value, (int, float)) and float(s.value) >= 0.99)
            for s in tidscores
        )
        status_class = "pass" if ok else "fail"
        status_text = "PASS" if ok else "FAIL"
        cells = [f'<td class="{status_class}">{html.escape(status_text)}</td>', f"<td>{html.escape(test_id)}</td>"]
        for name in scorer_names:
            s = score_map.get(name)
            if s is None:
                cells.append("<td>-</td>")
            else:
                val = s.value
                val_str = "✓" if val is True else ("✗" if val is False else (f"{float(val):.3f}" if isinstance(val, (int, float)) else str(val)))
                cells.append(f"<td>{html.escape(val_str)}</td>")
        rows_list.append("<tr>" + "".join(cells) + "</tr>")
    scorer_headers = "".join(f"<th>{html.escape(n)}</th>" for n in scorer_names)
    table_body = "\n".join(rows_list)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(title)}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 1rem 2rem; }}
  h1 {{ margin-bottom: 0.25rem; }}
  .meta {{ color: #666; font-size: 0.9rem; margin-bottom: 1rem; }}
  .summary {{ display: flex; gap: 1.5rem; margin-bottom: 1.5rem; }}
  .summary span {{ font-weight: 600; }}
  .pass {{ color: #0a0; }}
  .fail {{ color: #c00; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ddd; padding: 0.4rem 0.75rem; text-align: left; }}
  th {{ background: #f5f5f5; }}
</style>
</head>
<body>
<h1>{html.escape(title)}</h1>
<div class="meta">Run: {html.escape(run_id)} | Eval: {html.escape(eval_name)} | Agent: {html.escape(agent_id or "-")}</div>
<div class="summary">
  <span>Total: {total}</span>
  <span class="pass">Passed: {passed}</span>
  <span class="fail">Failed: {failed}</span>
</div>
<table>
<thead><tr><th>Status</th><th>Test ID</th>{scorer_headers}</tr></thead>
<tbody>
{table_body}
</tbody>
</table>
</body>
</html>
"""


class HTMLReportSink(Sink):
    """Sink that writes a single HTML report file."""

    def __init__(self, path: str | Path, title: str = "Evaluation Report"):
        """
        Initialize HTML report sink.

        Args:
            path: Path to output HTML file (e.g. results/report.html).
            title: Page title (default: Evaluation Report).
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.title = title
        self._runs: list[EvalResult] = []

    def emit(self, score: Score) -> None:
        """No-op for individual scores (use emit_run instead)."""
        pass

    def emit_run(self, run: EvalResult) -> None:
        """Buffer run for flush."""
        self._runs.append(run)

    def flush(self) -> None:
        """Write HTML report to path. Uses last run if multiple."""
        if not self._runs:
            logger.warning(f"No runs to write to {self.path}")
            return
        run = self._runs[-1]
        by_test = _scores_by_test_id(run)
        scorer_names = _scorer_names(run)
        total = len(by_test)
        passed = sum(1 for scores in by_test.values() if _test_passed(scores))
        failed = total - passed
        run_meta = run.metadata or {}
        agent_id = run_meta.get("agent_id", "")
        eval_name = run_meta.get("name", run.eval_id)
        experiment_name = eval_name  # For backward compatibility in HTML template

        rows: list[str] = []
        for test_id, scores in sorted(by_test.items()):
            score_map = {s.name: s for s in scores}
            ok = _test_passed(scores)
            status_class = "pass" if ok else "fail"
            status_text = "PASS" if ok else "FAIL"
            cells = [f'<td class="{status_class}">{html.escape(status_text)}</td>']
            cells.append(f"<td>{html.escape(test_id)}</td>")
            for name in scorer_names:
                s = score_map.get(name)
                if s is None:
                    cells.append("<td>-</td>")
                else:
                    val = s.value
                    if isinstance(val, bool):
                        val_str = "✓" if val else "✗"
                    else:
                        val_str = f"{float(val):.3f}" if isinstance(val, (int, float)) else str(val)
                    cells.append(f"<td>{html.escape(val_str)}</td>")
            rows.append("<tr>" + "".join(cells) + "</tr>")

        scorer_headers = "".join(f"<th>{html.escape(n)}</th>" for n in scorer_names)
        table_body = "\n".join(rows)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(self.title)}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 1rem 2rem; }}
  h1 {{ margin-bottom: 0.25rem; }}
  .meta {{ color: #666; font-size: 0.9rem; margin-bottom: 1rem; }}
  .summary {{ display: flex; gap: 1.5rem; margin-bottom: 1.5rem; }}
  .summary span {{ font-weight: 600; }}
  .pass {{ color: #0a0; }}
  .fail {{ color: #c00; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ddd; padding: 0.4rem 0.75rem; text-align: left; }}
  th {{ background: #f5f5f5; }}
</style>
</head>
<body>
<h1>{html.escape(self.title)}</h1>
<div class="meta">Run: {html.escape(run.run_id)} | Eval: {html.escape(eval_name)} | Agent: {html.escape(agent_id or "-")}</div>
<div class="summary">
  <span>Total: {total}</span>
  <span class="pass">Passed: {passed}</span>
  <span class="fail">Failed: {failed}</span>
</div>
<table>
<thead><tr><th>Status</th><th>Test ID</th>{scorer_headers}</tr></thead>
<tbody>
{table_body}
</tbody>
</table>
</body>
</html>
"""
        self.path.write_text(html_content, encoding="utf-8")
        logger.info(f"Wrote HTML report to {self.path} ({total} tests, {passed} passed, {failed} failed)")
        self._runs.clear()

