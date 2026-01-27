"""Example usage of the AI Evolution Platform API."""

import requests
import time
import json

BASE_URL = "http://localhost:8000"


def create_experiment(config_path: str, run_async: bool = True):
    """Create an experiment via API."""
    # Load config
    with open(config_path, "r") as f:
        import yaml
        config = yaml.safe_load(f)
    
    # Create experiment request
    request_data = {
        "experiment_name": config["experiment"]["name"],
        "config": config,
        "run_async": run_async,
    }
    
    # Send request
    response = requests.post(
        f"{BASE_URL}/experiments",
        json=request_data,
    )
    response.raise_for_status()
    
    return response.json()


def get_task_status(task_id: str):
    """Get task status."""
    response = requests.get(f"{BASE_URL}/tasks/{task_id}")
    response.raise_for_status()
    return response.json()


def get_task_result(task_id: str):
    """Get task result."""
    response = requests.get(f"{BASE_URL}/tasks/{task_id}/result")
    response.raise_for_status()
    return response.json()


def wait_for_completion(task_id: str, timeout: int = 3600):
    """Wait for task to complete."""
    start_time = time.time()
    
    while True:
        task = get_task_status(task_id)
        status = task["status"]
        
        if status == "completed":
            return task
        elif status == "failed":
            raise RuntimeError(f"Task failed: {task.get('error')}")
        elif status == "cancelled":
            raise RuntimeError("Task was cancelled")
        
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
        
        time.sleep(2)  # Poll every 2 seconds


def main():
    """Example: Create and monitor an experiment."""
    print("Creating experiment...")
    
    # Create experiment
    task = create_experiment(
        "examples/ml_infra/config.yaml",
        run_async=True,
    )
    
    task_id = task["id"]
    print(f"Created task: {task_id}")
    print(f"Status: {task['status']}")
    
    # Wait for completion
    print("\nWaiting for task to complete...")
    try:
        completed_task = wait_for_completion(task_id)
        print(f"Task completed!")
        
        # Get result
        result = get_task_result(task_id)
        print(f"\nExecution time: {result['execution_time_seconds']:.2f}s")
        print(f"Scores: {len(result['experiment_run']['scores'])}")
        
        # Print score summary
        score_groups = {}
        for score in result['experiment_run']['scores']:
            name = score['name']
            if name not in score_groups:
                score_groups[name] = []
            score_groups[name].append(score['value'])
        
        print("\nScore Summary:")
        for name, values in score_groups.items():
            avg = sum(v for v in values if isinstance(v, (int, float))) / len(values)
            print(f"  {name}: {avg:.3f} (n={len(values)})")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
