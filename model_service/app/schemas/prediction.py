"""
Pydantic Request and Response Schemas.

Defines strict schema validation, field constraints, and OpenAPI schema documentation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class PredictionRequest(BaseModel):
    """Single instance prediction request schema."""

    features: List[float] = Field(
        ...,
        description="Array of 4 input numerical features: [sepal_length, sepal_width, petal_length, petal_width]",
        examples=[[5.1, 3.5, 1.4, 0.2]],
        min_length=4,
        max_length=4,
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Optional tracking request identifier",
        examples=["req-12345-abcde"],
    )

    @field_validator("features")
    @classmethod
    def validate_features(cls, v: List[float]) -> List[float]:
        """Ensure feature values are valid finite real numbers."""
        for i, val in enumerate(v):
            if val is None or not isinstance(val, (int, float)):
                raise ValueError(f"Feature at index {i} must be a valid number, got {val}")
            if val != val:  # NaN check
                raise ValueError(f"Feature at index {i} cannot be NaN")
            if val == float("inf") or val == float("-inf"):
                raise ValueError(f"Feature at index {i} cannot be infinite")
        return [float(x) for x in v]


class BatchPredictionRequest(BaseModel):
    """Batch prediction request schema."""

    instances: List[List[float]] = Field(
        ...,
        description="List of feature vectors for batch inference",
        examples=[
            [
                [5.1, 3.5, 1.4, 0.2],
                [6.2, 2.9, 4.3, 1.3],
                [7.3, 2.8, 6.4, 2.0],
            ]
        ],
        min_length=1,
        max_length=1000,
    )

    @field_validator("instances")
    @classmethod
    def validate_instances(cls, instances: List[List[float]]) -> List[List[float]]:
        """Validate each vector in the batch."""
        for row_idx, row in enumerate(instances):
            if len(row) != 4:
                raise ValueError(
                    f"Row {row_idx} has {len(row)} features; expected exactly 4"
                )
            for col_idx, val in enumerate(row):
                if val is None or not isinstance(val, (int, float)) or val != val:
                    raise ValueError(f"Invalid value at row {row_idx}, col {col_idx}")
        return instances


class PredictionResponse(BaseModel):
    """Single prediction response schema matching spec requirements."""

    prediction: int = Field(
        ...,
        description="Predicted class index (e.g. 0, 1, 2)",
        examples=[1],
    )
    confidence: float = Field(
        ...,
        description="Prediction confidence score between 0.0 and 1.0",
        ge=0.0,
        le=1.0,
        examples=[0.94],
    )
    model_version: str = Field(
        ...,
        description="Version tag of the deployed model",
        examples=["v1.0.0"],
    )
    target_class: Optional[str] = Field(
        default=None,
        description="Human-readable name of the predicted class",
        examples=["versicolor"],
    )
    inference_time_ms: Optional[float] = Field(
        default=None,
        description="Pure model inference duration in milliseconds",
        examples=[1.25],
    )


class BatchPredictionResponse(BaseModel):
    """Batch prediction response schema."""

    predictions: List[PredictionResponse] = Field(
        ..., description="List of individual prediction responses"
    )
    model_version: str = Field(..., description="Active model version tag")
    batch_size: int = Field(..., description="Total instances evaluated in batch")
    total_inference_time_ms: float = Field(
        ..., description="Total batch inference duration in milliseconds"
    )


class HealthResponse(BaseModel):
    """Liveness probe response schema."""

    status: str = Field(default="healthy", examples=["healthy"])


class ReadyResponse(BaseModel):
    """Readiness probe response schema."""

    status: str = Field(default="ready", examples=["ready"])
    model_version: str = Field(default="v1.0.0", examples=["v1.0.0"])
    model_loaded: bool = Field(default=True, examples=[True])
    dependencies_ready: bool = Field(default=True, examples=[True])
    details: Optional[Dict[str, Any]] = Field(default=None)


class ErrorResponse(BaseModel):
    """Standardized error response schema."""

    error: str = Field(..., description="Error category code", examples=["VALIDATION_ERROR"])
    message: str = Field(..., description="Descriptive human-readable error message")
    details: Optional[Any] = Field(default=None, description="Detailed validation breakdown")
