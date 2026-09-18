#!/usr/bin/env bash
# ==============================================================================
# Automated GitOps Promotion Script
#
# Promotes an immutable image tag to the specified Kubernetes overlay environment.
# Updates the Kustomize image tag and prepares a Git commit or Pull Request.
#
# Usage:
#   ./scripts/promote.sh <environment> <image-tag> [create-pr]
#
# Examples:
#   ./scripts/promote.sh dev git-a1b2c3d
#   ./scripts/promote.sh production v1.0.1 true
# ==============================================================================

set -euo pipefail

ENVIRONMENT="${1:-}"
IMAGE_TAG="${2:-}"
CREATE_PR="${3:-false}"

if [ -z "${ENVIRONMENT}" ] || [ -z "${IMAGE_TAG}" ]; then
  echo "Error: Missing required arguments."
  echo "Usage: $0 <environment: dev|production> <image-tag> [create-pr: true|false]"
  exit 1
fi

TARGET_DIR="k8s/overlays/${ENVIRONMENT}"
KUSTOMIZATION_FILE="${TARGET_DIR}/kustomization.yaml"

if [ ! -f "${KUSTOMIZATION_FILE}" ]; then
  echo "Error: Target overlay kustomization file not found at ${KUSTOMIZATION_FILE}"
  exit 1
fi

echo "=========================================================="
echo "Promoting ML Inference Service"
echo "Environment : ${ENVIRONMENT}"
echo "New Tag     : ${IMAGE_TAG}"
echo "Target File : ${KUSTOMIZATION_FILE}"
echo "=========================================================="

# Update the newTag field in the target overlay kustomization.yaml
if command -v kustomize >/dev/null 2>&1; then
  (cd "${TARGET_DIR}" && kustomize edit set image "ghcr.io/ragibcs/ml-inference-service=ghcr.io/ragibcs/ml-inference-service:${IMAGE_TAG}")
else
  # Portable sed replacement
  sed -i -E "s/(newTag: ).*/\1${IMAGE_TAG}/" "${KUSTOMIZATION_FILE}"
fi

echo "Successfully updated ${KUSTOMIZATION_FILE} with image tag: ${IMAGE_TAG}"

# Check for Git changes
if git diff --quiet "${KUSTOMIZATION_FILE}"; then
  echo "No changes detected. ${KUSTOMIZATION_FILE} is already at tag ${IMAGE_TAG}."
  exit 0
fi

BRANCH_NAME="promo/${ENVIRONMENT}-${IMAGE_TAG}"
COMMIT_MSG="chore(gitops): promote ml-inference-service to ${IMAGE_TAG} in ${ENVIRONMENT}"

if [ "${CREATE_PR}" = "true" ]; then
  echo "Preparing promotion Pull Request on branch: ${BRANCH_NAME}"
  git checkout -b "${BRANCH_NAME}"
  git add "${KUSTOMIZATION_FILE}"
  git commit -m "${COMMIT_MSG}"
  echo "Promotion commit created on ${BRANCH_NAME}. Push and submit PR with:"
  echo "  git push origin ${BRANCH_NAME} && gh pr create --title '${COMMIT_MSG}' --body 'Automated GitOps promotion.'"
else
  echo "Staging changes locally..."
  git add "${KUSTOMIZATION_FILE}"
  echo "Changes staged. Commit with: git commit -m '${COMMIT_MSG}'"
fi

echo "GitOps promotion completed successfully."
