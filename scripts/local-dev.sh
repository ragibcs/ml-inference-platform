#!/usr/bin/env bash
# ==============================================================================
# Local Development Startup Script
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

echo "Starting ML Inference Platform in Local Development Mode..."

# Activate virtualenv if present
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# Ensure model artifact exists
if [ ! -f "model_service/model/model.joblib" ]; then
  echo "Training baseline model artifact..."
  PYTHONPATH=model_service python model_service/model/train.py
fi

# Export environment variables for local development
export APP_ENV="dev"
export LOG_LEVEL="DEBUG"
export LOG_FORMAT="json"
export MODEL_PATH="model_service/model/model.joblib"
export PORT="8000"
export HOST="127.0.0.1"

echo "Launching FastAPI server on http://${HOST}:${PORT} (with hot-reload)..."
PYTHONPATH=model_service python -m uvicorn app.main:app --host "${HOST}" --port "${PORT}" --reload
