# ========================================================
# Multi-Stage Production Dockerfile for ML Inference Service
# ========================================================

# --------------------------------------------------------
# Stage 1: Builder
# --------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

# Install security updates and build utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pinned Python dependencies into a virtual target
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# --------------------------------------------------------
# Stage 2: Production Runtime
# --------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

# Apply latest base OS security updates
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Security hardening: Create non-root system group and user
ENV APP_USER=appuser \
    APP_UID=10001 \
    APP_GID=10001 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH=/install/bin:$PATH

RUN groupadd --gid ${APP_GID} ${APP_USER} && \
    useradd --uid ${APP_UID} --gid ${APP_GID} --create-home --shell /bin/bash ${APP_USER}

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application source code and model artifacts
COPY --chown=${APP_USER}:${APP_GID} app/ /app/app/
COPY --chown=${APP_USER}:${APP_GID} model/ /app/model/

# Ensure directory permissions are correctly owned and accessible by non-root user
RUN chown -R ${APP_USER}:${APP_GID} /app && \
    chmod -R 755 /app

# Switch to non-root execution user
USER ${APP_USER}

# Expose HTTP API port
EXPOSE 8000

# Container liveness healthcheck
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Production ASGI server entrypoint
CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "/app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--access-log"]
