"""
Health and Readiness Endpoint Tests.
"""

from fastapi import status
from fastapi.testclient import TestClient
from app.services.inference import get_model_service


def test_health_liveness_endpoint(client: TestClient):
    """Verify /health returns 200 OK and status healthy."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"


def test_ready_readiness_endpoint_when_loaded(client: TestClient):
    """Verify /ready returns 200 OK and model metadata when model is loaded."""
    response = client.get("/ready")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ready"
    assert data["model_loaded"] is True
    assert data["dependencies_ready"] is True
    assert data["model_version"] == "v1.0.0"
    assert "details" in data
    assert data["details"]["expected_features"] == 4


def test_ready_readiness_endpoint_when_unloaded(client: TestClient):
    """Verify /ready returns 503 Service Unavailable when model is unloaded."""
    model_service = get_model_service()
    # Temporarily unload
    original_state = model_service.is_loaded
    model_service._is_loaded = False

    try:
        response = client.get("/ready")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["status"] == "unready"
        assert data["model_loaded"] is False
    finally:
        model_service._is_loaded = original_state


def test_metrics_prometheus_endpoint(client: TestClient):
    """Verify /metrics returns Prometheus format text data."""
    # Send a request to generate metrics
    client.get("/health")

    response = client.get("/metrics")
    assert response.status_code == status.HTTP_200_OK
    assert "text/plain" in response.headers["content-type"]
    text = response.text
    assert "http_requests_total" in text
    assert "http_request_duration_seconds" in text
    assert "model_load_status" in text
