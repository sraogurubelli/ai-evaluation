"""Server entry point for FastAPI application."""

import os
import uvicorn
import logging
from dotenv import load_dotenv
from ai_evolution.api.app import create_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


def main():
    """Run the FastAPI server."""
    # Support debug mode via environment variable
    debug = os.getenv("DEBUG", "false").lower() == "true"
    reload = os.getenv("RELOAD", "false").lower() == "true" or debug
    
    # Use import string when reload is enabled (required by uvicorn)
    if reload:
        uvicorn.run(
            "ai_evolution.api.app:app",
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "7890")),
            log_level="debug" if debug else "info",
            reload=reload,
        )
    else:
        # Use app object directly when reload is disabled
        app = create_app()
        uvicorn.run(
            app,
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "7890")),
            log_level="debug" if debug else "info",
            reload=reload,
        )


if __name__ == "__main__":
    main()
