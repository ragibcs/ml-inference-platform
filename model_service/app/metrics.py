"""
Prometheus Metrics Instrumentation Module.

Exposes standard RED (Rate, Errors, Duration) metrics and ML inference specific telemetry.
"""

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

__all__ = [
    "ACTIVE_REQUESTS",
    "CONTENT_TYPE_LATEST",
    "HTTP_REQUESTS_TOTAL",
    "HTTP_REQUEST_DURATION_SECONDS",
    "MODEL_INFERENCE_DURATION_SECONDS",
    "MODEL_LOAD_STATUS",
    "PREDICTIONS_TOTAL",
    "PREDICTION_ERRORS_TOTAL",
    "get_latest_metrics",
]

# Standard HTTP metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total count of HTTP requests processed by endpoint and status code.",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "endpoint"],
    buckets=(
        0.002,
        0.005,
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
    ),
)

ACTIVE_REQUESTS = Gauge(
    "active_requests",
    "Number of concurrent requests currently being processed.",
)

# Model specific metrics
MODEL_INFERENCE_DURATION_SECONDS = Histogram(
    "model_inference_duration_seconds",
    "Pure machine learning model inference duration in seconds.",
    ["model_version"],
    buckets=(
        0.0005,
        0.001,
        0.002,
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
    ),
)

PREDICTIONS_TOTAL = Counter(
    "predictions_total",
    "Total count of ML model predictions generated.",
    ["model_version", "predicted_class"],
)

PREDICTION_ERRORS_TOTAL = Counter(
    "prediction_errors_total",
    "Total count of prediction failures or validation errors.",
    ["model_version", "error_type"],
)

MODEL_LOAD_STATUS = Gauge(
    "model_load_status",
    "Indicates if the ML model is currently loaded in memory (1=loaded, 0=unloaded).",
    ["model_version"],
)


def get_latest_metrics() -> bytes:
    """Generate latest metrics from Prometheus collector registry."""
    return generate_latest(REGISTRY)
