import sys
import os
from unittest.mock import patch
from importlib.metadata import PackageNotFoundError
from pathlib import Path


def test_version_unknown():
    if "aiautocommit" in sys.modules:
        del sys.modules["aiautocommit"]

    with patch("importlib.metadata.version", side_effect=PackageNotFoundError):
        import aiautocommit

        assert aiautocommit.__version__ == "unknown"

    if "aiautocommit" in sys.modules:
        del sys.modules["aiautocommit"]
    import aiautocommit


def test_config_paths_env():
    if "aiautocommit" in sys.modules:
        del sys.modules["aiautocommit"]

    with patch.dict(os.environ, {"AIAUTOCOMMIT_CONFIG": "/tmp/custom_config"}):
        import aiautocommit

        assert Path("/tmp/custom_config") in aiautocommit.CONFIG_PATHS

    if "aiautocommit" in sys.modules:
        del sys.modules["aiautocommit"]
    import aiautocommit


def test_logging_suppression():
    if "aiautocommit" in sys.modules:
        del sys.modules["aiautocommit"]

    with patch.dict(os.environ, {}, clear=True):
        with patch("logging.getLogger") as mock_get_logger:
            import aiautocommit  # noqa: F401

            assert mock_get_logger.called

    if "aiautocommit" in sys.modules:
        del sys.modules["aiautocommit"]


def test_logging_not_suppressed():
    if "aiautocommit" in sys.modules:
        del sys.modules["aiautocommit"]

    with patch.dict(os.environ, {"AIAUTOCOMMIT_LOG_PATH": "/tmp/test.log"}):
        with patch("logging.getLogger") as mock_get_logger:
            import aiautocommit  # noqa: F401

            assert not mock_get_logger.called

    if "aiautocommit" in sys.modules:
        del sys.modules["aiautocommit"]


def test_log_path_env():
    if "aiautocommit.log" in sys.modules:
        del sys.modules["aiautocommit.log"]

    with patch.dict(os.environ, {"AIAUTOCOMMIT_LOG_PATH": "/tmp/test.log"}):
        import aiautocommit.log  # noqa: F401

        assert os.environ["PYTHON_LOG_PATH"] == "/tmp/test.log"

    if "aiautocommit.log" in sys.modules:
        del sys.modules["aiautocommit.log"]
