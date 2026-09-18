"""
Prediction API Endpoint Tests.
"""


from app.services.inference import get_model_service
from fastapi import status
from fastapi.testclient import TestClient


def test_predict_valid_features(client: TestClient, sample_features: list[float]):
    """Test standard single-instance prediction with valid 4 features."""
    payload = {"features": sample_features, "request_id": "test-req-001"}
    response = client.post("/predict", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Spec requirements: prediction (int), confidence (float), model_version (str)
    assert "prediction" in data
    assert isinstance(data["prediction"], int)
    assert 0 <= data["prediction"] <= 2

    assert "confidence" in data
    assert isinstance(data["confidence"], float)
    assert 0.0 <= data["confidence"] <= 1.0

    assert data["model_version"] == "v1.0.0"
    assert data["target_class"] in ["setosa", "versicolor", "virginica"]
    assert "inference_time_ms" in data
    assert data["inference_time_ms"] > 0

    # Header correlation
    assert "X-Request-ID" in response.headers


def test_predict_missing_features(client: TestClient):
    """Test validation failure when features field is missing."""
    response = client.post("/predict", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["error"] == "VALIDATION_ERROR"


def test_predict_too_few_features(client: TestClient):
    """Test validation failure when feature vector length is less than 4."""
    payload = {"features": [5.1, 3.5, 1.4]}
    response = client.post("/predict", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["error"] == "VALIDATION_ERROR"


def test_predict_too_many_features(client: TestClient):
    """Test validation failure when feature vector length exceeds 4."""
    payload = {"features": [5.1, 3.5, 1.4, 0.2, 9.9]}
    response = client.post("/predict", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["error"] == "VALIDATION_ERROR"


def test_predict_invalid_data_types(client: TestClient):
    """Test validation failure when strings or non-numeric types are supplied."""
    payload = {"features": [5.1, "invalid_string", 1.4, 0.2]}
    response = client.post("/predict", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_predict_when_model_unloaded(client: TestClient, sample_features: list[float]):
    """Test 503 response when prediction attempted on unloaded model."""
    model_service = get_model_service()
    original_state = model_service._is_loaded
    model_service._is_loaded = False

    try:
        response = client.post("/predict", json={"features": sample_features})
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    finally:
        model_service._is_loaded = original_state


def test_predict_batch_valid(client: TestClient, sample_batch_features: list[list[float]]):
    """Test batch prediction with multiple valid vectors."""
    payload = {"instances": sample_batch_features}
    response = client.post("/predict/batch", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["batch_size"] == 3
    assert len(data["predictions"]) == 3
    assert data["model_version"] == "v1.0.0"
    assert data["total_inference_time_ms"] > 0

    for item in data["predictions"]:
        assert isinstance(item["prediction"], int)
        assert 0.0 <= item["confidence"] <= 1.0


def test_predict_batch_invalid_item(client: TestClient):
    """Test batch prediction validation failure when one row is invalid."""
    payload = {
        "instances": [
            [5.1, 3.5, 1.4, 0.2],
            [6.0, 2.9],  # Invalid length
        ]
    }
    response = client.post("/predict/batch", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_predict_batch_when_model_unloaded(client: TestClient, sample_batch_features: list[list[float]]):
    """Test batch prediction returns 503 when model is unloaded."""
    model_service = get_model_service()
    original_state = model_service._is_loaded
    model_service._is_loaded = False

    try:
        response = client.post("/predict/batch", json={"instances": sample_batch_features})
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    finally:
        model_service._is_loaded = original_state


def test_predict_inference_exception_handling(client: TestClient, monkeypatch):
    """Test 500 status returned when model pipeline throws unexpected inference error."""
    model_service = get_model_service()

    def mock_predict(*args, **kwargs):
        raise RuntimeError("Simulated internal computational breakdown")

    monkeypatch.setattr(model_service.pipeline, "predict", mock_predict)
    response = client.post("/predict", json={"features": [5.1, 3.5, 1.4, 0.2]})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "error" in data


def test_predict_batch_exception_handling(client: TestClient, monkeypatch):
    """Test 500 status returned when batch inference fails."""
    model_service = get_model_service()

    def mock_predict(*args, **kwargs):
        raise RuntimeError("Simulated batch computational breakdown")

    monkeypatch.setattr(model_service.pipeline, "predict", mock_predict)
    response = client.post("/predict/batch", json={"instances": [[5.1, 3.5, 1.4, 0.2]]})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

