# Performance and Load Testing Guide

This directory contains k6 load testing scenarios designed to benchmark the ML inference service, validate SLO thresholds, and demonstrate Horizontal Pod Autoscaler (HPA) dynamics under stress.

## Scenarios

| Scenario | File | Virtual Users (VUs) | Duration | Objective |
| :--- | :--- | :--- | :--- | :--- |
| **Smoke Test** | `smoke.js` | 10 | 1 min | Sanity check endpoint correctness and base latency |
| **Load Test** | `load.js` | 50 – 100 | 9 min | Simulate sustained production load across single/batch endpoints |
| **Stress Test** | `stress.js` | 10 → 200 | 8 min | Progressive load spike to trigger HPA autoscaling from 2 to 10 pods |

---

## Running with Local k6 CLI

```bash
# Smoke test (against local container or port-forwarded Kubernetes service)
k6 run -e TARGET_URL=http://localhost:8000 load_tests/k6/smoke.js

# Standard Load test
k6 run -e TARGET_URL=http://localhost:8000 load_tests/k6/load.js

# Stress test (Triggers HPA scale-up)
k6 run -e TARGET_URL=http://localhost:8000 load_tests/k6/stress.js
```

---

## Running via Docker (No k6 installation needed)

```bash
docker run --rm -i --net="host" \
  -v $(pwd)/load_tests/k6:/scripts \
  grafana/k6:latest run -e TARGET_URL=http://localhost:8000 /scripts/smoke.js
```

---

## Metric Outputs Captured

* **RPS** (`http_reqs/s`): Total request rate throughput
* **p50 Latency**: Median response time
* **p95 Latency**: 95th percentile response time (SLO target < 250ms)
* **p99 Latency**: 99th percentile response time (tail latency)
* **Error Rate**: Percentage of failed requests (`error_rate < 1%`)
* **HPA Pod Count**: Observed replica count in Prometheus / Kubernetes during test execution
