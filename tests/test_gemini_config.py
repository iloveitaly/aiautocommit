from unittest.mock import MagicMock, patch

from pydantic_ai.models.google import GoogleModel

from aiautocommit import complete


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
