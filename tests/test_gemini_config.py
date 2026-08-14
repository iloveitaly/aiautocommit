from unittest.mock import MagicMock, patch

import pytest
from pydantic_ai.models.google import GoogleModel

from aiautocommit import complete, lowest_thinking_effort


@pytest.mark.parametrize(
    ("model_name", "expected"),
    [
        ("google:gemini-3.5-flash-lite", "minimal"),
        ("gemini-3.5-flash-lite", "minimal"),
        ("google:gemini-3-flash", "minimal"),
        ("google:gemini-2.5-flash", "minimal"),
        ("google:gemini-3.7-flash", "low"),
        ("gemini-3.7-flash", "low"),
        ("google:gemini-3.7-pro", "low"),
        ("google:gemini-4-flash", "low"),
        ("google:gemini-3.8-flash", "low"),
    ],
)
def test_lowest_thinking_effort(model_name, expected):
    assert lowest_thinking_effort(model_name) == expected


@patch("aiautocommit.MODEL_NAME", "google:gemini-3.5-flash-lite")
@patch("aiautocommit.Agent")
def test_complete_gemini_thinking_config(MockAgent):
    mock_agent_instance = MockAgent.return_value
    mock_agent_instance.model = MagicMock(spec=GoogleModel)
    mock_agent_instance.model.model_name = "gemini-3.5-flash-lite"
    mock_agent_instance.run_sync.return_value = MagicMock(output="test message")

    complete("test prompt", "test diff")

    args, kwargs = mock_agent_instance.run_sync.call_args
    assert kwargs["model_settings"]["thinking"] == "minimal"


@patch("aiautocommit.MODEL_NAME", "google:gemini-3.7-flash")
@patch("aiautocommit.Agent")
def test_complete_gemini_37_uses_low_thinking(MockAgent):
    mock_agent_instance = MockAgent.return_value
    mock_agent_instance.model = MagicMock(spec=GoogleModel)
    mock_agent_instance.model.model_name = "gemini-3.7-flash"
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
