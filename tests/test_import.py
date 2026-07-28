"""Test aiautocommit."""

import aiautocommit


def test_import() -> None:
    """Test that the  can be imported."""
    assert isinstance(aiautocommit.__name__, str)


def test_default_model() -> None:
    """Test that the default model is stable."""
    assert aiautocommit.DEFAULT_MODEL_NAME == "google:gemini-3.5-flash-lite"


def test_version() -> None:
    """Test that the version is available."""
    assert isinstance(aiautocommit.__version__, str)
