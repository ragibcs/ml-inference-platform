"""
Health and Readiness Probes API.

Implements Kubernetes liveness (/health) and readiness (/ready) probe endpoints.
"""

from fastapi import APIRouter, Response, status

from app.config import get_settings
from app.schemas.prediction import HealthResponse, ReadyResponse
from app.services.inference import get_model_service

router = APIRouter(tags=["Health & Probes"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Kubernetes liveness probe endpoint. Verifies the HTTP process is responsive.",
)
def get_health() -> HealthResponse:
    """Return healthy status for liveness check."""
    return HealthResponse(status="healthy")


@router.get(
    "/ready",
    response_model=ReadyResponse,
    status_code=status.HTTP_200_OK,
    responses={
        503: {
            "model": ReadyResponse,
            "description": "Service is unavailable or model artifact is not loaded.",
        }
    },
    summary="Readiness Probe",
    description="Kubernetes readiness probe endpoint. Verifies model artifact is loaded and ready for inference.",
)
def get_ready(response: Response) -> ReadyResponse:
    """
    Check if application and ML model are ready to receive traffic.
    Returns 200 if loaded, 503 if not ready.
    """
    settings = get_settings()
    model_service = get_model_service()

    is_model_ready = model_service.is_loaded

    if not is_model_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadyResponse(
            status="unready",
            model_version=settings.model_version,
            model_loaded=False,
            dependencies_ready=False,
            details={"error": "Model artifact is not loaded in memory"},
        )

    return ReadyResponse(
        status="ready",
        model_version=model_service.model_version,
        model_loaded=True,
        dependencies_ready=True,
        details={
            "expected_features": model_service.expected_features_count,
            "classes": model_service.target_names,
            "model_path": model_service.model_path,
        },
    )
