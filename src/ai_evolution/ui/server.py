"""UI server launcher."""

import sys
from ai_evolution.ui.gradio_app import create_ui


def main():
    """Launch Gradio UI."""
    demo = create_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
