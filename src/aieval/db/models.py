"""SQLAlchemy database models."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

from aieval.tasks.models import TaskStatus

# Base class for all models
Base = declarative_base()


class Task(Base):
    """Task model for eval execution."""

    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    eval_name = Column(String(255), nullable=False, index=True)
    config = Column(JSON, nullable=False)
    status = Column(
        SQLEnum(TaskStatus, name="task_status", create_constraint=True),
        nullable=False,
        default=TaskStatus.PENDING,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    meta = Column("meta_data", JSON, nullable=True, default=dict)

    # Relationships
    result = relationship(
        "TaskResult", back_populates="task", uselist=False, cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "eval_name": self.eval_name,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "metadata": self.meta or {},
        }


class TaskResult(Base):
    """Task result model."""

    __tablename__ = "task_results"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(
        UUID(as_uuid=False), ForeignKey("tasks.id"), nullable=False, unique=True, index=True
    )
    run_id = Column(
        UUID(as_uuid=False), ForeignKey("runs.id"), nullable=True, index=True
    )  # Migrated from experiment_run_id
    execution_time_seconds = Column(Float, nullable=False)
    meta = Column("meta_data", JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="result")
    eval_result = relationship("EvalResult", back_populates="task_results")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": str(self.task_id),
            "run": self.eval_result.to_dict() if self.eval_result else None,
            "execution_time_seconds": self.execution_time_seconds,
            "metadata": self.meta or {},
        }


class Eval(Base):
    """Eval model."""

    __tablename__ = "evals"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    dataset_config = Column(JSON, nullable=False)
    scorers_config = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta = Column("meta_data", JSON, nullable=True, default=dict)

    # Relationships
    runs = relationship("EvalResult", back_populates="eval", cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "dataset_config": self.dataset_config,
            "scorers_config": self.scorers_config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.meta or {},
        }


class EvalResult(Base):
    """EvalResult model."""

    __tablename__ = "runs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    eval_id = Column(UUID(as_uuid=False), ForeignKey("evals.id"), nullable=False, index=True)
    run_id = Column(String(255), nullable=False, unique=True, index=True)
    dataset_id = Column(String(255), nullable=False, index=True)
    model = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    meta = Column("meta_data", JSON, nullable=True, default=dict)

    # Relationships
    eval = relationship("Eval", back_populates="runs")
    scores = relationship("Score", back_populates="eval_result", cascade="all, delete-orphan")
    task_results = relationship("TaskResult", back_populates="eval_result")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "eval_id": str(self.eval_id),
            "run_id": self.run_id,
            "dataset_id": self.dataset_id,
            "scores": [score.to_dict() for score in self.scores],
            "metadata": self.meta or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Score(Base):
    """Score model for evaluation results."""

    __tablename__ = "scores"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(
        UUID(as_uuid=False), ForeignKey("runs.id"), nullable=False, index=True
    )  # Migrated from experiment_run_id
    name = Column(String(255), nullable=False, index=True)
    value = Column(Float, nullable=False)
    eval_id = Column(String(255), nullable=False, index=True)
    comment = Column(Text, nullable=True)
    meta = Column("meta_data", JSON, nullable=True, default=dict)
    trace_id = Column(String(255), nullable=True, index=True)
    observation_id = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    eval_result = relationship("EvalResult", back_populates="scores")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "eval_id": self.eval_id,
            "comment": self.comment,
            "metadata": self.meta or {},
            "trace_id": self.trace_id,
            "observation_id": self.observation_id,
        }


# Guardrail models


class GuardrailTask(Base):
    """Guardrail task model (use case/application)."""

    __tablename__ = "guardrail_tasks"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta = Column("meta_data", JSON, nullable=True, default=dict)

    # Relationships
    policies = relationship("GuardrailPolicy", back_populates="task", cascade="all, delete-orphan")
    inferences = relationship("Inference", back_populates="task", cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.meta or {},
        }


class GuardrailPolicy(Base):
    """Guardrail policy model (policy-as-code)."""

    __tablename__ = "guardrail_policies"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(
        UUID(as_uuid=False), ForeignKey("guardrail_tasks.id"), nullable=True, index=True
    )
    name = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=False, default="v1")
    description = Column(Text, nullable=True)
    policy_yaml = Column(Text, nullable=False)  # YAML/JSON policy configuration
    is_global = Column(
        Boolean, nullable=False, default=False, index=True
    )  # Global policies apply to all tasks
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta = Column("meta_data", JSON, nullable=True, default=dict)

    # Relationships
    task = relationship("GuardrailTask", back_populates="policies")
    rules = relationship("GuardrailRule", back_populates="policy", cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "task_id": str(self.task_id) if self.task_id else None,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "policy_yaml": self.policy_yaml,
            "is_global": self.is_global,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.meta or {},
        }


class GuardrailRule(Base):
    """Guardrail rule model (parsed from policy)."""

    __tablename__ = "guardrail_rules"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_id = Column(
        UUID(as_uuid=False), ForeignKey("guardrail_policies.id"), nullable=False, index=True
    )
    rule_id = Column(String(255), nullable=False, index=True)  # Rule ID from policy
    check_type = Column(
        String(100), nullable=False, index=True
    )  # hallucination, prompt_injection, etc.
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    threshold = Column(Float, nullable=False, default=0.5)
    action = Column(String(50), nullable=False, default="warn")  # block, warn, log
    config = Column(JSON, nullable=True, default=dict)  # Rule-specific configuration
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    policy = relationship("GuardrailPolicy", back_populates="rules")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "policy_id": str(self.policy_id),
            "rule_id": self.rule_id,
            "check_type": self.check_type,
            "enabled": self.enabled,
            "threshold": self.threshold,
            "action": self.action,
            "config": self.config or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Inference(Base):
    """Inference tracking model (all prompt/response pairs with validation)."""

    __tablename__ = "inferences"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(
        UUID(as_uuid=False), ForeignKey("guardrail_tasks.id"), nullable=True, index=True
    )
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    context = Column(Text, nullable=True)  # RAG context for hallucination checks
    model_name = Column(String(255), nullable=True, index=True)
    run_id = Column(
        UUID(as_uuid=False), ForeignKey("runs.id"), nullable=True, index=True
    )  # Migrated from experiment_run_id
    rule_results = Column(
        JSON, nullable=True, default=dict
    )  # Validation results from policy engine
    passed = Column(Boolean, nullable=False, default=True, index=True)
    blocked = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    meta = Column("meta_data", JSON, nullable=True, default=dict)

    # Relationships
    task = relationship("GuardrailTask", back_populates="inferences")
    eval_result = relationship("EvalResult", foreign_keys=[run_id])

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "task_id": str(self.task_id) if self.task_id else None,
            "prompt": self.prompt,
            "response": self.response,
            "context": self.context,
            "model_name": self.model_name,
            "run_id": str(self.run_id) if self.run_id else None,
            "rule_results": self.rule_results or {},
            "passed": self.passed,
            "blocked": self.blocked,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.meta or {},
        }
