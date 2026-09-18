# Engineering Guidelines for GitOps ML Inference Platform

This document defines the architecture conventions, verification commands, and engineering rules for AI coding assistants working in this repository.

---

## 1. Repository Structure Overview

* `model_service/app/`: FastAPI application code (api routes, schemas, inference services, metrics, structured logging).
* `model_service/model/`: ML model training script (`train.py`) and serialized artifact (`model.joblib`).
* `model_service/tests/`: Pytest unit and integration test suite.
* `model_service/Dockerfile`: Multi-stage, non-root production container specification.
* `infrastructure/`: Terraform infrastructure modules (`network/`, `kubernetes/`, `monitoring/`) and environments (`dev/`, `production/`).
* `k8s/`: Declarative Kubernetes manifests using Kustomize (`base/` and `overlays/dev/`, `overlays/production/`).
* `argocd/`: GitOps Application, ApplicationSet, and AppProject declarations.
* `monitoring/`: Prometheus scrape configs, ServiceMonitors, Grafana dashboards, and Alertmanager rules.
* `load_tests/`: k6 load testing scenarios (`smoke.js`, `load.js`, `stress.js`).
* `scripts/`: Automation scripts (`local-dev.sh`, `build.sh`, `deploy-dev.sh`, `promote.sh`).

---

## 2. Standard Verification Commands

Always run and verify these commands before concluding tasks:

```bash
# Install dependencies
make install

# Train / serialize baseline model artifact
make train-model

# Run tests with coverage (>80% required)
make test

# Code quality and linting
make lint

# Docker build and container verification
make docker-build
make docker-scan

# Local development server
make run
```

---

## 3. Core Architectural Rules

1. **Separation of Infrastructure and Application:**
   * Terraform manages cloud/Kubernetes cluster infrastructure only.
   * ArgoCD manages application deployments via GitOps.
2. **Git as the Single Source of Truth:**
   * Never execute manual `kubectl apply` commands against production clusters.
   * All production deployments originate from an immutable image tag commit in `k8s/overlays/production/kustomization.yaml`.
3. **Container Security & Least Privilege:**
   * Containers must always run as non-root user `appuser` (UID 10001).
   * Dockerfiles must use multi-stage builds and keep image sizes optimized.
   * Root filesystems must be mounted read-only with Linux capabilities dropped.
4. **Testing Standards:**
   * Every new endpoint or feature requires corresponding pytest tests in `model_service/tests/`.
   * Total application test coverage must always exceed **80%**.
5. **No Hardcoded Secrets:**
   * Never commit credentials, tokens, or private keys to Git.
