"""Gradio UI for AI Evolution Platform.

This module provides a web-based UI for running experiments, viewing results,
and managing experiments.
"""

import gradio as gr
import requests
import json
from typing import Any
from pathlib import Path


# API base URL (configurable via environment)
API_BASE_URL = os.getenv("AI_EVOLUTION_API_URL", "http://localhost:8000")


def run_experiment(
    experiment_name: str,
    dataset_type: str,
    dataset_path: str,
    adapter_type: str,
    adapter_base_url: str,
    adapter_auth_token: str,
    scorer_types: list[str],
    model: str,
    concurrency_limit: int,
) -> tuple[str, Any]:
    """Run an experiment via API."""
    try:
        # Prepare experiment config
        config = {
            "dataset": {
                "type": dataset_type,
                "path": dataset_path,
            },
            "adapter": {
                "type": adapter_type,
                "base_url": adapter_base_url,
                "auth_token": adapter_auth_token,
            },
            "scorers": [{"type": scorer} for scorer in scorer_types],
            "models": [model],
            "execution": {
                "concurrency_limit": concurrency_limit,
            },
        }
        
        # Create experiment
        response = requests.post(
            f"{API_BASE_URL}/experiments",
            json={
                "experiment_name": experiment_name,
                "config": config,
                "run_async": True,
            },
            timeout=30,
        )
        
        if response.status_code == 201:
            task_data = response.json()
            task_id = task_data.get("id")
            
            return (
                f"✅ Experiment '{experiment_name}' started successfully!\n"
                f"Task ID: {task_id}\n"
                f"Status: {task_data.get('status')}",
                task_data,
            )
        else:
            error_msg = response.text
            return (
                f"❌ Error starting experiment: {response.status_code}\n{error_msg}",
                None,
            )
    except Exception as e:
        return f"❌ Error: {str(e)}", None


def get_task_status(task_id: str) -> str:
    """Get task status."""
    try:
        response = requests.get(f"{API_BASE_URL}/tasks/{task_id}", timeout=10)
        if response.status_code == 200:
            task_data = response.json()
            status = task_data.get("status", "unknown")
            return f"Status: {status}"
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"


def list_experiments() -> str:
    """List all experiments."""
    try:
        response = requests.get(f"{API_BASE_URL}/tasks?status=completed", timeout=10)
        if response.status_code == 200:
            tasks = response.json()
            if not tasks:
                return "No completed experiments found."
            
            result = "Completed Experiments:\n\n"
            for task in tasks[:10]:  # Show first 10
                result += f"- {task.get('experiment_name', 'Unknown')} ({task.get('status')})\n"
            return result
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"


def create_ui():
    """Create Gradio UI."""
    with gr.Blocks(title="AI Evolution Platform") as demo:
        gr.Markdown("# AI Evolution Platform")
        gr.Markdown("Run experiments, view results, and manage evaluations.")
        
        with gr.Tabs():
            with gr.TabItem("Run Experiment"):
                with gr.Row():
                    with gr.Column():
                        experiment_name = gr.Textbox(
                            label="Experiment Name",
                            placeholder="my_experiment",
                            value="test_experiment",
                        )
                        
                        dataset_type = gr.Dropdown(
                            choices=["jsonl", "index_csv", "function"],
                            label="Dataset Type",
                            value="index_csv",
                        )
                        
                        dataset_path = gr.Textbox(
                            label="Dataset Path",
                            placeholder="benchmarks/datasets/index.csv",
                            value="benchmarks/datasets/index.csv",
                        )
                        
                        adapter_type = gr.Dropdown(
                            choices=["http"],  # Use http adapter with your API configuration
                            label="Adapter Type",
                            value="http",
                        )
                        
                        adapter_base_url = gr.Textbox(
                            label="Adapter Base URL",
                            placeholder="http://localhost:8000",
                            value="http://localhost:8000",
                        )
                        
                        adapter_auth_token = gr.Textbox(
                            label="Auth Token",
                            placeholder="your-token",
                            type="password",
                        )
                        
                        scorer_types = gr.CheckboxGroup(
                            choices=["deep_diff_v1", "deep_diff_v2", "deep_diff_v3"],
                            label="Scorers",
                            value=["deep_diff_v3"],
                        )
                        
                        model = gr.Textbox(
                            label="Model",
                            placeholder="claude-3-5-sonnet-20241022",
                            value="claude-3-5-sonnet-20241022",
                        )
                        
                        concurrency_limit = gr.Slider(
                            minimum=1,
                            maximum=10,
                            value=5,
                            label="Concurrency Limit",
                        )
                        
                        run_button = gr.Button("Run Experiment", variant="primary")
                    
                    with gr.Column():
                        output_text = gr.Textbox(
                            label="Output",
                            lines=10,
                            interactive=False,
                        )
                        
                        output_json = gr.JSON(label="Task Details")
                
                run_button.click(
                    fn=run_experiment,
                    inputs=[
                        experiment_name,
                        dataset_type,
                        dataset_path,
                        adapter_type,
                        adapter_base_url,
                        adapter_auth_token,
                        scorer_types,
                        model,
                        concurrency_limit,
                    ],
                    outputs=[output_text, output_json],
                )
            
            with gr.TabItem("View Results"):
                gr.Markdown("## Experiment Results")
                
                task_id_input = gr.Textbox(
                    label="Task ID",
                    placeholder="Enter task ID to check status",
                )
                
                status_button = gr.Button("Check Status")
                status_output = gr.Textbox(label="Status", lines=5)
                
                status_button.click(
                    fn=get_task_status,
                    inputs=[task_id_input],
                    outputs=[status_output],
                )
                
                list_button = gr.Button("List Experiments")
                list_output = gr.Textbox(label="Experiments", lines=10)
                
                list_button.click(
                    fn=list_experiments,
                    inputs=[],
                    outputs=[list_output],
                )
        
        gr.Markdown("---")
        gr.Markdown(f"API Base URL: {API_BASE_URL}")
    
    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860)
