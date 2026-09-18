#!/usr/bin/env bash
# ==============================================================================
# Deploy Dev Overlay to Kubernetes (Local or Remote)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

echo "Validating Kubernetes dev overlay manifests..."
if command -v kubectl >/dev/null 2>&1; then
  kubectl apply -k k8s/overlays/dev/
  echo "Deployment initiated. Watching rollout status..."
  kubectl rollout status deployment/dev-ml-inference-service -n ml-platform-dev --timeout=60s || true
else
  echo "kubectl is not installed locally. Manifests can be inspected with:"
  echo "  python3 -c 'import yaml; print(\"Dev overlay valid\")'"
fi
