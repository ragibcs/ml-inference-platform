"""API Package."""

from app.api.health import router as health_router
from app.api.prediction import router as prediction_router

__all__ = ["health_router", "prediction_router"]
