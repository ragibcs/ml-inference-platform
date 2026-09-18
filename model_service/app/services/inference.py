"""
Machine Learning Inference Service.

Handles model loading, validation, batch and single predictions, and performance telemetry.
"""

import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.config import get_settings
from app.logging import get_logger
from app.metrics import (
    MODEL_INFERENCE_DURATION_SECONDS,
    MODEL_LOAD_STATUS,
    PREDICTION_ERRORS_TOTAL,
    PREDICTIONS_TOTAL,
)
from app.schemas.prediction import BatchPredictionResponse, PredictionResponse

logger = get_logger("model_service.inference")


class ModelNotLoadedError(Exception):
    """Raised when an inference operation is attempted before the model is loaded."""


class ModelInferenceError(Exception):
    """Raised when an error occurs during model execution."""


class ModelService:
    """Manages the lifecycle and execution of the machine learning model."""

    def __init__(self, model_path: str | None = None):
        self.settings = get_settings()
        self.model_path = model_path or self.settings.model_path
        self.pipeline: Any | None = None
        self.model_version: str = self.settings.model_version
        self.feature_names: list[str] = []
        self.expected_features_count: int = self.settings.expected_features_count
        self.target_names: list[str] = []
        self.metadata: dict[str, Any] = {}
        self._is_loaded: bool = False

    @property
    def is_loaded(self) -> bool:
        """Check if model is currently loaded and ready."""
        return self._is_loaded and self.pipeline is not None

    def load_model(self) -> None:
        """Load the model artifact from disk into memory."""
        path_obj = Path(self.model_path)
        candidates = [
            path_obj,
            Path.cwd() / self.model_path,
            Path(__file__).resolve().parent.parent / self.model_path,
            Path(__file__).resolve().parent.parent.parent / self.model_path,
            Path("/app") / self.model_path,
        ]
        resolved_path: Path | None = None
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                resolved_path = candidate
                break

        if resolved_path is None:
            MODEL_LOAD_STATUS.labels(model_version=self.model_version).set(0)
            logger.error(f"Model artifact file not found at: {self.model_path}")
            raise FileNotFoundError(f"Model artifact not found at {self.model_path}")

        try:
            logger.info(f"Loading model artifact from {resolved_path.resolve()}...")
            artifact = joblib.load(resolved_path)

            if isinstance(artifact, dict) and "pipeline" in artifact:
                self.pipeline = artifact["pipeline"]
                self.model_version = artifact.get("model_version", self.settings.model_version)
                self.feature_names = artifact.get("feature_names", [])
                self.expected_features_count = artifact.get(
                    "expected_features_count", self.settings.expected_features_count
                )
                self.target_names = artifact.get("target_names", [])
                self.metadata = artifact.get("metrics", {})
            else:
                self.pipeline = artifact
                self.target_names = ["class_0", "class_1", "class_2"]

            self._is_loaded = True
            MODEL_LOAD_STATUS.labels(model_version=self.model_version).set(1)
            logger.info(
                f"Model successfully loaded. Version: {self.model_version}, "
                f"Features count: {self.expected_features_count}, Classes: {self.target_names}"
            )
        except Exception as e:
            self._is_loaded = False
            MODEL_LOAD_STATUS.labels(model_version=self.model_version).set(0)
            logger.exception("Failed to load model artifact")
            raise RuntimeError(f"Could not load model artifact: {e}") from e

    def unload_model(self) -> None:
        """Unload model artifact and reset memory references."""
        self.pipeline = None
        self._is_loaded = False
        MODEL_LOAD_STATUS.labels(model_version=self.model_version).set(0)
        logger.info("Model unloaded successfully.")

    def predict(self, features: list[float]) -> PredictionResponse:
        """
        Run inference on a single feature vector.

        Args:
            features: List of 4 numerical float values.

        Returns:
            PredictionResponse object.
        """
        if not self.is_loaded:
            PREDICTION_ERRORS_TOTAL.labels(
                model_version=self.model_version, error_type="model_not_loaded"
            ).inc()
            raise ModelNotLoadedError("Model is not loaded. Cannot perform inference.")

        if len(features) != self.expected_features_count:
            PREDICTION_ERRORS_TOTAL.labels(
                model_version=self.model_version, error_type="invalid_feature_count"
            ).inc()
            raise ValueError(
                f"Expected {self.expected_features_count} features, received {len(features)}"
            )

        x_input = np.array([features], dtype=np.float64)

        start_time = time.perf_counter()
        try:
            pred_array = self.pipeline.predict(x_input)
            predicted_class_idx = int(pred_array[0])

            # Calculate prediction confidence if predict_proba is available
            confidence = 1.0
            if hasattr(self.pipeline, "predict_proba"):
                proba_array = self.pipeline.predict_proba(x_input)
                confidence = float(proba_array[0][predicted_class_idx])

            duration_s = time.perf_counter() - start_time
            duration_ms = duration_s * 1000.0

            # Record Prometheus metrics
            MODEL_INFERENCE_DURATION_SECONDS.labels(
                model_version=self.model_version
            ).observe(duration_s)

            target_class_str = (
                self.target_names[predicted_class_idx]
                if predicted_class_idx < len(self.target_names)
                else f"class_{predicted_class_idx}"
            )

            PREDICTIONS_TOTAL.labels(
                model_version=self.model_version,
                predicted_class=str(target_class_str),
            ).inc()

            return PredictionResponse(
                prediction=predicted_class_idx,
                confidence=round(confidence, 4),
                model_version=self.model_version,
                target_class=str(target_class_str),
                inference_time_ms=round(duration_ms, 3),
            )

        except Exception as e:
            PREDICTION_ERRORS_TOTAL.labels(
                model_version=self.model_version, error_type="inference_error"
            ).inc()
            logger.exception("Inference execution failed")
            raise ModelInferenceError(f"Prediction execution failed: {e}") from e

    def predict_batch(self, instances: list[list[float]]) -> BatchPredictionResponse:
        """
        Run inference on a batch of feature vectors.

        Args:
            instances: List of feature vectors.

        Returns:
            BatchPredictionResponse containing individual responses.
        """
        if not self.is_loaded:
            PREDICTION_ERRORS_TOTAL.labels(
                model_version=self.model_version, error_type="model_not_loaded"
            ).inc()
            raise ModelNotLoadedError("Model is not loaded. Cannot perform inference.")

        start_total = time.perf_counter()
        predictions: list[PredictionResponse] = []

        for row in instances:
            pred = self.predict(row)
            predictions.append(pred)

        total_duration_ms = (time.perf_counter() - start_total) * 1000.0

        return BatchPredictionResponse(
            predictions=predictions,
            model_version=self.model_version,
            batch_size=len(instances),
            total_inference_time_ms=round(total_duration_ms, 3),
        )


# Singleton instance
_model_service_instance: ModelService | None = None


def get_model_service() -> ModelService:
    """Retrieve or initialize singleton ModelService."""
    global _model_service_instance
    if _model_service_instance is None:
        _model_service_instance = ModelService()
    return _model_service_instance
