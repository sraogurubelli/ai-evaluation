"""Temporal worker for executing workflows and activities."""

import asyncio
import logging
import os
import signal
from temporalio.client import Client
from temporalio.worker import Worker

from ai_evolution.workflows.activities import (
    load_dataset_activity,
    run_experiment_activity,
    score_item_activity,
    emit_results_activity,
)
from ai_evolution.workflows.workflows import (
    ExperimentWorkflow,
    MultiModelWorkflow,
)

logger = logging.getLogger(__name__)

# Temporal configuration
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
TEMPORAL_TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "ai-evolution")


async def run_worker():
    """Run Temporal worker."""
    logger.info(f"Connecting to Temporal at {TEMPORAL_HOST}")
    
    client = await Client.connect(
        target_host=TEMPORAL_HOST,
        namespace=TEMPORAL_NAMESPACE,
    )
    
    logger.info(f"Starting worker on task queue: {TEMPORAL_TASK_QUEUE}")
    
    worker = Worker(
        client,
        task_queue=TEMPORAL_TASK_QUEUE,
        workflows=[ExperimentWorkflow, MultiModelWorkflow],
        activities=[
            load_dataset_activity,
            run_experiment_activity,
            score_item_activity,
            emit_results_activity,
        ],
    )
    
    logger.info("Worker started. Press Ctrl+C to stop.")
    
    # Handle shutdown gracefully
    shutdown_event = asyncio.Event()
    
    def signal_handler():
        logger.info("Shutdown signal received")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, lambda s, f: signal_handler())
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler())
    
    try:
        await asyncio.wait_for(worker.run(), timeout=None)
    except asyncio.CancelledError:
        logger.info("Worker cancelled")
    finally:
        logger.info("Worker stopped")


def main():
    """Main entry point for worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")


if __name__ == "__main__":
    main()
