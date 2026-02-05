import subprocess
from unittest.mock import patch, MagicMock
import pytest
from aiautocommit.difftastic import get_difftastic_diff

@patch("shutil.which")
def test_get_difftastic_diff_binary_missing(mock_which):
    mock_which.return_value = None
    with pytest.raises(FileNotFoundError):
        get_difftastic_diff()

@patch("shutil.which")
@patch("aiautocommit.difftastic.run_command")
def test_get_difftastic_diff_success(mock_run, mock_which):
    mock_which.return_value = "/usr/local/bin/difft"
    mock_run.return_value = MagicMock(stdout="semantic diff", returncode=0)
    
    result = get_difftastic_diff(excluded_files=["*.log"])
    
    assert result == "semantic diff"
    # Check that excluded files were added to cmd
    args, kwargs = mock_run.call_args
    cmd = args[0]
    assert ":(exclude)***.log" in cmd
    # Check env vars
    assert kwargs["env"]["GIT_EXTERNAL_DIFF"] == "/usr/local/bin/difft"

@patch("shutil.which")
@patch("aiautocommit.difftastic.run_command")
def test_get_difftastic_diff_failure(mock_run, mock_which):
    mock_which.return_value = "/usr/local/bin/difft"
    mock_run.return_value = MagicMock(stdout="", stderr="error", returncode=2)
    
    with pytest.raises(subprocess.CalledProcessError):
        get_difftastic_diff()