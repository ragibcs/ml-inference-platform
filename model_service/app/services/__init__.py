"""Services Package."""

from app.services.inference import ModelService, get_model_service

__all__ = ["ModelService", "get_model_service"]
