# GitOps-Driven Scalable ML Inference Platform

## 1. Project Objective

Build a production-grade ML inference platform that demonstrates how a machine learning model can be developed, containerized, deployed, monitored, automatically scaled, and continuously delivered through a GitOps workflow.

The platform should demonstrate practical DevOps/MLOps engineering rather than simply deploying a FastAPI application.

### Core Engineering Goals

* Serve an ML model through a production-grade FastAPI API.
* Package the application as a secure Docker image.
* Provision Kubernetes/cloud infrastructure using Terraform.
* Manage Kubernetes deployments declaratively.
* Implement GitOps using ArgoCD.
* Build CI pipelines using GitHub Actions.
* Automatically build, test, scan, and publish container images.
* Deploy new versions through Git-based configuration changes.
* Implement Kubernetes health checks and resource management.
* Implement Horizontal Pod Autoscaling.
* Collect application and infrastructure metrics with Prometheus.
* Visualize metrics and system health with Grafana.
* Perform load testing and demonstrate autoscaling behavior.
* Implement security, reliability, and operational best practices.

---

# 2. Target Architecture

```text
                         Developer
                             |
                             v
                    +----------------+
                    |    GitHub      |
                    | Source Code    |
                    +-------+--------+
                            |
                            v
                    GitHub Actions CI
                            |
             +--------------+--------------+
             |              |              |
             v              v              v
          Tests         Docker Build    Trivy Scan
             |              |              |
             +--------------+--------------+
                            |
                            v
                    Container Registry
                    (GHCR / ECR)
                            |
                            |
                     GitOps Repository
                            |
                            v
                         ArgoCD
                            |
                            v
                     Kubernetes Cluster
                            |
            +---------------+---------------+
            |               |               |
            v               v               v
       FastAPI Pods       Service          HPA
            |                               |
            |                               v
            |                         Scale Pods
            |
            v
       ML Model
            |
            v
      Prometheus Metrics
            |
            v
          Grafana


Terraform
    |
    +----> Kubernetes / Cloud Infrastructure
```

---

# 3. Repository Architecture

Use a structure that clearly separates application code, infrastructure, deployment configuration, and testing.

```text
ml-inference-platform/
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── docker.yml
│       └── security.yml
│
├── model_service/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   │
│   │   ├── api/
│   │   │   ├── health.py
│   │   │   └── prediction.py
│   │   │
│   │   ├── schemas/
│   │   │   └── prediction.py
│   │   │
│   │   ├── services/
│   │   │   └── inference.py
│   │   │
│   │   └── metrics.py
│   │
│   ├── model/
│   │   └── model.joblib
│   │
│   ├── tests/
│   │   ├── test_health.py
│   │   ├── test_prediction.py
│   │   └── test_model.py
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
│
├── infrastructure/
│   ├── modules/
│   │   ├── network/
│   │   ├── kubernetes/
│   │   └── monitoring/
│   │
│   ├── environments/
│   │   ├── dev/
│   │   └── production/
│   │
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   └── versions.tf
│
├── k8s/
│   ├── base/
│   │   ├── namespace.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   ├── serviceaccount.yaml
│   │   ├── hpa.yaml
│   │   └── kustomization.yaml
│   │
│   └── overlays/
│       ├── dev/
│       │   ├── kustomization.yaml
│       │   └── patch.yaml
│       │
│       └── production/
│           ├── kustomization.yaml
│           └── patch.yaml
│
├── argocd/
│   ├── project.yaml
│   ├── application.yaml
│   └── application-set.yaml
│
├── monitoring/
│   ├── prometheus/
│   ├── grafana/
│   └── alerts/
│
├── load_tests/
│   ├── k6/
│   │   ├── smoke.js
│   │   ├── load.js
│   │   └── stress.js
│   │
│   └── README.md
│
├── scripts/
│   ├── local-dev.sh
│   ├── build.sh
│   └── deploy-dev.sh
│
├── docs/
│   ├── architecture.md
│   ├── deployment.md
│   ├── troubleshooting.md
│   └── load-testing.md
│
├── .gitignore
├── README.md
├── Makefile
└── CLAUDE.md
```

---

# 4. Implementation Phases

## Phase 1 — ML Inference API

Build the inference service first.

### Requirements

Implement:

```text
GET  /health
GET  /ready
GET  /metrics
POST /predict
```

### `/health`

Used as a Kubernetes liveness probe.

Response:

```json
{
  "status": "healthy"
}
```

### `/ready`

Used as a Kubernetes readiness probe.

It should verify that:

* application initialized successfully
* model is loaded
* required dependencies are available

### `/predict`

Use Pydantic request/response models.

Example:

```json
{
  "features": [...]
}
```

Response:

```json
{
  "prediction": 1,
  "confidence": 0.94,
  "model_version": "v1.0.0"
}
```

