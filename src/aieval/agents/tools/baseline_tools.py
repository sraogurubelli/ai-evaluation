"""Baseline-related tools."""

from typing import Any
from pathlib import Path
import json
import os

from aieval.agents.tools.base import Tool, ToolResult


class BaselineManager:
    """Simple baseline manager for storing eval_id -> run_id mappings."""

    def __init__(self, storage_path: str | Path | None = None):
        """
        Initialize baseline manager.

        Args:
            storage_path: Path to JSON file for storing baselines.
                         If None, uses ~/.aieval/baselines.json
        """
        if storage_path is None:
            storage_path = Path.home() / ".aieval" / "baselines.json"
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._baselines: dict[str, str] = {}  # eval_id -> run_id
        self._load_baselines()

    def _load_baselines(self) -> None:
        """Load baselines from storage file."""
        if self.storage_path.exists():
            try:
                with self.storage_path.open("r") as f:
                    self._baselines = json.load(f)
            except Exception:
                self._baselines = {}

    def _save_baselines(self) -> None:
        """Save baselines to storage file."""
        try:
            with self.storage_path.open("w") as f:
                json.dump(self._baselines, f, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to save baselines: {e}")

    def set_baseline(self, eval_id: str, run_id: str) -> None:
        """Set baseline run for an eval."""
        if not eval_id or not isinstance(eval_id, str):
            raise ValueError("eval_id must be a non-empty string")
        if not run_id or not isinstance(run_id, str):
            raise ValueError("run_id must be a non-empty string")

        self._baselines[eval_id] = run_id
        self._save_baselines()

    def get_baseline(self, eval_id: str) -> str | None:
        """Get baseline run ID for an eval."""
        if not eval_id or not isinstance(eval_id, str):
            raise ValueError("eval_id must be a non-empty string")
        return self._baselines.get(eval_id)

    def unset_baseline(self, eval_id: str) -> None:
        """Unset baseline for an eval."""
        if eval_id in self._baselines:
            del self._baselines[eval_id]
            self._save_baselines()


# Global baseline manager instance
_baseline_manager: BaselineManager | None = None


def get_baseline_manager(storage_path: str | Path | None = None) -> BaselineManager:
    """Get singleton baseline manager."""
    global _baseline_manager
    if _baseline_manager is None:
        _baseline_manager = BaselineManager(storage_path)
    return _baseline_manager


class SetBaselineTool(Tool):
    """Tool for setting baseline runs."""

    def __init__(self):
        super().__init__(
            name="set_baseline",
            description="Set a run as baseline for an eval",
            parameters_schema={
                "type": "object",
                "properties": {
                    "eval_id": {
                        "type": "string",
                        "description": "Evaluation ID",
                    },
                    "run_id": {
                        "type": "string",
                        "description": "Run ID to set as baseline",
                    },
                    "storage_path": {
                        "type": "string",
                        "description": "Optional path to baseline storage file",
                    },
                },
                "required": ["eval_id", "run_id"],
            },
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute baseline setting."""
        try:
            self.validate_parameters(**kwargs)

            eval_id = kwargs["eval_id"]
            run_id = kwargs["run_id"]
            storage_path = kwargs.get("storage_path")

            manager = get_baseline_manager(storage_path)
            manager.set_baseline(eval_id, run_id)

            return ToolResult(
                success=True,
                data={
                    "eval_id": eval_id,
                    "run_id": run_id,
                },
                metadata={"action": "set_baseline"},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )


class GetBaselineTool(Tool):
    """Tool for getting baseline run IDs."""

    def __init__(self):
        super().__init__(
            name="get_baseline",
            description="Get baseline run ID for an eval",
            parameters_schema={
                "type": "object",
                "properties": {
                    "eval_id": {
                        "type": "string",
                        "description": "Evaluation ID",
                    },
                    "storage_path": {
                        "type": "string",
                        "description": "Optional path to baseline storage file",
                    },
                },
                "required": ["eval_id"],
            },
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute baseline retrieval."""
        try:
            self.validate_parameters(**kwargs)

            eval_id = kwargs["eval_id"]
            storage_path = kwargs.get("storage_path")

            manager = get_baseline_manager(storage_path)
            run_id = manager.get_baseline(eval_id)

            if run_id is None:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"No baseline set for eval_id: {eval_id}",
                )

            return ToolResult(
                success=True,
                data={
                    "eval_id": eval_id,
                    "run_id": run_id,
                },
                metadata={"action": "get_baseline"},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )
