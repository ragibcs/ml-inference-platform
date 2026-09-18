.PHONY: help install train-model test lint build docker-build docker-scan docker-run run k8s-dev k8s-prod load-smoke load-test load-stress promote clean

SHELL := /bin/bash
IMAGE_NAME ?= ml-inference-service
IMAGE_TAG ?= latest
PORT ?= 8000

help: ## Show this help message
	@echo "GitOps Scalable ML Inference Platform — Developer Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Create virtualenv and install all dependencies using uv/pip
	@echo "Setting up Python virtual environment..."
	uv venv --python 3.12 .venv || python3 -m venv .venv
	source .venv/bin/activate && uv pip install -r model_service/requirements.txt || pip install -r model_service/requirements.txt
	@echo "Dependencies installed successfully."

train-model: ## Train and serialize the scikit-learn model artifact
	@echo "Training model..."
	source .venv/bin/activate && PYTHONPATH=model_service python model_service/model/train.py

test: ## Run unit and integration tests with coverage enforcement (>80%)
	@echo "Executing pytest suite..."
	source .venv/bin/activate && PYTHONPATH=model_service pytest model_service/tests/ -v --cov=model_service/app --cov-fail-under=80 --cov-report=term-missing

lint: ## Run code style and linter checks
	@echo "Checking formatting and linting..."
	source .venv/bin/activate && python -m ruff check model_service/app model_service/tests || true

build: train-model docker-build ## Train model and build production Docker image

docker-build: ## Build production multi-stage non-root Docker container
	@echo "Building Docker image $(IMAGE_NAME):$(IMAGE_TAG)..."
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) model_service/

docker-scan: ## Scan Docker container for vulnerabilities using Trivy
	@echo "Scanning $(IMAGE_NAME):$(IMAGE_TAG) with Trivy..."
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image --severity HIGH,CRITICAL --ignore-unfixed $(IMAGE_NAME):$(IMAGE_TAG) || trivy image $(IMAGE_NAME):$(IMAGE_TAG)

docker-run: ## Run production Docker container locally
	@echo "Starting container on http://localhost:$(PORT)..."
	docker run --rm -p $(PORT):8000 $(IMAGE_NAME):$(IMAGE_TAG)

run: ## Start local development server with hot-reload
	@./scripts/local-dev.sh

k8s-dev: ## Apply Kustomize dev overlay to Kubernetes cluster
	@./scripts/deploy-dev.sh

k8s-prod: ## Apply Kustomize production overlay to Kubernetes cluster
	@kubectl apply -k k8s/overlays/production/ || echo "Run against active Kubernetes cluster"

load-smoke: ## Run k6 smoke test (10 VUs, 1 min)
	@k6 run -e TARGET_URL=http://localhost:$(PORT) load_tests/k6/smoke.js || docker run --rm -i --net="host" -v $$(pwd)/load_tests/k6:/scripts grafana/k6:latest run -e TARGET_URL=http://localhost:$(PORT) /scripts/smoke.js

load-test: ## Run k6 sustained load test (50-100 VUs)
	@k6 run -e TARGET_URL=http://localhost:$(PORT) load_tests/k6/load.js || docker run --rm -i --net="host" -v $$(pwd)/load_tests/k6:/scripts grafana/k6:latest run -e TARGET_URL=http://localhost:$(PORT) /scripts/load.js

load-stress: ## Run k6 stress test (10-200 VUs to trigger HPA scaling)
	@k6 run -e TARGET_URL=http://localhost:$(PORT) load_tests/k6/stress.js || docker run --rm -i --net="host" -v $$(pwd)/load_tests/k6:/scripts grafana/k6:latest run -e TARGET_URL=http://localhost:$(PORT) /scripts/stress.js

promote: ## Promote image tag to environment (e.g. make promote ENV=production TAG=v1.0.1)
	@./scripts/promote.sh $(ENV) $(TAG) false

clean: ## Clean cache, bytecode, and test coverage artifacts
	@rm -rf .pytest_cache htmlcov .coverage
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
