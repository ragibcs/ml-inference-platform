"""
Master FastAPI Application Entrypoint.

Configures middleware, lifecycle events, global exception handling, routes, and OpenAPI metadata.
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.prediction import router as prediction_router
from app.config import get_settings
from app.logging import get_logger, setup_logging
from app.metrics import (
    ACTIVE_REQUESTS,
    CONTENT_TYPE_LATEST,
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
    get_latest_metrics,
)
from app.services.inference import get_model_service

# Initialize settings and logger
settings = get_settings()
setup_logging(log_level=settings.log_level, log_format=settings.log_format)
logger = get_logger("model_service.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifecycle manager.
    Loads ML model artifact on startup and manages graceful shutdown.
    """
    logger.info(
        f"Starting {settings.app_name} (version={settings.app_version}, env={settings.app_env})..."
    )
    model_service = get_model_service()
    try:
        model_service.load_model()
        logger.info("Model service initialized and ready to serve traffic.")
    except Exception as e:
        logger.error(
            f"Startup warning: Model could not be pre-loaded: {e}. "
            "Readiness probe will report unready until resolved."
        )

    yield

    logger.info("Initiating graceful shutdown sequence...")
    model_service.unload_model()
    logger.info("Application shutdown complete.")


# Initialize FastAPI application instance
app = FastAPI(
    title="GitOps ML Inference Platform API",
    description=(
        "Production-grade Machine Learning Inference API featuring automated GitOps delivery, "
        "Prometheus & Grafana observability, Horizontal Pod Autoscaling, and Kubernetes readiness/liveness probes."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# HTTP Request Tracking & Observability Middleware
@app.middleware("http")
async def metrics_and_logging_middleware(request: Request, call_next):
    """
    Tracks request latency, status codes, active concurrency, and injects correlation IDs.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    endpoint = request.url.path
    method = request.method

    ACTIVE_REQUESTS.inc()
    start_time = time.perf_counter()

    try:
        response: Response = await call_next(request)
        status_code = str(response.status_code)
    except Exception as exc:
        status_code = "500"
        logger.exception(f"Unhandled exception during request processing: {exc}")
        raise exc from None
    finally:
        duration_s = time.perf_counter() - start_time
        ACTIVE_REQUESTS.dec()

        # Record metrics excluding metrics endpoint itself to avoid recursion noise
        if endpoint != "/metrics":
            HTTP_REQUESTS_TOTAL.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method, endpoint=endpoint
            ).observe(duration_s)

    response.headers["X-Request-ID"] = request_id
    return response


# Global Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Format HTTPException details consistently."""
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP_ERROR", "message": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format Pydantic validation errors into consistent JSON response."""
    errors = exc.errors()
    clean_errors = []
    for err in errors:
        loc = " -> ".join(str(x) for x in err.get("loc", []))
        clean_errors.append({"field": loc, "issue": err.get("msg")})

    logger.warning(
        f"Validation error on {request.method} {request.url.path}: {clean_errors}",
        extra={"request_id": getattr(request.state, "request_id", None)},
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "The request payload failed input schema validation.",
            "details": clean_errors,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected server errors gracefully."""
    logger.exception(
        f"Internal server error processing {request.method} {request.url.path}: {exc}"
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected server error occurred during request execution.",
        },
    )


# Expose Prometheus Metrics Endpoint
@app.get(
    "/metrics",
    summary="Prometheus Metrics",
    description="Exposes application and infrastructure metrics in Prometheus text format.",
    tags=["Observability"],
)
def get_metrics() -> Response:
    """Expose application metrics in standard OpenMetrics format."""
    return Response(
        content=get_latest_metrics(),
        media_type=CONTENT_TYPE_LATEST,
    )


# Include Sub-Routers
app.include_router(health_router)
app.include_router(prediction_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=(settings.app_env.lower() == "dev"),
    )
