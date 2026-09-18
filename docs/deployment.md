# Deployment and Operations Guide

This guide describes how to provision the infrastructure, deploy the ML inference platform, configure GitOps synchronization, and execute production rollouts and rollbacks.

---

## 1. Prerequisites

Ensure the following tools are installed:
* **Docker Engine** (20.10+)
* **Terraform / OpenTofu** (>= 1.5.0)
* **kubectl** (>= 1.28)
* **kustomize** (>= 5.0)
* **ArgoCD CLI** (>= 2.9)
* **AWS CLI** configured with administrator credentials (for cloud deployments)

---

## 2. Infrastructure Provisioning (Terraform)

Terraform provisions the cloud infrastructure (VPC, Subnets, EKS, Node Groups, IAM, and ECR).

### Step 1: Initialize Terraform Modules
```bash
cd infrastructure/environments/production
terraform init
```

### Step 2: Plan and Apply Infrastructure
```bash
# Review planned resources
terraform plan -out=tfplan

# Apply cloud infrastructure
terraform apply tfplan
```

### Step 3: Connect `kubectl` to EKS Cluster
```bash
aws eks update-kubeconfig --region us-east-1 --name ml-platform-prod-eks
kubectl get nodes
```

---

## 3. GitOps Continuous Delivery Setup (ArgoCD)

ArgoCD is installed automatically via Terraform's Helm provider in the `argocd` namespace.

### Step 1: Retrieve ArgoCD Initial Admin Password
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

### Step 2: Port-Forward ArgoCD Web UI
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:80
```
Open `http://localhost:8080` in your browser.

### Step 3: Register GitOps Project and Applications
```bash
# Apply AppProject definition
kubectl apply -f argocd/project.yaml

# Apply Multi-Environment ApplicationSet
kubectl apply -f argocd/application-set.yaml
```

ArgoCD will automatically discover the repository, create the `ml-platform-dev` and `ml-platform-prod` namespaces, and deploy the respective Kustomize overlays.

---

## 4. Continuous Integration & Release Flow

When a developer merges code to `main`:
1. **GitHub Actions CI (`.github/workflows/ci.yml`)** executes tests with coverage validation (`pytest --cov`) and runs Trivy vulnerability scanning.
2. **Release Workflow (`.github/workflows/docker.yml`)** builds the Docker container, stamps an immutable tag (`git-<sha>`), and publishes to GHCR.
3. **Automated Promotion (`scripts/promote.sh`)** updates the Kustomize `newTag` in `k8s/overlays/production/kustomization.yaml` and commits back to the GitOps repository.
4. **ArgoCD** detects the Git change within 3 minutes (or via GitHub Webhook) and performs an automated rolling update.

---

## 5. Zero-Downtime Rolling Updates

The deployment utilizes Kubernetes rolling update mechanics:
* `maxSurge: 25%` ensures new pods are spun up before old ones are terminated.
* `maxUnavailable: 0` ensures the cluster always maintains 100% of desired replica capacity.
* `readinessProbe` ensures client traffic is only routed to newly spawned pods once the ML model artifact is loaded into RAM.

---

## 6. Instant Rollback Procedure

If a deployed model version demonstrates unexpected behavior in production, **never run `kubectl rollout undo`**, as this bypasses GitOps state.

Execute the GitOps rollback script:
```bash
# Promote the previous known good Git SHA or Semantic Release Tag
./scripts/promote.sh production git-a1b2c3d false

# Commit and push desired state to Git
git commit -am "chore(gitops): rollback ml-inference-service to git-a1b2c3d"
git push origin main
```

ArgoCD will instantly detect the commit and reconcile the Kubernetes cluster back to the previous version.
