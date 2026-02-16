"""Database module for AI Evolution Platform."""

from aieval.db.session import get_session, get_engine, init_db
from aieval.db.models import Base, Task, Eval, EvalResult, Score
# Backward compatibility aliases
Experiment = Eval  # type: ignore[misc,assignment]

__all__ = [
    "get_session",
    "get_engine",
    "init_db",
    "Base",
    "Task",
    "Experiment",
    "EvalResult",
    "Score",
]
