# Multi-stage Dockerfile for GEngine Echoes of Emergence services
# Supports: simulation, gateway, and llm services
# Build with: docker build -t gengine:latest .
# Run individual services with the SERVICE environment variable

# =============================================================================
# Stage 1: Base image with uv and Python dependencies
# =============================================================================
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

# Install curl for health checks and bash for entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create app directory
WORKDIR /app

# Copy dependency files and source so the package can be installed
COPY pyproject.toml ./
COPY src/ ./src/

# Install the gengine package + dependencies into the system environment
RUN uv pip install --system .

# =============================================================================
# Stage 2: Runtime image with application code
# =============================================================================
FROM base AS runtime

# Copy source code
COPY src/ ./src/

# Copy content directory (world data and configs)
COPY content/ ./content/

# Also copy content into the path used by the loader in site-packages
RUN mkdir -p /usr/local/lib/python3.12/content && \
  cp -R ./content/* /usr/local/lib/python3.12/content/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Default environment variables
ENV ECHOES_SERVICE_HOST=0.0.0.0 \
    ECHOES_SERVICE_PORT=8000 \
    ECHOES_SERVICE_WORLD=default \
    ECHOES_GATEWAY_HOST=0.0.0.0 \
    ECHOES_GATEWAY_PORT=8100 \
    ECHOES_LLM_PROVIDER=stub

# The SERVICE environment variable determines which service to run:
# - simulation: runs the simulation service (port 8000)
# - gateway: runs the gateway service (port 8100)
# - llm: runs the LLM service (port 8001)
ENV SERVICE=simulation

# Expose all possible ports (actual port depends on service)
EXPOSE 8000 8001 8100

# Health check (will be overridden per service in compose)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${ECHOES_SERVICE_PORT:-8000}/healthz || exit 1

# Entrypoint script to run the appropriate service
COPY --chown=appuser:appuser <<'EOF' /app/entrypoint.sh
#!/bin/bash
set -e

case "${SERVICE}" in
  simulation)
    echo "Starting Simulation Service on port ${ECHOES_SERVICE_PORT:-8000}..."
    exec python -m gengine.echoes.service.main
    ;;
  gateway)
    echo "Starting Gateway Service on port ${ECHOES_GATEWAY_PORT:-8100}..."
    exec python -m gengine.echoes.gateway.main
    ;;
  llm)
    echo "Starting LLM Service on port 8001..."
    exec python -m gengine.echoes.llm.main
    ;;
  *)
    echo "Unknown service: ${SERVICE}"
    echo "Valid services: simulation, gateway, llm"
    exit 1
    ;;
esac
EOF

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]

# =============================================================================
# Stage 3: Development image with dev dependencies
# =============================================================================
FROM runtime AS development

USER root

# Install dev dependencies
RUN uv pip install --system -e ".[dev]"

USER appuser

# Override for development to allow source mounting
ENV PYTHONDONTWRITEBYTECODE=0
