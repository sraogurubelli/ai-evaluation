# UI

Web UI (Gradio) for running experiments and viewing results.

## Launch

```bash
# Start API first (other terminal)
aieval-server

# Then start UI
python -m aieval.ui.server
```

UI: `http://localhost:7860`. Set `AI_EVOLUTION_API_URL` if API is elsewhere (default `http://localhost:8000`).

## Features

- **Run experiment:** Configure name, dataset, adapter, scorers, model; start and monitor task.
- **View results:** Task status, completed experiments, task details.

API used: `POST /experiments`, `GET /tasks`, `GET /tasks/{id}`.
