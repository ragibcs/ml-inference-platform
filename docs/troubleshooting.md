# Production Operational Troubleshooting Runbook

This guide details incident diagnosis and remediation procedures for common failure scenarios across the ML inference platform.

---

## 1. Pods in `CrashLoopBackOff` or `ImagePullBackOff`

### Diagnosis
```bash
# Check pod status and restart count
kubectl get pods -n ml-platform-prod -l app.kubernetes.io/name=ml-inference-service

# Inspect recent container logs
kubectl logs -n ml-platform-prod -l app.kubernetes.io/name=ml-inference-service --tail=50 --previous

# Describe pod events (image pull errors, permission errors, OOMKills)
kubectl describe pod -n ml-platform-prod <pod-name>
```

### Common Causes & Fixes
* **Missing Model Artifact:** If log states `Model artifact not found at model/model.joblib`, verify the Docker image was built with `python model_service/model/train.py` before container packaging.
* **Non-Root Permission Denied:** The container runs as non-root UID 10001. Ensure `/app` permissions permit read access (`chmod 755 /app`).
* **Exit Code 137 (OOMKilled):** If container memory usage exceeded `limits.memory: 512Mi`, check recent batch size submissions and increase pod memory limits in `k8s/overlays/production/patch.yaml`.

---

## 2. Readiness Probe Failing (HTTP 503 `status: unready`)

### Diagnosis
```bash
# Test readiness endpoint directly inside cluster
kubectl exec -it -n ml-platform-prod <pod-name> -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/ready').read())"

# Check Prometheus model load status metric
kubectl exec -it -n ml-platform-prod <pod-name> -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/metrics').read().decode())" | grep model_load_status
```

### Remediation
* The readiness probe returns 503 if `model_service.is_loaded` is `false`. Verify that joblib model deserialization succeeded during the FastAPI `lifespan` startup handler.
* Check whether scikit-learn version mismatch occurred between training environment and inference container.

---

## 3. Horizontal Pod Autoscaler (HPA) Not Scaling

### Diagnosis
```bash
# Check HPA status and target metrics
kubectl get hpa -n ml-platform-prod ml-inference-hpa

# Verify metrics-server is collecting pod resource metrics
kubectl top pods -n ml-platform-prod
kubectl top nodes
```

### Common Causes & Fixes
* **`<unknown>/60%` CPU metric:** Indicates Kubernetes `metrics-server` is either not running or cannot scrape kubelet ports. Verify metrics-server deployment:
  ```bash
  kubectl get deployment metrics-server -n kube-system
  ```
* **Resource Requests Missing:** HPA requires container `resources.requests.cpu` and `resources.requests.memory` to calculate percentage utilization. Ensure requests are defined in `k8s/base/deployment.yaml`.

---

## 4. ArgoCD Synchronization / Deployment Degraded

### Diagnosis
```bash
# Check ArgoCD application status via CLI
argocd app get ml-inference-prod

# Inspect sync status and difference from Git desired state
argocd app diff ml-inference-prod
```

### Remediation
* **Out of Sync (Git SHA mismatch):** Force sync using `argocd app sync ml-inference-prod --prune`.
* **Kustomize Build Error:** Test local overlay build:
  ```bash
  kustomize build k8s/overlays/production
  ```
* **Rollback Procedure:** To immediately roll back a faulty production deployment to a known good version:
  ```bash
  ./scripts/promote.sh production <previous-git-sha> false
  git commit -am "chore(gitops): rollback ml-inference-service to <previous-git-sha>"
  git push origin main
  ```
  ArgoCD will automatically reconcile and perform a rolling update to the previous working image.

---

## 5. NetworkPolicy Blocking Ingress or DNS

### Diagnosis
* If pods report DNS failure (`socket.gaierror`) or Prometheus cannot scrape `/metrics` (Scrape timeout):
```bash
# Check active network policies
kubectl get netpol -n ml-platform-prod
```
* Ensure `k8s/base/networkpolicy.yaml` permits UDP/TCP on port 53 for kube-dns, and ingress on port 8000 from the Prometheus namespace (`monitoring`).
