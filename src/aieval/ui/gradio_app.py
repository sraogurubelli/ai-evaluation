"""Gradio UI for AI Evolution Platform.

This module provides a web-based UI for running evals, viewing results,
and managing evals.
"""

import os
import gradio as gr
import requests
import json
from typing import Any
from pathlib import Path


# API base URL (configurable via environment)
API_BASE_URL = os.getenv("AI_EVOLUTION_API_URL", "http://localhost:8000")


def run_eval(
    eval_name: str,
    dataset_type: str,
    dataset_path: str,
    adapter_type: str,
    adapter_base_url: str,
    adapter_auth_token: str,
    scorer_types: list[str],
    model: str,
    concurrency_limit: int,
) -> tuple[str, Any]:
    """Run an eval via API."""
    try:
        # Prepare eval config
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

        # Create eval
        response = requests.post(
            f"{API_BASE_URL}/evals",
            json={
                "eval_name": eval_name,
                "config": config,
                "run_async": True,
            },
            timeout=30,
        )

        if response.status_code == 201:
            task_data = response.json()
            task_id = task_data.get("id")

            return (
                f"✅ Eval '{eval_name}' started successfully!\n"
                f"Task ID: {task_id}\n"
                f"Status: {task_data.get('status')}",
                task_data,
            )
        else:
            error_msg = response.text
            return (
                f"❌ Error starting eval: {response.status_code}\n{error_msg}",
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


def list_evals() -> str:
    """List all evals."""
    try:
        response = requests.get(f"{API_BASE_URL}/tasks?status=completed", timeout=10)
        if response.status_code == 200:
            tasks = response.json()
            if not tasks:
                return "No completed evals found."

            result = "Completed Evals:\n\n"
            for task in tasks[:10]:  # Show first 10
                result += f"- {task.get('eval_name', 'Unknown')} ({task.get('status')})\n"
            return result
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"


def fetch_agents() -> tuple[list[dict[str, Any]], str]:
    """Call GET /agents and return (list of agent dicts, message)."""
    try:
        response = requests.get(f"{API_BASE_URL}/agents", timeout=10)
        if response.status_code != 200:
            return [], f"Error: {response.status_code} - {response.text}"
        agents = response.json()
        return agents, f"Found {len(agents)} agent(s)."
    except Exception as e:
        return [], f"Error: {str(e)}"


def fetch_agent_runs(
    agent_id: str, limit: int = 50, offset: int = 0
) -> tuple[list[dict[str, Any]], str]:
    """Call GET /agents/{agent_id}/runs and return (list of run summaries, message)."""
    if not agent_id:
        return [], "Select an agent first."
    try:
        response = requests.get(
            f"{API_BASE_URL}/agents/{agent_id}/runs",
            params={"limit": limit, "offset": offset},
            timeout=10,
        )
        if response.status_code != 200:
            return [], f"Error: {response.status_code} - {response.text}"
        runs = response.json()
        return runs, f"Found {len(runs)} run(s)."
    except Exception as e:
        return [], f"Error: {str(e)}"


def fetch_run_detail(run_id: str) -> tuple[str, str | None]:
    """Call GET /runs/{run_id} and return (summary text, report_url)."""
    if not run_id:
        return "Enter a run ID.", None
    try:
        response = requests.get(f"{API_BASE_URL}/runs/{run_id}", timeout=10)
        if response.status_code != 200:
            return f"Error: {response.status_code} - {response.text}", None
        run = response.json()
        meta = run.get("metadata", {})
        scores = run.get("scores", [])
        total = len(scores)
        passed = sum(
            1
            for s in scores
            if s.get("value") is True
            or (isinstance(s.get("value"), (int, float)) and float(s.get("value", 0)) >= 0.99)
        )
        failed = total - passed
        report_url = f"{API_BASE_URL}/runs/{run_id}/report"
        summary = (
            f"Run ID: {run.get('run_id')}\n"
            f"Eval: {run.get('eval_id')}\n"
            f"Agent: {meta.get('agent_id', '-')}\n"
            f"Total: {total} | Passed: {passed} | Failed: {failed}\n\n"
            f"View report: {report_url}"
        )
        return summary, report_url
    except Exception as e:
        return f"Error: {str(e)}", None


def create_ui():
    """Create Gradio UI."""
    with gr.Blocks(title="AI Evolution Platform") as demo:
        gr.Markdown("# AI Evolution Platform")
        gr.Markdown("Run experiments, view results, and manage evaluations.")

        with gr.Tabs():
            # Add playground tabs
            from aieval.ui.playground import (
                create_prompt_playground,
                create_scorer_playground,
                create_agent_debugging_playground,
            )

            with gr.TabItem("Prompt Playground"):
                prompt_playground = create_prompt_playground()

            with gr.TabItem("Scorer Playground"):
                scorer_playground = create_scorer_playground()

            with gr.TabItem("Agent Debugging"):
                agent_playground = create_agent_debugging_playground()

            with gr.TabItem("Run Eval"):
                with gr.Row():
                    with gr.Column():
                        eval_name = gr.Textbox(
                            label="Eval Name",
                            placeholder="my_eval",
                            value="test_eval",
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

                        run_button = gr.Button("Run Eval", variant="primary")

                    with gr.Column():
                        output_text = gr.Textbox(
                            label="Output",
                            lines=10,
                            interactive=False,
                        )

                        output_json = gr.JSON(label="Task Details")

                run_button.click(
                    fn=run_eval,
                    inputs=[
                        eval_name,
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
                gr.Markdown("## Eval Results")

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

                list_button = gr.Button("List Evals")
                list_output = gr.Textbox(label="Evals", lines=10)

                list_button.click(
                    fn=list_evals,
                    inputs=[],
                    outputs=[list_output],
                )

            with gr.TabItem("By Agent"):
                gr.Markdown("## Runs by Agent")
                gr.Markdown("List agents that have runs, then view runs and report for each agent.")

                load_agents_btn = gr.Button("Load Agents", variant="primary")
                agents_msg = gr.Textbox(label="Agents", lines=2, interactive=False)
                agents_dropdown = gr.Dropdown(
                    choices=[],
                    label="Select Agent",
                    value=None,
                )

                def on_load_agents():
                    agents, msg = fetch_agents()
                    if not agents:
                        return msg, gr.Dropdown(choices=[], value=None)
                    choices = [
                        f"{a.get('agent_id', '')} ({a.get('agent_name') or '—'}) — {a.get('run_count', 0)} runs"
                        for a in agents
                    ]
                    values = [a.get("agent_id", "") for a in agents]
                    options = list(zip(choices, values))
                    first_val = values[0] if values else None
                    return msg, gr.Dropdown(choices=options, value=first_val)

                load_agents_btn.click(
                    fn=on_load_agents,
                    inputs=[],
                    outputs=[agents_msg, agents_dropdown],
                )

                load_runs_btn = gr.Button("Load Runs for Agent")
                runs_json = gr.JSON(label="Runs (run_id, created_at, model, total, passed, failed)")
                runs_msg = gr.Textbox(label="Runs", lines=2, interactive=False)

                def on_load_runs(agent_id: str):
                    if not agent_id:
                        return [], "Select an agent first."
                    runs, msg = fetch_agent_runs(agent_id)
                    return runs, msg

                load_runs_btn.click(
                    fn=on_load_runs,
                    inputs=[agents_dropdown],
                    outputs=[runs_json, runs_msg],
                )

                gr.Markdown("### View Run Detail")
                run_id_input = gr.Textbox(
                    label="Run ID", placeholder="Paste run_id from table above"
                )
                view_run_btn = gr.Button("View Run")
                run_summary_output = gr.Textbox(label="Run Summary", lines=8, interactive=False)
                report_url_output = gr.Textbox(label="Report URL", lines=1, interactive=False)

                def on_view_run(run_id: str):
                    summary, report_url = fetch_run_detail(run_id)
                    return summary, report_url or ""

                view_run_btn.click(
                    fn=on_view_run,
                    inputs=[run_id_input],
                    outputs=[run_summary_output, report_url_output],
                )

        gr.Markdown("---")
        gr.Markdown(f"API Base URL: {API_BASE_URL}")

    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860)
