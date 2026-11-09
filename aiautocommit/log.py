import logging
import os
import sys

import structlog
from structlog_config import configure_logger

DEFAULT_LOG_LEVEL = "WARNING"


def ignore_log_level_env():
    """
    Ensure structlog-config only respects AIAUTOCOMMIT_LOG_LEVEL, not a generic LOG_LEVEL.
    Defaults to WARNING when AIAUTOCOMMIT_LOG_LEVEL is not set.
    """
    if level := os.environ.get("AIAUTOCOMMIT_LOG_LEVEL"):
        os.environ["LOG_LEVEL"] = level
    else:
        os.environ["LOG_LEVEL"] = DEFAULT_LOG_LEVEL


def setup_logging():
    # Map AIAUTOCOMMIT_LOG_PATH to PYTHON_LOG_PATH for structlog-config
    if log_path := os.environ.get("AIAUTOCOMMIT_LOG_PATH"):
        os.environ["PYTHON_LOG_PATH"] = log_path

    # Suppress verbose INFO and AFC advisory WARNING logs from google_genai
    logging.getLogger("google_genai.models").setLevel(logging.ERROR)

    # Suppress noisy HTTP request logging:
    # - httpx is pulled in by google-genai
    # - httpx2 is used by pydantic-ai-slim, openai, anthropic, and genai-prices
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpx2").setLevel(logging.WARNING)

    ignore_log_level_env()

    return configure_logger(
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr)
    )


log = setup_logging()
