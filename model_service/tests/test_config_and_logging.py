"""
Configuration and Structured Logging Unit Tests.
"""

import json
import logging

from app.config import Settings
from app.logging import JSONFormatter, get_logger, setup_logging


def test_settings_defaults():
    """Verify application configuration default values."""
    settings = Settings()
    assert settings.app_name == "ml-inference-platform"
    assert settings.port == 8000
    assert settings.expected_features_count == 4
    assert settings.model_version == "v1.0.0"


def test_json_formatter():
    """Verify JSON log formatter outputs valid parseable JSON with required keys."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test log message %s",
        args=("arg1",),
        exc_info=None,
    )
    record.request_id = "req-test-123"
    record.prediction = 1

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test log message arg1"
    assert parsed["logger"] == "test_logger"
    assert parsed["request_id"] == "req-test-123"
    assert parsed["prediction"] == 1
    assert "timestamp" in parsed


def test_setup_logging_text_and_json():
    """Verify setup_logging configures root logger without exceptions."""
    setup_logging(log_level="DEBUG", log_format="text")
    logger = get_logger("sample_text")
    assert logger is not None

    setup_logging(log_level="INFO", log_format="json")
    logger_json = get_logger("sample_json")
    assert logger_json is not None
