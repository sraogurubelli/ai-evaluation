# UI Documentation

## Overview

AI Evolution Platform provides a web-based UI built with Gradio for running experiments, viewing results, and managing evaluations.

## Launching the UI

### Option 1: Using Python

```bash
python -m ai_evolution.ui.server
```

### Option 2: Using Gradio directly

```bash
python -m ai_evolution.ui.gradio_app
```

### Option 3: Programmatically

```python
from ai_evolution.ui import create_ui

demo = create_ui()
demo.launch(server_name="0.0.0.0", server_port=7860)
```

## Configuration

Set the API base URL via environment variable:

```bash
export AI_EVOLUTION_API_URL=http://localhost:8000
python -m ai_evolution.ui.server
```

## Features

### Run Experiment Tab

- **Experiment Configuration**: Configure experiment name, dataset, adapter, scorers, and model
- **Real-time Execution**: Start experiments and monitor task status
- **Task Details**: View detailed task information including task ID and status

### View Results Tab

- **Task Status**: Check the status of running or completed tasks
- **Experiment List**: View list of completed experiments
- **Task Details**: Get detailed information about specific tasks

## API Integration

The UI communicates with the FastAPI backend via REST API:

- `POST /experiments` - Create and run experiments
- `GET /tasks/{id}` - Get task status
- `GET /tasks?status=completed` - List completed tasks

## Future Enhancements

- Real-time progress updates (WebSocket/SSE)
- Results visualization with charts
- Experiment comparison interface
- Export results (CSV, JSON)
- Experiment history and versioning
