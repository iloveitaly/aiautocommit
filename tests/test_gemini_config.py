from unittest.mock import MagicMock, patch

import pytest
from google.genai.types import ThinkingLevel
from pydantic_ai.models.google import GoogleModel

from aiautocommit import (
    UserFacingError,
    complete,
    default_google_thinking_level,
    resolve_google_thinking_level,
)


@pytest.mark.parametrize(
    ("model_name", "expected"),
    [
        ("google:gemini-3.5-flash-lite", "minimal"),
        ("google:gemini-3-flash", "minimal"),
        ("google:gemini-2.5-flash", "minimal"),
        ("google:gemini-3.7-flash", "low"),
        ("gemini-3.7-flash", "low"),
        ("google:gemini-3.7-pro", "low"),
        ("google:gemini-4-flash", "low"),
        ("google:gemini-3.8-flash", "low"),
        ("openai:gpt-4o", "minimal"),
    ],
)
def test_default_google_thinking_level(model_name, expected):
    assert default_google_thinking_level(model_name) == expected


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


@patch.dict("os.environ", {"AIAUTOCOMMIT_GOOGLE_THINKING_LEVEL": "high"})
@patch("aiautocommit.MODEL_NAME", "google:gemini-3.7-flash")
@patch("aiautocommit.Agent")
def test_complete_gemini_thinking_level_override(MockAgent):
    mock_agent_instance = MockAgent.return_value
    mock_agent_instance.model = MagicMock(spec=GoogleModel)
    mock_agent_instance.run_sync.return_value = MagicMock(output="test message")

    complete("test prompt", "test diff")

    args, kwargs = mock_agent_instance.run_sync.call_args
    model_settings = kwargs["model_settings"]
    assert (
        model_settings["google_thinking_config"]["thinking_level"] == ThinkingLevel.HIGH
    )


def test_resolve_google_thinking_level_invalid():
    with patch.dict("os.environ", {"AIAUTOCOMMIT_GOOGLE_THINKING_LEVEL": "extreme"}):
        with pytest.raises(UserFacingError, match="Invalid Google thinking level"):
            resolve_google_thinking_level("google:gemini-3.7-flash")


@patch("aiautocommit.Agent")
def test_complete_non_gemini_no_config(MockAgent):
    mock_agent_instance = MockAgent.return_value
    # Mock agent.model to NOT be a GoogleModel instance
    mock_agent_instance.model = MagicMock()
    mock_agent_instance.run_sync.return_value = MagicMock(output="test message")

    complete("test prompt", "test diff")

    args, kwargs = mock_agent_instance.run_sync.call_args
    assert kwargs.get("model_settings") is None
