"""Test aiautocommit."""

import aiautocommit


def test_import() -> None:
    """Test that the  can be imported."""
    assert isinstance(aiautocommit.__name__, str)
