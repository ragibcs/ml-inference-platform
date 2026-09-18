"""
Model Service Unit Tests.
"""

import pytest
from app.schemas.prediction import BatchPredictionResponse, PredictionResponse
from app.services.inference import (
    ModelNotLoadedError,
    ModelService,
)


def test_model_service_load_and_predict(sample_features):
    """Test loading model and running prediction."""
    service = ModelService()
    service.load_model()

    assert service.is_loaded is True
    assert service.expected_features_count == 4
    assert len(service.target_names) == 3

    result = service.predict(sample_features)
    assert isinstance(result, PredictionResponse)
    assert result.prediction == 0  # Iris-setosa
    assert result.target_class == "setosa"
    assert result.confidence >= 0.80
    assert result.model_version == "v1.0.0"


def test_model_service_invalid_feature_count(model_service: ModelService):
    """Test ValueError raised on incorrect feature count."""
    with pytest.raises(ValueError, match="Expected 4 features"):
        model_service.predict([1.0, 2.0, 3.0])


def test_model_service_unloaded_raises_error():
    """Test ModelNotLoadedError raised when inference run without load."""
    service = ModelService()
    service.unload_model()
    assert service.is_loaded is False

    with pytest.raises(ModelNotLoadedError):
        service.predict([5.1, 3.5, 1.4, 0.2])


def test_model_service_missing_file():
    """Test FileNotFoundError raised on invalid model path."""
    service = ModelService(model_path="non_existent/path/model.joblib")
    with pytest.raises(FileNotFoundError):
        service.load_model()


def test_model_service_batch_predict(model_service: ModelService, sample_batch_features):
    """Test batch prediction produces correct batch output."""
    result = model_service.predict_batch(sample_batch_features)
    assert isinstance(result, BatchPredictionResponse)
    assert result.batch_size == 3
    assert len(result.predictions) == 3
    assert result.predictions[0].target_class == "setosa"
    assert result.predictions[1].target_class == "versicolor"
    assert result.predictions[2].target_class == "virginica"
