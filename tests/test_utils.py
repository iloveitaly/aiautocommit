import subprocess
import pytest
from aiautocommit.utils import run_command

def test_run_command_success():
    result = run_command(["echo", "hello"])
    assert result.stdout.strip() == "hello"
    assert result.returncode == 0

def test_run_command_failure():

    with pytest.raises(subprocess.CalledProcessError):

        run_command(["ls", "/non-existent-directory-12345"], check=True)
