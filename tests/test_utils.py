import subprocess
import pytest
from aiautocommit.utils import get_current_branch, run_command


def test_run_command_success():
    result = run_command(["echo", "hello"])
    assert result.stdout.strip() == "hello"
    assert result.returncode == 0


def test_run_command_failure():

    with pytest.raises(subprocess.CalledProcessError):
        run_command(["ls", "/non-existent-directory-12345"], check=True)


def test_get_current_branch():
    branch = get_current_branch()
    # In a git repo, this should return something
    assert branch is not None
