import os
from unittest.mock import MagicMock, patch

import pydantic_ai
from pydantic_ai.models.google import GoogleModel

from aiautocommit import complete


def test_pydantic_ai_banner_disabled(monkeypatch):
    from pydantic_ai._display import _banner_suppressed

    assert os.environ.get("PYDANTIC_AI_NO_BANNER") == "1"
    assert pydantic_ai.BANNER_ENABLED is False

    monkeypatch.delenv("PYTEST_VERSION", raising=False)
    monkeypatch.delenv("CI", raising=False)
    assert _banner_suppressed() is True


@patch("aiautocommit.Agent")
def test_complete_gemini_thinking_config(MockAgent):
    mock_agent_instance = MockAgent.return_value
    mock_agent_instance.model = MagicMock(spec=GoogleModel)
    mock_agent_instance.run_sync.return_value = MagicMock(output="test message")

    complete("test prompt", "test diff")

    args, kwargs = mock_agent_instance.run_sync.call_args
    assert kwargs["model_settings"]["thinking"] == "low"


@patch("aiautocommit.Agent")
def test_complete_non_gemini_no_config(MockAgent):
    mock_agent_instance = MockAgent.return_value
    mock_agent_instance.model = MagicMock()
    mock_agent_instance.run_sync.return_value = MagicMock(output="test message")

    complete("test prompt", "test diff")

    args, kwargs = mock_agent_instance.run_sync.call_args
    assert kwargs.get("model_settings") is None
