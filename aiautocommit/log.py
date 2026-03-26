import os
import logging

from structlog_config import configure_logger


def setup_logging():
    # Map AIAUTOCOMMIT_LOG_PATH to PYTHON_LOG_PATH for structlog-config
    if log_path := os.environ.get("AIAUTOCOMMIT_LOG_PATH"):
        os.environ["PYTHON_LOG_PATH"] = log_path

    # Suppress verbose INFO logs from google_genai
    logging.getLogger("google_genai.models").setLevel(logging.WARNING)

    return configure_logger()


log = setup_logging()
