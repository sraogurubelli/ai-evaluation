"""Server entry point for FastAPI application."""

import os
import uvicorn
from dotenv import load_dotenv

# Initialize logging before importing app
from aieval.logging_config import initialize_logging
import structlog

# Load environment variables from .env file
load_dotenv()

# Initialize structured logging
initialize_logging()

logger = structlog.get_logger(__name__)

from aieval.api.app import create_app


def main():
    """Run the FastAPI server."""
    # Support debug mode via environment variable
    debug = os.getenv("DEBUG", "false").lower() == "true"
    reload = os.getenv("RELOAD", "false").lower() == "true" or debug

    logger.info(
        "Starting FastAPI server",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "7890")),
        debug=debug,
        reload=reload,
    )

    # Use import string when reload is enabled (required by uvicorn)
    if reload:
        uvicorn.run(
            "aieval.api.app:app",
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
