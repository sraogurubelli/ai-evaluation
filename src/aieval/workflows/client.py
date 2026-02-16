"""Temporal client for starting and querying workflows."""

import os
import logging
from typing import Any

from temporalio.client import Client, WorkflowHandle

logger = logging.getLogger(__name__)

# Temporal configuration
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
TEMPORAL_TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "ai-evolution")


async def get_client() -> Client:
    """Get Temporal client."""
    return await Client.connect(
        target_host=TEMPORAL_HOST,
        namespace=TEMPORAL_NAMESPACE,
    )


async def start_eval_workflow(
    eval_name: str,
    config: dict[str, Any],
    workflow_id: str | None = None,
) -> str:
    """
    Start an eval workflow.

    Args:
        eval_name: Name of the eval
        config: Eval configuration
        workflow_id: Optional workflow ID (auto-generated if not provided)

    Returns:
        Workflow ID
    """
    client = await get_client()

    if not workflow_id:
        workflow_id = f"{eval_name}-{os.urandom(8).hex()}"

    handle = await client.start_workflow(
        "eval_workflow",
        args=[eval_name, config],
        id=workflow_id,
        task_queue=TEMPORAL_TASK_QUEUE,
    )

    logger.info(f"Started workflow: {handle.id}")
    return handle.id


async def get_workflow_status(workflow_id: str) -> dict[str, Any]:
    """
    Get workflow status.

    Args:
        workflow_id: Workflow ID

    Returns:
        Status dictionary
    """
    client = await get_client()
    handle = client.get_workflow_handle(workflow_id)

    description = await handle.describe()

    return {
        "workflow_id": workflow_id,
        "status": description.status.name,
        "run_id": description.run_id,
        "start_time": description.start_time.isoformat() if description.start_time else None,
        "close_time": description.close_time.isoformat() if description.close_time else None,
    }


async def get_workflow_result(workflow_id: str) -> dict[str, Any]:
    """
    Get workflow result (waits for completion if needed).

    Args:
        workflow_id: Workflow ID

    Returns:
        Workflow result
    """
    client = await get_client()
    handle = client.get_workflow_handle(workflow_id)

    result = await handle.result()
    return result