### Requirements

* Pydantic validation
* structured JSON logging
* exception handling
* model loaded once during startup
* configuration through environment variables
* no hardcoded secrets
* Prometheus metrics
* API documentation through OpenAPI

---

# 5. Phase 2 — Testing

Create a proper testing layer before containerization.

### Unit Tests

Test:

* request validation
* model loading
* prediction logic
* invalid input
* health endpoint
* readiness endpoint
* error handling

Run:

```bash
pytest model_service/tests/ -v
```

### API Tests

Use FastAPI's `TestClient`.

Test:

```text
POST /predict
GET /health
GET /ready
```

### Test Coverage

Target:

```text
>80% application coverage
```

Use:

```bash
pytest --cov=model_service/app
```

---

# 6. Phase 3 — Production Docker Image

Create a secure multi-stage Docker build.

Requirements:

* Python slim base image
* multi-stage build where appropriate
* non-root user
* minimal dependencies
* `.dockerignore`
* pinned dependency versions
* no secrets inside image
* healthcheck where appropriate
* deterministic image build

Example runtime principle:

```text
Docker
  |
  +-- Non-root user
  +-- Minimal OS packages
  +-- Python dependencies
  +-- Application
  +-- Model artifact
```

Build:

```bash
docker build -t ml-inference-service:latest model_service/
```

Run:

```bash
docker run \
  -p 8000:8000 \
  ml-inference-service:latest
```

Verify:

```bash
curl http://localhost:8000/health
```

---

# 7. Phase 4 — Container Security

Integrate Trivy into the development and CI workflow.

```bash
trivy image ml-inference-service:latest
```

CI should fail for configured critical vulnerabilities.

Also scan:

* Docker image
* filesystem dependencies
* IaC files

Example:

```bash
trivy fs .
trivy config infrastructure/
trivy image $IMAGE
```

---

# 8. Phase 5 — Kubernetes Deployment

Create Kubernetes manifests using Kustomize.

Required resources:

```text
Namespace
Deployment
Service
ConfigMap
ServiceAccount
HPA
PodDisruptionBudget
NetworkPolicy
```

### Deployment Requirements

Every container must define:

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "256Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```

Configure:

```text
replicas
livenessProbe
readinessProbe
startupProbe
resources
securityContext
rollingUpdate
```

Use:

```yaml
securityContext:
  runAsNonRoot: true
  allowPrivilegeEscalation: false
```

---

# 9. Phase 6 — Kubernetes Autoscaling

Implement Horizontal Pod Autoscaler.

Example strategy:

```text
Minimum replicas: 2
Maximum replicas: 10
CPU target: 60%
Memory target: 70%
```

The exact values should be validated through load testing rather than assumed to be optimal.

Demonstrate:

```text
Low traffic
    ↓
2 Pods

Traffic increases
    ↓
HPA detects resource pressure

    ↓
4 Pods

Traffic increases further
    ↓
8 Pods

Traffic decreases
    ↓
Pods scale down
```

---

# 10. Phase 7 — Infrastructure as Code

Use Terraform/OpenTofu to provision infrastructure.

### Local Development

Support:

```text
Kind
```

or:

```text
Minikube
```

### Production Architecture

For AWS:

```text
AWS
 |
 +-- VPC
 |
 +-- Subnets
 |
 +-- EKS
 |
 +-- IAM
 |
 +-- ECR
 |
 +-- Security Groups
 |
 +-- CloudWatch / logging integration
```

Terraform should manage infrastructure rather than Kubernetes application deployments.

### Important Separation

Terraform:

```text
Infrastructure
```

ArgoCD:

```text
Application deployment
```

This separation should be explicitly documented.

---

# 11. Phase 8 — GitOps with ArgoCD

ArgoCD becomes the deployment controller.

Desired workflow:

```text
Developer
   |
   v
Git push
   |
   v
GitHub Actions
   |
   +--> Test
   +--> Build
   +--> Scan
   +--> Push Image
   |
   v
Update image tag in GitOps configuration
   |
   v
ArgoCD detects Git change
   |
   v
Kubernetes deployment
```

### GitOps Rules

Never manually deploy production workloads with:

```bash
kubectl apply
```

Production state must originate from Git.

Use:

```text
Git → ArgoCD → Kubernetes
```

rather than:

```text
Developer → kubectl → Production
```

---

# 12. Phase 9 — CI/CD Pipeline

Create GitHub Actions workflows.

## CI Pipeline

Trigger:

```text
Pull Request
Push
```

Pipeline:

```text
Checkout
   ↓
Setup Python
   ↓
Install dependencies
   ↓
Lint
   ↓
Unit tests
   ↓
Coverage
   ↓
Docker build
   ↓
Trivy scan
```

---

## Image Pipeline

On merge to main:

