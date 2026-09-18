# System Architecture Documentation

## 1. System Overview

The **GitOps-Driven Scalable ML Inference Platform** is an enterprise-grade cloud-native machine learning serving platform. It automates the entire lifecycle of model serving: training serialization, unit and integration testing, containerization with security scanning, immutable image promotion, declarative GitOps continuous delivery via ArgoCD, Kubernetes horizontal pod autoscaling, and full-stack observability with Prometheus and Grafana.

---

## 2. High-Level Architecture Diagram

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
                         │  - Pytest (>80%)   │
                         │  - Multi-stage BLD │
                         │  - Trivy Vuln Scan │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ Container Registry │
                         │    (GHCR / ECR)    │
                         │  tag: git-<sha>    │
                         └─────────┬──────────┘
                                   │
                     ┌─────────────┴─────────────┐
                     │ Automated GitOps PR       │
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

## 3. Architecture Layer Breakdown

### Layer 1: Application Layer (`model_service/app/`)
* **Framework:** FastAPI with Python 3.12, Uvicorn ASGI server.
* **Model Inference Engine:** Thread-safe scikit-learn classification pipeline loaded once into memory during the application `lifespan` startup event.
* **Validation & Schemas:** Pydantic models enforcing strict type checking, finite numerical constraints, and array dimension validation.
* **Observability Instrumentation:** Native Prometheus metrics collector tracking RED metrics (`http_requests_total`, `http_request_duration_seconds`, `model_inference_duration_seconds`, `prediction_errors_total`, `active_requests`).
* **Structured Logging:** Unified JSON formatted logging emitting ISO8601 timestamps, request IDs, correlation tags, and error traces.

### Layer 2: Container Security & Packaging (`model_service/Dockerfile`)
* **Multi-Stage Build:** Dedicated builder stage generates optimized wheels; runtime stage contains only lean production dependencies.
* **Least Privilege:** Executes under a non-root system user (`appuser`, UID/GID 10001).
* **Hardening:** Read-only root filesystem, dropped Linux capabilities, and immutable tagging.
* **Automated Scanning:** Integrated Trivy vulnerability scanning blocking CRITICAL and HIGH CVEs.

### Layer 3: Infrastructure as Code (`infrastructure/`)
* **Provisioning Engine:** Terraform / OpenTofu modules managing cloud infrastructure.
* **Separation of Concerns:** Terraform provisions VPC networks, subnets, EKS clusters, IAM roles, and ECR registries. Application deployment is strictly delegated to ArgoCD.
* **Multi-Environment Support:** Structured `dev` and `production` environments with isolated configurations and instance sizing.

### Layer 4: Declarative Kubernetes Workloads (`k8s/`)
* **Configuration Management:** Kustomize base and environment overlays (`k8s/overlays/dev`, `k8s/overlays/production`).
* **Resilience Mechanisms:** `RollingUpdate` deployment strategy (`maxUnavailable: 0`), `PodDisruptionBudget` (`minAvailable: 1`), and non-root SecurityContext.
* **Health Probes:** Kubernetes startup, liveness (`/health`), and readiness (`/ready`) probes guaranteeing zero-downtime rollouts.

### Layer 5: GitOps Delivery (`argocd/`)
* **Source of Truth:** Git repository governs all production cluster states. Manual `kubectl apply` commands in production are strictly forbidden.
* **Reconciliation:** ArgoCD continuously monitors Git configuration changes, detects drift, and reconciles desired state with automatic self-healing.
* **Multi-Cluster / Multi-Env:** `ApplicationSet` generator automates synchronization across development and production environments.

### Layer 6: Observability & Alerting (`monitoring/`)
* **Prometheus:** High-resolution 10-second scrape interval capturing application RED metrics and Kubernetes container utilization.
* **Grafana:** Production dashboard visualizing request rates, p50/p95/p99 latency distributions, prediction classification splits, and HPA replica scaling.
* **Alertmanager:** Configured alert rules for SLO violations (error rate > 5%, p95 latency > 500ms, model unloaded, pod restart frequency).
