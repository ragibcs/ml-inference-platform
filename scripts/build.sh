#!/usr/bin/env bash
# ==============================================================================
# Model Training and Docker Build Script
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

IMAGE_TAG="${1:-latest}"

cd "${ROOT_DIR}"

echo "1. Training and serializing ML model artifact..."
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi
PYTHONPATH=model_service python model_service/model/train.py

echo "2. Building production multi-stage Docker image (tag: ml-inference-service:${IMAGE_TAG})..."
docker build -t "ml-inference-service:${IMAGE_TAG}" model_service/

echo "Build complete. Verified image: ml-inference-service:${IMAGE_TAG}"