```text
Checkout
   ↓
Test
   ↓
Build Docker image
   ↓
Generate immutable image tag
   ↓
Security scan
   ↓
Push to GHCR/ECR
```

Avoid relying exclusively on:

```text
latest
```

Prefer:

```text
ml-inference-service:git-<commit-sha>
```

or another immutable tag strategy.

---

# 13. Phase 10 — Automated GitOps Promotion

After a successful image build:

```text
New Image
    ↓
Update Kubernetes image tag
    ↓
Create Git commit / PR
    ↓
GitOps repository
    ↓
ArgoCD
    ↓
Cluster
```

For a production-style workflow, prefer a PR-based promotion mechanism rather than silently modifying deployment configuration.

This creates an auditable deployment history.

---

# 14. Phase 11 — Observability

Implement the three major observability signals:

```text
Metrics
Logs
Health
```

## Prometheus

Expose:

```text
/predict request count
/request latency
/error count
/inference latency
/active requests
```

Example metrics:

```text
http_requests_total
http_request_duration_seconds
model_inference_duration_seconds
prediction_errors_total
```

---

# 15. Phase 12 — Grafana Dashboard

Create a production-style dashboard showing:

### Application

```text
Requests/sec
Request latency
Error rate
Inference latency
```

### Kubernetes

```text
Pod count
CPU usage
Memory usage
Restart count
HPA replicas
```

### Infrastructure

```text
Node CPU
Node memory
Cluster utilization
```

The dashboard should make it possible to visually understand what happens during a traffic spike.

---

# 16. Phase 13 — Alerting

Create Prometheus alert rules.

Examples:

```text
HighErrorRate
HighRequestLatency
PodRestartingFrequently
HighCPUUsage
HighMemoryUsage
DeploymentUnavailable
```

Example concept:

```text
Error rate > 5%
for 5 minutes
    ↓
Alert
```

Do not create arbitrary thresholds without documenting why they were chosen.

---

# 17. Phase 14 — Load Testing

Use k6.

Create three scenarios.

### Smoke Test

Small amount of traffic to verify correctness.

```text
10 users
1 minute
```

### Load Test

Simulate expected traffic.

```text
50–100 concurrent users
5–10 minutes
```

### Stress Test

Gradually increase traffic until the system demonstrates its scaling or performance limits.

```text
10
 ↓
25
 ↓
50
 ↓
100
 ↓
200
```

Record:

```text
RPS
p50 latency
p95 latency
p99 latency
error rate
pod count
CPU
memory
```

---

# 18. Phase 15 — Autoscaling Demonstration

The project should contain an actual experiment demonstrating HPA.

Example:

```text
Before Load
-------------
Pods: 2
CPU: 20%
RPS: 5


During Load
-------------
Pods: 6
CPU: 65%
RPS: 80


Peak Load
-------------
Pods: 10
CPU: 75%
RPS: 150


After Load
-------------
Pods: 2
CPU: 20%
```

These numbers should come from the actual experiment, not be fabricated.

Document the results in:

```text
docs/load-testing.md
```

---

# 19. Phase 16 — Reliability

Add production-oriented reliability mechanisms.

Implement:

* rolling deployments
* readiness probes
* startup probes
* PodDisruptionBudget
* graceful shutdown
* replica redundancy
* resource limits
* HPA
* deployment health checks

Optional:

```text
Pod anti-affinity
topology spread constraints
```

---

# 20. Phase 17 — Kubernetes Security

Implement:

```text
Non-root containers
Read-only filesystem where practical
Dropped Linux capabilities
No privilege escalation
Dedicated ServiceAccount
NetworkPolicy
Secrets management
RBAC
```

Never commit:

```text
AWS credentials
API keys
database passwords
tokens
private keys
```

---

# 21. Phase 18 — Developer Experience

Create a `Makefile`.

Example:

```bash
make install
make test
make lint
make build
make docker-build
make docker-scan
make run
make k8s-deploy
make load-test
```

A new developer should be able to understand the project quickly.

---

# 22. Phase 19 — Documentation

README must contain:

## Project Overview

What problem the platform solves.

## Architecture

Include an architecture diagram.

## Technology Stack

```text
Python
FastAPI
Docker
Kubernetes
Terraform
ArgoCD
GitHub Actions
Prometheus
Grafana
k6
Trivy
```

## Local Setup

Exact commands to reproduce the environment.

## CI/CD

Explain the pipeline.

## GitOps

Explain how Git changes reach Kubernetes.

## Autoscaling

Explain HPA behavior.

## Observability

Explain Prometheus/Grafana.

## Load Testing

Include real benchmark results.

## Troubleshooting

Document common failures.

---

# 23. Definition of Done

The project is complete only when all of the following work.

### Application

