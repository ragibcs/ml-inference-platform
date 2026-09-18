"""
Pytest Fixtures and Global Test Configuration.
"""

import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure model_service is in sys.path
MODEL_SERVICE_DIR = Path(__file__).resolve().parent.parent
if str(MODEL_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_SERVICE_DIR))

# Ensure model artifact exists for tests
MODEL_PATH = MODEL_SERVICE_DIR / "model" / "model.joblib"
if not MODEL_PATH.exists():
    from model.train import train_and_save_model
    train_and_save_model(output_path=str(MODEL_PATH))

from app.main import app
from app.services.inference import ModelService, get_model_service


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """Yield initialized TestClient with lifespan context."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_features() -> list[float]:
    """Provide standard 4-feature test vector (Iris Setosa)."""
    return [5.1, 3.5, 1.4, 0.2]


@pytest.fixture
def sample_batch_features() -> list[list[float]]:
    """Provide standard multi-vector batch test payload."""
    return [
        [5.1, 3.5, 1.4, 0.2],  # Setosa
        [6.0, 2.9, 4.5, 1.5],  # Versicolor
        [6.9, 3.1, 5.4, 2.1],  # Virginica
    ]


@pytest.fixture
def model_service() -> ModelService:
    """Provide active ModelService instance."""
    service = get_model_service()
    if not service.is_loaded:
        service.load_model()
    return service
