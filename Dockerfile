# Multi-stage Dockerfile for AI Evolution Platform
# Stage 1: Builder
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=0.1.0

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy dependency files
COPY pyproject.toml ./
COPY requirements.txt ./
COPY requirements-dev.txt ./
COPY requirements-llm.txt ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    if [ -f requirements-llm.txt ]; then pip install --no-cache-dir -r requirements-llm.txt; fi

# Install application in editable mode
COPY . .
RUN pip install --no-cache-dir -e .

# Stage 2: Runtime
FROM python:3.11-slim as runtime

# Set labels
LABEL org.opencontainers.image.title="AI Evolution Platform" \
      org.opencontainers.image.description="Unified AI Evaluation and Experimentation Platform" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.licenses="MIT"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r aievolution && useradd -r -g aievolution aievolution

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=aievolution:aievolution . .

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R aievolution:aievolution /app

# Switch to non-root user
USER aievolution

# Expose port
EXPOSE 7890

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:7890/health || exit 1

# Default command
CMD ["python", "-m", "aieval.api.server"]
