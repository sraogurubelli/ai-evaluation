"""Rule agent for managing guardrail tasks and policies."""

import logging
from typing import Any
from uuid import uuid4

from aieval.agents.base import BaseEvaluationAgent
from aieval.policies.policy_engine import PolicyEngine
from aieval.policies.policy_loader import PolicyLoader
from aieval.policies.policy_validator import PolicyValidator
from aieval.policies.models import Policy, RuleConfig
from aieval.db.models import GuardrailTask, GuardrailPolicy, GuardrailRule
from aieval.db.session import get_session

logger = logging.getLogger(__name__)


class RuleAgent(BaseEvaluationAgent):
    """Agent for managing guardrail tasks and policies."""
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize rule agent."""
        super().__init__(config)
        self.policy_engine = PolicyEngine()
        self.policy_loader = PolicyLoader()
        self.policy_validator = PolicyValidator()
    
    async def run(self, query: str, **kwargs: Any) -> Any:
        """
        Run rule operation based on query.
        
        Supported queries:
        - "create_task": Create a guardrail task
        - "get_task": Get a task by ID
        - "list_tasks": List all tasks
        - "create_policy": Create a policy
        - "load_policy": Load policy from file/string
        - "get_policy": Get policy by name
        - "list_policies": List all policies
        - "validate_policy": Validate policy configuration
        
        Args:
            query: Operation to perform
            **kwargs: Operation-specific parameters
            
        Returns:
            Operation result
        """
        if query == "create_task":
            return await self.create_task(**kwargs)
        elif query == "get_task":
            return await self.get_task(**kwargs)
        elif query == "list_tasks":
            return await self.list_tasks(**kwargs)
        elif query == "create_policy":
            return await self.create_policy(**kwargs)
        elif query == "load_policy":
            return await self.load_policy(**kwargs)
        elif query == "get_policy":
            return await self.get_policy(**kwargs)
        elif query == "list_policies":
            return await self.list_policies(**kwargs)
        elif query == "validate_policy":
            return await self.validate_policy(**kwargs)
        else:
            raise ValueError(f"Unknown query: {query}")
    
    async def create_task(
        self,
        name: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GuardrailTask:
        """Create a guardrail task."""
        try:
            async for session in get_session():
                task = GuardrailTask(
                    id=str(uuid4()),
                    name=name,
                    description=description,
                    meta=metadata or {},
                )
                session.add(task)
                await session.commit()
                await session.refresh(task)
                return task
        except Exception as e:
            logger.error(f"Failed to create task: {e}", exc_info=True)
            raise
    
    async def get_task(self, task_id: str) -> GuardrailTask | None:
        """Get task by ID."""
        try:
            from sqlalchemy import select
            
            async for session in get_session():
                result = await session.execute(
                    select(GuardrailTask).where(GuardrailTask.id == task_id)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get task: {e}", exc_info=True)
            raise
    
    async def list_tasks(self) -> list[GuardrailTask]:
        """List all tasks."""
        try:
            from sqlalchemy import select
            
            async for session in get_session():
                result = await session.execute(
                    select(GuardrailTask).order_by(GuardrailTask.created_at.desc())
                )
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}", exc_info=True)
            raise
    
    async def create_policy(
        self,
        name: str,
        policy_yaml: str,
        task_id: str | None = None,
        version: str = "v1",
        description: str | None = None,
        is_global: bool = False,
        enabled: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> GuardrailPolicy:
        """Create a policy from YAML."""
        # Load and validate policy
        policy = self.policy_loader.load_from_string(policy_yaml, format="yaml")
        is_valid, errors = self.policy_validator.validate(policy)
        
        if not is_valid:
            raise ValueError(f"Policy validation failed: {', '.join(errors)}")
        
        try:
            async for session in get_session():
                # Create policy record
                policy_record = GuardrailPolicy(
                    id=str(uuid4()),
                    task_id=task_id,
                    name=name,
                    version=version,
                    description=description or policy.description,
                    policy_yaml=policy_yaml,
                    is_global=is_global,
                    enabled=enabled,
                    meta=metadata or {},
                )
                session.add(policy_record)
                
                # Create rule records
                for rule in policy.rules:
                    rule_record = GuardrailRule(
                        id=str(uuid4()),
                        policy_id=policy_record.id,
                        rule_id=rule.id,
                        check_type=rule.type,
                        enabled=rule.enabled,
                        threshold=rule.threshold,
                        action=rule.action,
                        config=rule.config,
                    )
                    session.add(rule_record)
                
                await session.commit()
                await session.refresh(policy_record)
                
                # Load into policy engine
                self.policy_engine.load_policy(policy, name=name)
                
                return policy_record
        except Exception as e:
            logger.error(f"Failed to create policy: {e}", exc_info=True)
            raise
    
    async def load_policy(
        self,
        file_path: str | None = None,
        policy_yaml: str | None = None,
        name: str | None = None,
    ) -> Policy:
        """Load policy from file or string."""
        if file_path:
            policy = self.policy_loader.load_from_file(file_path)
        elif policy_yaml:
            policy = self.policy_loader.load_from_string(policy_yaml, format="yaml")
        else:
            raise ValueError("Either file_path or policy_yaml must be provided")
        
        # Load into policy engine
        policy_name = name or policy.name
        self.policy_engine.load_policy(policy, name=policy_name)
        
        return policy
    
    async def get_policy(self, name: str) -> Policy | None:
        """Get policy by name from engine."""
        return self.policy_engine.get_policy(name)
    
    async def list_policies(self) -> list[dict[str, Any]]:
        """List all policies."""
        return [
            {
                "name": name,
                "version": policy.version,
                "description": policy.description,
                "rule_count": len(policy.rules),
            }
            for name, policy in self.policy_engine.policies.items()
        ]
    
    async def validate_policy(
        self,
        policy_yaml: str | None = None,
        policy: Policy | None = None,
    ) -> dict[str, Any]:
        """Validate policy configuration."""
        if policy is None:
            if policy_yaml is None:
                raise ValueError("Either policy or policy_yaml must be provided")
            policy = self.policy_loader.load_from_string(policy_yaml, format="yaml")
        
        is_valid, errors = self.policy_validator.validate(policy)
        
        return {
            "valid": is_valid,
            "errors": errors,
            "rule_count": len(policy.rules),
            "enabled_rule_count": len(policy.get_enabled_rules()),
        }
