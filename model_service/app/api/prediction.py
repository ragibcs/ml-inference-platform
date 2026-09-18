"""
Prediction API Endpoints.

Handles single and batch ML inference requests with Pydantic validation and error handling.
"""

from fastapi import APIRouter, HTTPException, status

from app.logging import get_logger
from app.schemas.prediction import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    ErrorResponse,
    PredictionRequest,
    PredictionResponse,
)
from app.services.inference import (
    ModelInferenceError,
    ModelNotLoadedError,
    get_model_service,
)

logger = get_logger("model_service.api.prediction")
router = APIRouter(tags=["Inference"])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input features"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Inference computation error"},
        503: {"model": ErrorResponse, "description": "Model is not loaded"},
    },
    summary="Generate Model Prediction",
    description="Accepts 4 numerical feature inputs and returns model prediction class, confidence, and version.",
)
def predict(request: PredictionRequest) -> PredictionResponse:
    """Run model inference for a single input feature vector."""
    model_service = get_model_service()

    try:
        response = model_service.predict(request.features)
        logger.info(
            f"Prediction generated successfully: class={response.prediction} "
            f"confidence={response.confidence} version={response.model_version}",
            extra={
                "prediction": response.prediction,
                "confidence": response.confidence,
                "model_version": response.model_version,
                "request_id": request.request_id,
            },
        )
        return response

    except ModelNotLoadedError as e:
        logger.error(f"Inference rejected: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "MODEL_NOT_LOADED", "message": str(e)},
        )
    except ValueError as e:
        logger.warning(f"Feature validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_INPUT", "message": str(e)},
        )
    except ModelInferenceError as e:
        logger.exception("Inference execution error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "INFERENCE_FAILED", "message": str(e)},
        ) from e


@router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid batch payload"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Inference computation error"},
        503: {"model": ErrorResponse, "description": "Model is not loaded"},
    },
    summary="Generate Batch Model Predictions",
    description="Accepts multiple feature vectors for high-throughput batch inference.",
)
def predict_batch(request: BatchPredictionRequest) -> BatchPredictionResponse:
    """Run model inference across an array of feature vectors."""
    model_service = get_model_service()

    try:
        response = model_service.predict_batch(request.instances)
        logger.info(
            f"Batch inference completed for {response.batch_size} instances in "
            f"{response.total_inference_time_ms}ms"
        )
        return response

    except ModelNotLoadedError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "MODEL_NOT_LOADED", "message": str(e)},
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_INPUT", "message": str(e)},
        ) from e
    except Exception as e:
        logger.exception("Batch prediction execution error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "BATCH_INFERENCE_FAILED", "message": str(e)},
        ) from e
