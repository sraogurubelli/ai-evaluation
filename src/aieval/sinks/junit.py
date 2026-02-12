"""JUnit XML sink for CI test result publishing.

Writes a JUnit-style XML file so CI (Jenkins, GitLab, GitHub Actions) can
publish test results. One testcase per dataset item (test_id); success/failure
derived from scores.
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from aieval.sinks.base import Sink
from aieval.core.types import Score, Run

logger = logging.getLogger(__name__)


def _escape(s: str) -> str:
    """Escape for XML text content."""
    if not s:
        return ""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _scores_by_test_id(run: Run) -> dict[str, list[Score]]:
    """Group scores by test_id from metadata."""
    by_id: dict[str, list[Score]] = {}
    for score in run.scores:
        test_id = score.metadata.get("test_id") or "unknown"
        by_id.setdefault(test_id, []).append(score)
    return by_id


def _test_passed(scores: list[Score]) -> tuple[bool, str]:
    """Return (passed, message). Failed if generation_error or any score is 0/False."""
    for s in scores:
        if s.name == "generation_error" and s.value is False:
            return False, s.comment or "Generation error"
        if s.name == "generation_error":
            continue
        val = s.value
        if val is False or (isinstance(val, (int, float)) and val == 0.0):
            return False, s.comment or f"{s.name}={val}"
    return True, ""


class JUnitSink(Sink):
    """Sink that writes JUnit-style XML for CI test results."""

    def __init__(self, path: str | Path, testsuite_name: str = "aieval"):
        """
        Initialize JUnit sink.

        Args:
            path: Path to output XML file (e.g. results/junit.xml).
            testsuite_name: Name for the testsuite element (default: aieval).
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.testsuite_name = testsuite_name
        self._runs: list[ExperimentRun] = []

    def emit(self, score: Score) -> None:
        """No-op for individual scores (use emit_run instead)."""
        pass

    def emit_run(self, run: Run) -> None:
        """Buffer run for flush."""
        self._runs.append(run)

    def flush(self) -> None:
        """Write JUnit XML to path. Last run only (or combine if multiple)."""
        if not self._runs:
            logger.warning(f"No runs to write to {self.path}")
            return
        # Use last run for single-run usage; could merge multiple runs into one suite
        run = self._runs[-1]
        by_test = _scores_by_test_id(run)
        tests = len(by_test)
        failures = sum(1 for scores in by_test.values() if not _test_passed(scores)[0])
        suite = ET.Element(
            "testsuite",
            name=self.testsuite_name,
            tests=str(tests),
            failures=str(failures),
            errors="0",
            time="0",
        )
        for test_id, scores in sorted(by_test.items()):
            passed, msg = _test_passed(scores)
            case = ET.SubElement(suite, "testcase", name=_escape(test_id), classname=self.testsuite_name)
            if not passed:
                ET.SubElement(case, "failure", message=_escape(msg[:200])).text = _escape(msg)
        tree = ET.ElementTree(ET.Element("testsuites"))
        tree.getroot().append(suite)
        ET.indent(tree, space="  ")
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
            tree.getroot(), encoding="unicode", method="xml"
        )
        self.path.write_text(xml_str, encoding="utf-8")
        logger.info(f"Wrote JUnit XML to {self.path} ({tests} tests, {failures} failures)")
        self._runs.clear()

