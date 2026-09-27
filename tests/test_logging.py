import logging
import os
from unittest.mock import patch

from aiautocommit import update_env_variables
from aiautocommit.log import ignore_log_level_env, setup_logging


def test_plain_log_level_ignored():
    with patch.dict(
        os.environ,
        {"LOG_LEVEL": "DEBUG"},
        clear=True,
    ):
        setup_logging()
        assert logging.getLogger().level == logging.INFO
        assert os.environ.get("LOG_LEVEL") is None


def test_aiautocommit_log_level_respected():
    with patch.dict(
        os.environ,
        {"AIAUTOCOMMIT_LOG_LEVEL": "DEBUG"},
        clear=True,
    ):
        setup_logging()
        assert logging.getLogger().level == logging.DEBUG
        assert os.environ.get("LOG_LEVEL") == "DEBUG"


def test_aiautocommit_log_level_precedence_over_plain():
    with patch.dict(
        os.environ,
        {"LOG_LEVEL": "DEBUG", "AIAUTOCOMMIT_LOG_LEVEL": "WARNING"},
        clear=True,
    ):
        setup_logging()
        assert logging.getLogger().level == logging.WARNING
        assert os.environ.get("LOG_LEVEL") == "WARNING"


def test_update_env_variables_skips_log_level():
    with patch.dict(
        os.environ,
        {"AIAUTOCOMMIT_LOG_LEVEL": "DEBUG"},
        clear=True,
    ):
        update_env_variables()
        assert os.environ.get("LOG_LEVEL") is None


def test_ignore_log_level_env():
    with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}, clear=True):
        ignore_log_level_env()
        assert "LOG_LEVEL" not in os.environ

    with patch.dict(
        os.environ,
        {"LOG_LEVEL": "INFO", "AIAUTOCOMMIT_LOG_LEVEL": "DEBUG"},
        clear=True,
    ):
        ignore_log_level_env()
        assert os.environ.get("LOG_LEVEL") == "DEBUG"
