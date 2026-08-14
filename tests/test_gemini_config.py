from unittest.mock import MagicMock, patch

import pytest
from google.genai.types import ThinkingLevel
from pydantic_ai.models.google import GoogleModel

from aiautocommit import complete, google_thinking_level


@pytest.mark.parametrize(
    ("model_name", "expected"),
    [
        ("google:gemini-3.5-flash-lite", ThinkingLevel.MINIMAL),
        ("google:gemini-3-flash", ThinkingLevel.MINIMAL),
        ("google:gemini-2.5-flash", ThinkingLevel.MINIMAL),
        ("google:gemini-3.7-flash", ThinkingLevel.LOW),
        ("gemini-3.7-flash", ThinkingLevel.LOW),
        ("google:gemini-3.7-pro", ThinkingLevel.LOW),
        ("google:gemini-4-flash", ThinkingLevel.LOW),
        ("google:gemini-3.8-flash", ThinkingLevel.LOW),
    ],
)
def test_google_thinking_level(model_name, expected):
    assert google_thinking_level(model_name) == expected


@patch("aiautocommit.MODEL_NAME", "google:gemini-3.5-flash-lite")
@patch("aiautocommit.Agent")
def test_complete_gemini_thinking_config(MockAgent):
    mock_agent_instance = MockAgent.return_value
    # Mock agent.model to be a GoogleModel instance
    mock_agent_instance.model = MagicMock(spec=GoogleModel)
    mock_agent_instance.run_sync.return_value = MagicMock(output="test message")

    complete("test prompt", "test diff")

    # Verify that run_sync was called with model_settings
    args, kwargs = mock_agent_instance.run_sync.call_args
    assert "model_settings" in kwargs
    model_settings = kwargs["model_settings"]
    assert (
        model_settings["google_thinking_config"]["thinking_level"]
        == ThinkingLevel.MINIMAL
    )
    assert model_settings["google_thinking_config"]["include_thoughts"] is True


@patch("aiautocommit.MODEL_NAME", "google:gemini-3.7-flash")
@patch("aiautocommit.Agent")
def test_complete_gemini_37_uses_low_thinking(MockAgent):
    mock_agent_instance = MockAgent.return_value
    mock_agent_instance.model = MagicMock(spec=GoogleModel)
    mock_agent_instance.run_sync.return_value = MagicMock(output="test message")

    complete("test prompt", "test diff")

    args, kwargs = mock_agent_instance.run_sync.call_args
    model_settings = kwargs["model_settings"]
    assert (
        model_settings["google_thinking_config"]["thinking_level"] == ThinkingLevel.LOW
    )


@patch("aiautocommit.Agent")
def test_complete_non_gemini_no_config(MockAgent):
    mock_agent_instance = MockAgent.return_value
    # Mock agent.model to NOT be a GoogleModel instance
    mock_agent_instance.model = MagicMock()
    mock_agent_instance.run_sync.return_value = MagicMock(output="test message")

    complete("test prompt", "test diff")

    args, kwargs = mock_agent_instance.run_sync.call_args
    assert kwargs.get("model_settings") is None
