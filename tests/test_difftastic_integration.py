import shutil
import pytest
from unittest.mock import patch
from click.testing import CliRunner
from aiautocommit import main
from tests.utils import GitTestMixin

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def git_repo(runner):
    with runner.isolated_filesystem():
        mixin = GitTestMixin()
        mixin.init_repo()
        yield mixin

def test_difftastic_integration(runner, git_repo):
    # Verify difft is installed as per the user's instructions
    if not shutil.which("difft"):
        pytest.fail("difftastic (difft) is required but not found in PATH")

    # Create and stage a file
    git_repo.create_file("test.py", "def main():\n    print('hello')\n")
    git_repo.git_add("test.py")
    git_repo.git_commit("initial")

    # Modify the file to create a diff
    git_repo.create_file("test.py", "def main():\n    print('hello world')\n")
    git_repo.git_add("test.py")

    # Run aiautocommit with --difftastic
    with patch('aiautocommit.get_difftastic_diff') as mock_difft:
        mock_difft.return_value = "structural diff"
        with patch('aiautocommit.generate_commit_message') as mock_gen:
            mock_gen.return_value = "feat: add world"
            result = runner.invoke(main, ["commit", "--difftastic", "--print-message"])
            
            assert result.exit_code == 0
            assert mock_difft.called
            assert "feat: add world" in result.output

def test_difftastic_not_called_by_default(runner, git_repo):
    git_repo.create_file("test.py", "print('hello')")
    git_repo.git_add("test.py")
    
    with patch('aiautocommit.get_difftastic_diff') as mock_difft:
        with patch('aiautocommit.generate_commit_message') as mock_gen:
            mock_gen.return_value = "feat: initial"
            result = runner.invoke(main, ["commit", "--print-message"])
            
            assert result.exit_code == 0
            assert not mock_difft.called