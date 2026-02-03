"""Inference repository for tracking validations."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from aieval.db.models import Inference, GuardrailTask

logger = logging.getLogger(__name__)


class InferenceRepository:
    """Repository for inference tracking."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(
        self,
        prompt: str,
        response: str | None = None,
        context: str | None = None,
        task_id: str | None = None,
        model_name: str | None = None,
        experiment_run_id: str | None = None,
        rule_results: dict[str, Any] | None = None,
        passed: bool = True,
        blocked: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> Inference:
        """Create a new inference record."""
        inference = Inference(
            prompt=prompt,
            response=response,
            context=context,
            task_id=task_id,
            model_name=model_name,
            experiment_run_id=experiment_run_id,
            rule_results=rule_results or {},
            passed=passed,
            blocked=blocked,
            meta=metadata or {},
        )
        self.session.add(inference)
        await self.session.commit()
        await self.session.refresh(inference)
        return inference
    
    async def get_by_id(self, inference_id: str) -> Inference | None:
        """Get inference by ID."""
        result = await self.session.execute(
            select(Inference).where(Inference.id == inference_id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_task(
        self,
        task_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Inference]:
        """List inferences for a task."""
        result = await self.session.execute(
            select(Inference)
            .where(Inference.task_id == task_id)
            .order_by(Inference.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def list_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        task_id: str | None = None,
        model_name: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[Inference]:
        """List inferences by date range."""
        conditions = [
            Inference.created_at >= start_date,
            Inference.created_at <= end_date,
        ]
        
        if task_id:
            conditions.append(Inference.task_id == task_id)
        
        if model_name:
            conditions.append(Inference.model_name == model_name)
        
        result = await self.session.execute(
            select(Inference)
            .where(and_(*conditions))
            .order_by(Inference.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def get_statistics(
        self,
        task_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get aggregate statistics."""
        conditions = []
        
        if task_id:
            conditions.append(Inference.task_id == task_id)
        
        if start_date:
            conditions.append(Inference.created_at >= start_date)
        
        if end_date:
            conditions.append(Inference.created_at <= end_date)
        
        query = select(Inference)
        if conditions:
            query = query.where(and_(*conditions))
        
        # Total count
        total_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar() or 0
        
        # Passed count
        passed_result = await self.session.execute(
            select(func.count()).select_from(
                query.where(Inference.passed == True).subquery()
            )
        )
        passed = passed_result.scalar() or 0
        
        # Blocked count
        blocked_result = await self.session.execute(
            select(func.count()).select_from(
                query.where(Inference.blocked == True).subquery()
            )
        )
        blocked = blocked_result.scalar() or 0
        
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "blocked": blocked,
            "pass_rate": (passed / total * 100) if total > 0 else 0.0,
        }
