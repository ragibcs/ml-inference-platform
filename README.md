# GitOps-Driven Scalable ML Inference Platform

[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue.svg)](.github/workflows/ci.yml)
[![GitOps](https://img.shields.io/badge/GitOps-ArgoCD-orange.svg)](argocd/application.yaml)
[![Kubernetes](https://img.shields.io/badge/Orchestration-Kubernetes%20%2F%20Kustomize-326ce5.svg)](k8s/)
[![IaC](https://img.shields.io/badge/IaC-Terraform-7B42BC.svg)](infrastructure/)
[![Observability](https://img.shields.io/badge/Monitoring-Prometheus%20%26%20Grafana-F46800.svg)](monitoring/)
[![Security](https://img.shields.io/badge/Security-Trivy%20Scanned-2496ED.svg)](.trivy.yaml)
[![Test Coverage](https://img.shields.io/badge/Coverage-93%25-brightgreen.svg)](model_service/tests/)

A production-grade, enterprise-scale Machine Learning Inference Platform demonstrating how an ML model is developed, containerized, securely scanned, deployed via declarative GitOps (ArgoCD), horizontally autoscaled (HPA), and monitored in real-time with Prometheus and Grafana.

---

## 1. Project Overview

Deploying an ML model is straightforward; operating an enterprise-grade ML platform requires solving critical DevOps and MLOps challenges:
* **Zero-Downtime Releases:** Rolling deployment strategies that verify model memory initialization before routing client traffic.
* **Declarative GitOps Delivery:** Eliminating manual `kubectl` interventions by designating Git as the single source of truth.
* **Automated Elastic Autoscaling:** Responding dynamically to traffic surges with Horizontal Pod Autoscalers (HPA).
* **Comprehensive Observability:** Real-time RED metrics (Rate, Errors, Duration) and pure model inference latency telemetry.
* **Security & Hardening:** Multi-stage non-root container builds, dropped Linux capabilities, and automated CI/CD vulnerability scanning with Trivy.

---

## 2. Architecture Diagram

```text
                         Developer / Data Scientist
                                    │
                                    ▼
                         ┌────────────────────┐
                         │   GitHub Source    │
                         │    Repository      │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ GitHub Actions CI  │
                         │  - Pytest (>90%)   │
                         │  - Multi-stage BLD │
                         │  - Trivy Vuln Scan │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ Container Registry │
                         │  (GHCR / AWS ECR)  │
                         │  tag: git-<sha>    │
                         └─────────┬──────────┘
                                   │
                     ┌─────────────┴─────────────┐
                     │ Automated Promotion PR    │
                     │ Updates k8s/overlays/prod │
                     └─────────────┬─────────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │  ArgoCD Controller │
                         │  (Sync State)      │
                         └─────────┬──────────┘
                                   │ Reconciles
                                   ▼
            ┌──────────────────────────────────────────────┐
            │        Kubernetes Production Cluster         │
            │                                              │
            │  ┌────────────────┐      ┌────────────────┐  │
            │  │ Ingress/Service│ ───► │  FastAPI Pods  │  │
            │  └────────────────┘      │  (scikit-learn)│  │
            │                          └────────┬───────┘  │
            │  ┌────────────────┐               │          │
            │  │  HPA Autoscaler│ ◄─────────────┤          │
            │  │  (CPU > 60%)   │ Scales 2->10  │          │
            │  └────────────────┘               │          │
            │                                   ▼          │
            │  ┌────────────────┐      ┌────────────────┐  │
            │  │    Grafana     │ ◄─── │   Prometheus   │  │
            │  │   Dashboards   │      │ (RED Telemetry)│  │
            │  └────────────────┘      └────────────────┘  │
            └──────────────────────────────────────────────┘
```

---

## 3. Technology Stack

| Layer | Technologies | Description |
| :--- | :--- | :--- |
| **API & ML Runtime** | Python 3.12, FastAPI, Uvicorn, scikit-learn, Pydantic | High-performance async REST API serving validated model inferences |
| **Containerization** | Docker (Multi-Stage), non-root (`appuser`), Distroless-style | Minimal, secured OCI container image (146MB compressed) |
| **Security Scanning** | Trivy, SARIF, GitHub Security Tab | Automated CVE, secret, and IaC misconfiguration scanning |
| **Orchestration** | Kubernetes 1.30, Kustomize | Declarative base and environment overlays (`dev`, `production`) |
| **GitOps** | ArgoCD (Application & ApplicationSet) | Continuous reconciliation and automated sync from Git to cluster |
| **Infrastructure as Code**| Terraform (AWS VPC, Subnets, EKS, IAM, ECR) | Reproducible cloud infrastructure provisioning |
| **CI/CD** | GitHub Actions | Automated linting, testing, image build, scanning, and tag promotion |
| **Observability** | Prometheus, Grafana, Alertmanager | RED metrics, inference latency percentiles, HPA dashboards, and SLO alerts |
| **Performance Testing** | k6 | Smoke, sustained load, and progressive stress testing suites |

---

## 4. Quickstart & Local Reproduction

### Step 1: Clone Repository and Setup Environment
```bash
git clone https://github.com/ragibcs/ml-inference-platform.git
cd ml-inference-platform

# Install dependencies and train baseline model artifact
make install
make train-model
```

### Step 2: Run Unit & Integration Tests (>80% Coverage)
```bash
make test
```
*Current test suite achieves **93% test coverage** across 23 unit and integration tests.*

### Step 3: Run Local Development Server
```bash
make run
```
Access the interactive OpenAPI Swagger UI at `http://localhost:8000/docs`.

### Step 4: Build & Test Local Production Container
```bash
# Build production multi-stage Docker image
make docker-build

# Run container locally on port 8000
make docker-run
```

Verify endpoints in another terminal:
```bash
# Liveness Probe
curl http://localhost:8000/health
# {"status":"healthy"}

# Readiness Probe
curl http://localhost:8000/ready
# {"status":"ready","model_version":"v1.0.0","model_loaded":true,"dependencies_ready":true,...}

# Prediction Endpoint
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [5.1, 3.5, 1.4, 0.2]}'
# {"prediction":0,"confidence":1.0,"model_version":"v1.0.0","target_class":"setosa","inference_time_ms":1.2}

# Prometheus Metrics
curl http://localhost:8000/metrics | grep http_requests_total
```

---

## 5. CI/CD & Automated GitOps Workflow

```text
1. Developer pushes code to GitHub
2. GitHub Actions CI (`.github/workflows/ci.yml`) runs tests, coverage, and Trivy scan
3. Release Workflow (`.github/workflows/docker.yml`) builds immutable tag `git-<commit-sha>`
4. Script (`scripts/promote.sh`) updates `k8s/overlays/production/kustomization.yaml`
5. ArgoCD detects the commit change and performs a rolling update on Kubernetes
```

### GitOps Rule of Truth
* No manual `kubectl apply` commands in production.
* Production state is declared in Git; rollbacks are executed by promoting previous Git tags.

---

## 6. Kubernetes Autoscaling & Load Testing

The platform configures a **Horizontal Pod Autoscaler (HPA)** targeting 60% CPU utilization with replica scaling from 2 (min) to 10 (max).

### Running k6 Benchmarks
```bash
# Smoke Test (10 VUs, 1 min)
make load-smoke

# Sustained Production Load (50-100 VUs, 9 min)
make load-test

# Autoscaling Stress Test (10 -> 200 VUs)
make load-stress
```

### Empirical Benchmark Summary (From `docs/load-testing.md`)

| Traffic Level | Concurrency | Throughput | p95 Latency | Error Rate | Active Pods |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Idle** | 0 VUs | 5 RPS | 3.1 ms | 0.00% | **2 Pods** |
| **Normal Load** | 50 VUs | 76 RPS | 32.8 ms | 0.00% | **4 Pods** |
| **Peak Stress** | 200 VUs | 265 RPS | 82.5 ms | 0.04% | **10 Pods (Max)** |
| **Cooldown** | 0 VUs | 0 RPS | 2.8 ms | 0.00% | **2 Pods (Min)** |

---

## 7. Observability & SRE Dashboards

* **Prometheus Metrics:** Scrapes endpoints every 10s capturing RED metrics and `model_inference_duration_seconds`.
* **Grafana Dashboard:** Pre-configured dashboard at `monitoring/grafana/dashboards/ml-inference-overview.json`.
* **Alertmanager Rules:** Alerts for error rate > 5%, latency degradation (p95 > 500ms), and model unloaded state.

---

## 8. Recruiter Demonstration Scenario (5–10 Min Walkthrough)

1. **Architecture Overview:** Present `docs/architecture.md` showing end-to-end GitOps flow.
2. **Interactive API:** Open `http://localhost:8000/docs` and execute a sample `/predict` request.
3. **Automated Testing & Coverage:** Run `make test` to show 23 passing tests with 93% code coverage.
4. **Container Security:** Show non-root multi-stage `Dockerfile` and run `make docker-scan`.
5. **GitOps in Action:** Demonstrate `argocd/application.yaml` and `./scripts/promote.sh` immutable tag update.
6. **Live Autoscaling:** Start `make load-stress` and open Grafana to show request rates climbing and HPA scaling pods from 2 to 10.
7. **Graceful Cooldown:** Stop the load test and observe pods scaling back down to 2 replicas without dropping requests.
