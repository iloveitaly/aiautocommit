from unittest.mock import patch, MagicMock
from aiautocommit import complete
from pydantic_ai.models.google import GoogleModel

@patch('aiautocommit.Agent')
def test_complete_gemini_thinking_config(MockAgent):
    mock_agent_instance = MockAgent.return_value
    # Mock agent.model to be a GoogleModel instance
    mock_agent_instance.model = MagicMock(spec=GoogleModel)
    mock_agent_instance.run_sync.return_value = MagicMock(output="test message")
    
    complete("test prompt", "test diff")
    
    # Verify that run_sync was called with model_settings
    args, kwargs = mock_agent_instance.run_sync.call_args
    assert 'model_settings' in kwargs
    model_settings = kwargs['model_settings']
    assert model_settings['google_thinking_config']['thinking_level'] == 'minimal'
    assert model_settings['google_thinking_config']['include_thoughts'] is True

@patch('aiautocommit.Agent')
def test_complete_non_gemini_no_config(MockAgent):
    mock_agent_instance = MockAgent.return_value
    # Mock agent.model to NOT be a GoogleModel instance
    mock_agent_instance.model = MagicMock() 
    mock_agent_instance.run_sync.return_value = MagicMock(output="test message")
    
    complete("test prompt", "test diff")
    
    args, kwargs = mock_agent_instance.run_sync.call_args
    assert kwargs.get('model_settings') is None
