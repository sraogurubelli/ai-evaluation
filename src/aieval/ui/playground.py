"""Playground components for prompt and scorer testing."""

import gradio as gr
from typing import Any


def create_prompt_playground():
    """Create prompt testing playground."""
    with gr.Blocks(title="Prompt Playground") as playground:
        gr.Markdown("## Prompt Testing Playground")
        gr.Markdown("Test prompts with different models and compare outputs side-by-side.")
        
        with gr.Row():
            with gr.Column():
                prompt_input = gr.Textbox(
                    label="Prompt",
                    placeholder="Enter your prompt here...",
                    lines=5,
                )
                
                model1 = gr.Dropdown(
                    choices=["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
                    label="Model 1",
                    value="gpt-4o-mini",
                )
                
                model2 = gr.Dropdown(
                    choices=["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
                    label="Model 2",
                    value="claude-3-5-sonnet-20241022",
                )
                
                test_button = gr.Button("Test Prompts", variant="primary")
            
            with gr.Column():
                output1 = gr.Textbox(
                    label="Output 1",
                    lines=10,
                    interactive=False,
                )
                
                output2 = gr.Textbox(
                    label="Output 2",
                    lines=10,
                    interactive=False,
                )
        
        def test_prompts(prompt: str, m1: str, m2: str):
            """Test prompts with two models."""
            # This would call the adapter/LLM
            # Placeholder implementation
            return f"[Model 1 ({m1}) output for: {prompt[:50]}...]", f"[Model 2 ({m2}) output for: {prompt[:50]}...]"
        
        test_button.click(
            fn=test_prompts,
            inputs=[prompt_input, model1, model2],
            outputs=[output1, output2],
        )
    
    return playground


def create_scorer_playground():
    """Create scorer testing playground."""
    with gr.Blocks(title="Scorer Playground") as playground:
        gr.Markdown("## Scorer Testing Playground")
        gr.Markdown("Test scorers on sample outputs and visualize scores.")
        
        with gr.Row():
            with gr.Column():
                generated_output = gr.Textbox(
                    label="Generated Output",
                    placeholder="Enter generated output...",
                    lines=5,
                )
                
                expected_output = gr.Textbox(
                    label="Expected Output",
                    placeholder="Enter expected output (optional)...",
                    lines=5,
                )
                
                scorer_type = gr.Dropdown(
                    choices=["deep_diff", "schema_validation", "llm_judge", "hallucination", "helpfulness"],
                    label="Scorer Type",
                    value="deep_diff",
                )
                
                test_scorer_button = gr.Button("Test Scorer", variant="primary")
            
            with gr.Column():
                score_output = gr.Textbox(
                    label="Score Result",
                    lines=10,
                    interactive=False,
                )
                
                score_visualization = gr.JSON(
                    label="Score Details",
                )
        
        def test_scorer(generated: str, expected: str, scorer: str):
            """Test scorer on outputs."""
            # This would call the scorer
            # Placeholder implementation
            return f"Score: 0.85\nScorer: {scorer}", {"score": 0.85, "scorer": scorer, "details": "..."}
        
        test_scorer_button.click(
            fn=test_scorer,
            inputs=[generated_output, expected_output, scorer_type],
            outputs=[score_output, score_visualization],
        )
    
    return playground


def create_agent_debugging_playground():
    """Create agent debugging visualization."""
    with gr.Blocks(title="Agent Debugging") as playground:
        gr.Markdown("## Agent Debugging Visualization")
        gr.Markdown("Visualize agent steps, tool calls, and reasoning.")
        
        trace_id_input = gr.Textbox(
            label="Trace ID",
            placeholder="Enter trace ID...",
        )
        
        load_trace_button = gr.Button("Load Trace", variant="primary")
        
        with gr.Row():
            with gr.Column():
                steps_output = gr.JSON(
                    label="Agent Steps",
                )
            
            with gr.Column():
                tool_calls_output = gr.JSON(
                    label="Tool Calls",
                )
        
        reasoning_output = gr.Textbox(
            label="Reasoning",
            lines=10,
            interactive=False,
        )
        
        def load_trace(trace_id: str):
            """Load and visualize trace."""
            # This would fetch trace and extract steps/tool calls
            # Placeholder implementation
            return (
                [{"step": 1, "action": "load_dataset", "status": "success"}],
                [{"tool": "load_dataset", "parameters": {"path": "data.jsonl"}}],
                "Agent loaded dataset successfully.",
            )
        
        load_trace_button.click(
            fn=load_trace,
            inputs=[trace_id_input],
            outputs=[steps_output, tool_calls_output, reasoning_output],
        )
    
    return playground