* [ ] `/predict` works
* [ ] `/health` works
* [ ] `/ready` works
* [ ] `/metrics` works
* [ ] Pydantic validation works
* [ ] Structured logging works
* [ ] Model loads correctly

### Testing

* [ ] Unit tests pass
* [ ] API tests pass
* [ ] Coverage is measured
* [ ] Invalid requests are tested

### Docker

* [ ] Image builds successfully
* [ ] Container runs as non-root
* [ ] Image is vulnerability scanned
* [ ] Image size is reasonably optimized

### Kubernetes

* [ ] Deployment works
* [ ] Service works
* [ ] Probes work
* [ ] Resource requests/limits exist
* [ ] HPA works
* [ ] SecurityContext configured

### Terraform

* [ ] Infrastructure is reproducible
* [ ] Variables are documented
* [ ] Outputs are defined
* [ ] Terraform validation passes

### GitOps

* [ ] ArgoCD application works
* [ ] Git is the source of truth
* [ ] Deployment synchronization works
* [ ] Rollback process is documented

### CI/CD

* [ ] Tests run automatically
* [ ] Docker image builds automatically
* [ ] Trivy scan runs automatically
* [ ] Image is pushed to registry
* [ ] GitOps configuration is updated through an auditable workflow

### Observability

* [ ] Prometheus collects metrics
* [ ] Grafana dashboard works
* [ ] Application metrics exist
* [ ] Kubernetes metrics exist
* [ ] Alerts are configured

### Performance

* [ ] k6 tests work
* [ ] p95 latency is measured
* [ ] Error rate is measured
* [ ] HPA scaling is demonstrated
* [ ] Results are documented

---

# 24. Recruiter Demonstration Scenario

The final project should be demonstrable in approximately 5–10 minutes.

### Demonstration

1. Show GitHub repository.
2. Show architecture diagram.
3. Open FastAPI `/docs`.
4. Send a prediction request.
5. Show Kubernetes pods.
6. Show ArgoCD application.
7. Push a new application version.
8. Show GitHub Actions pipeline.
9. Show Docker image/security scan.
10. Show ArgoCD detecting the Git change.
11. Show Kubernetes rolling deployment.
12. Start k6 load test.
13. Open Grafana.
14. Show request rate increasing.
15. Show HPA increasing replica count.
16. Stop the load test.
17. Show replicas scaling back down.

The objective is to demonstrate an end-to-end production workflow rather than merely showing individual technologies.

---

# 25. Engineering Principles

Always prioritize:

```text
Reproducibility
Automation
Security
Observability
Reliability
Scalability
Auditability
Infrastructure as Code
GitOps
Least Privilege
```

Avoid:

```text
Manual production deployments
Hardcoded secrets
Mutable production images
Untracked infrastructure changes
Unvalidated configuration
Running containers as root
Ignoring resource limits
"latest" as the only deployment version
Unmeasured performance claims
```

---

# 26. AI Coding Assistant Rules

When modifying this repository:

1. Understand the existing architecture before changing files.
2. Do not introduce unnecessary technologies.
3. Do not rewrite working components without a concrete reason.
4. Keep application, infrastructure, and deployment concerns separated.
5. Never hardcode credentials or secrets.
6. Never bypass the GitOps workflow for production deployment.
7. Add tests for new application behavior.
8. Update documentation when architecture or commands change.
9. Validate Kubernetes manifests before considering the task complete.
10. Validate Terraform configuration before considering infrastructure work complete.
11. Prefer immutable image tags.
12. Keep Docker images minimal and secure.
13. Preserve backward compatibility unless explicitly instructed otherwise.
14. Do not fabricate benchmark results, security findings, or deployment results.
15. If a command cannot be executed in the current environment, state that clearly.
16. Before introducing a new dependency, determine whether an existing dependency already solves the problem.
17. Keep secrets outside Git and outside Docker images.
18. Use least-privilege RBAC.
19. Treat Git as the desired-state source of truth.
20. Make every production change reproducible.

---

# 27. Final Project Outcome

The finished repository should demonstrate the following complete lifecycle:

```text
                 MACHINE LEARNING MODEL
                          |
                          v
                    FastAPI API
                          |
                          v
                       Docker
                          |
                          v
                     Trivy Scan
                          |
                          v
                  Container Registry
                          |
                          v
                    GitHub Actions
                          |
                          v
                   GitOps Repository
                          |
                          v
                       ArgoCD
                          |
                          v
                    Kubernetes
                          |
             +------------+------------+
             |            |            |
             v            v            v
          Service        HPA        Probes
             |
             v
        ML Inference
             |
             v
       Prometheus
             |
             v
          Grafana
             |
             v
       Load Testing
             |
             v
     Measured Autoscaling
```

The final repository should look and behave like a **small production ML platform**, not a collection of disconnected Kubernetes, Terraform, Docker, and Python examples.



