import os
import subprocess
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner
import pytest
from aiautocommit import main, update_env_variables, is_reversion, check_lock_files
from tests.utils import GitTestMixin


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def git_repo(runner):
    with runner.isolated_filesystem():
        from tests.utils import GitTestMixin

        mixin = GitTestMixin()
        mixin.init_repo()
        yield mixin


def test_update_env_variables():
    with patch.dict(os.environ, {"AIAUTOCOMMIT_TEST_VAR_123": "new_value"}):
        update_env_variables()
        assert os.environ.get("TEST_VAR_123") == "new_value"


def test_output_prompt(runner):
    result = runner.invoke(main, ["output-prompt"])
    assert result.exit_code == 0
    assert result.output.strip() != ""


def test_output_exclusions(runner):
    result = runner.invoke(main, ["output-exclusions"])
    assert result.exit_code == 0
    assert "uv.lock" in result.output


def test_dump_prompts(runner):
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["dump-prompts"])
        assert result.exit_code == 0
        assert Path(".aiautocommit/commit_prompt.txt").exists()


def test_is_reversion_amend(runner, git_repo):
    git_repo.create_file("test.txt", "content")
    git_repo.git_add("test.txt")
    git_repo.git_commit("First commit")

    # Create a mock COMMIT_EDITMSG with same content as last commit
    msg_path = Path("COMMIT_EDITMSG")
    msg_path.write_text("First commit")

    # Should detect as "amend" (returning True)
    assert is_reversion(str(msg_path)) is True


def test_check_lock_files_mixed(runner, git_repo):
    # If we have two different types of lock files, it should return a generic message
    git_repo.create_file("uv.lock", "content")
    git_repo.create_file("package-lock.json", "content")
    git_repo.git_add("uv.lock")
    git_repo.git_add("package-lock.json")

    result = check_lock_files()
    assert result.startswith("chore(deps): update lock files")
    assert "Generated-by: aiautocommit" in result


def test_install_pre_commit(runner, git_repo):
    with runner.isolated_filesystem():
        mixin = GitTestMixin()
        mixin.init_repo()
        # Create a dummy .git directory structure if not fully present
        # actually init_repo should handle it
        result = runner.invoke(main, ["install-pre-commit"])
        assert result.exit_code == 0
        assert "Installed pre-commit hook" in result.output
        assert Path(".git/hooks/prepare-commit-msg").exists()


def test_debug_prompt(runner, git_repo):
    git_repo.create_file("test.txt", "content")
    git_repo.git_add("test.txt")
    git_repo.git_commit("First commit")

    # Get the last SHA
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()

    result = runner.invoke(main, ["debug-prompt", sha, "test message"])
    assert result.exit_code == 0
    assert "First commit" in result.output
    assert "test message" in result.output


def test_version_option(runner):
    from aiautocommit import __version__
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output



def test_is_reversion_revert_head(runner, git_repo):
    # REVERT_HEAD exists in .git
    Path(".git/REVERT_HEAD").write_text("reverting")
    assert is_reversion() is True


def test_is_reversion_merge_msg(runner, git_repo):
    # MERGE_MSG exists in .git
    Path(".git/MERGE_MSG").write_text("merging")
    assert is_reversion() is True


def test_configure_prompts_custom(runner, git_repo):
    config_dir = Path("custom_config")
    config_dir.mkdir()
    (config_dir / "commit_prompt.txt").write_text("custom prompt")

    from aiautocommit import configure_prompts

    configure_prompts(config_dir=str(config_dir))
    from aiautocommit import COMMIT_PROMPT

    assert COMMIT_PROMPT == "custom prompt"


def test_complete_truncation():
    from aiautocommit import complete, PROMPT_CUTOFF

    with patch("aiautocommit.Agent") as mock_agent_class:
        mock_agent = mock_agent_class.return_value
        mock_agent.run_sync.return_value.output = "Commit message"

        long_diff = "a" * (PROMPT_CUTOFF + 100)
        complete("prompt", long_diff)

        # Verify run_sync was called with truncated diff
        call_args = mock_agent.run_sync.call_args[0][0]
        assert len(call_args) == PROMPT_CUTOFF


def test_configure_prompts_with_examples(runner, git_repo):
    config_dir = Path("examples_config")
    config_dir.mkdir()
    (config_dir / "commit_prompt.txt").write_text("base prompt")
    examples_dir = config_dir / "examples"
    examples_dir.mkdir()
    (examples_dir / "example_1.md").write_text("example 1 content")
    (examples_dir / "example_2.md").write_text("example 2 content")

    from aiautocommit import configure_prompts

    configure_prompts(config_dir=str(config_dir))
    from aiautocommit import COMMIT_PROMPT

    assert "base prompt" in COMMIT_PROMPT
    assert "example 1 content" in COMMIT_PROMPT
    assert "example 2 content" in COMMIT_PROMPT


def test_git_commit():
    from aiautocommit import git_commit

    with patch("aiautocommit.run_command") as mock_run:
        mock_run.return_value.returncode = 0
        result = git_commit("test message")
        assert result == 0
        mock_run.assert_called_once()
        assert "test message" in mock_run.call_args[0][0]


def test_get_git_dir_failure():
    from aiautocommit import get_git_dir

    with patch("aiautocommit.run_command") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        assert get_git_dir() is None


def test_whitespace_change(runner, git_repo):
    # Create initial file
    git_repo.create_file("test.txt", "hello\n")
    git_repo.git_add("test.txt")
    git_repo.git_commit("initial")

    # Make whitespace change
    git_repo.create_file("test.txt", "hello \n")
    git_repo.git_add("test.txt")

    git_repo.cleanup_commit_editmsg()

    # Run command
    result = runner.invoke(main, ["commit", "--print-message"])

    # Assertions
    assert result.exit_code == 0
    assert "style: whitespace change" in result.output


def test_no_changes(runner, git_repo):
    # Run command with no staged changes
    result = runner.invoke(main, ["commit", "--print-message"])

    # Assertions
    assert result.exit_code == 1
    assert "No changes staged" in result.output


def test_static_commit_python(runner, git_repo):
    git_repo.create_file("uv.lock", "content\n")
    git_repo.git_add("uv.lock")
    git_repo.cleanup_commit_editmsg()

    result = runner.invoke(main, ["commit", "--print-message"])

    assert result.exit_code == 0
    assert "chore(deps): update uv.lock" in result.output


def test_static_commit_node(runner, git_repo):
    git_repo.create_file("package-lock.json", "content\n")
    git_repo.git_add("package-lock.json")
    git_repo.cleanup_commit_editmsg()

    result = runner.invoke(main, ["commit", "--print-message"])

    assert result.exit_code == 0
    assert "chore(deps): update package-lock.json" in result.output


def test_static_commit_mixed_cli(runner, git_repo):
    git_repo.create_file("uv.lock", "content\n")
    git_repo.create_file("package-lock.json", "content\n")
    git_repo.git_add("uv.lock")
    git_repo.git_add("package-lock.json")
    git_repo.cleanup_commit_editmsg()

    result = runner.invoke(main, ["commit", "--print-message"])

    assert result.exit_code == 0
    assert "chore(deps): update lock files" in result.output


def test_lock_file_not_excluded(runner, git_repo):
    # Create a lock file that is NOT in the default excluded_files.txt
    config_dir = Path("config")
    config_dir.mkdir()
    (config_dir / "excluded_files.txt").write_text("")
    (config_dir / "commit_prompt.txt").write_text("Write 'AI message'")

    git_repo.create_file("uv.lock", "content\n")
    git_repo.git_add("uv.lock")
    git_repo.cleanup_commit_editmsg()

    # Mock generate_commit_message to return a fixed string
    with patch("aiautocommit.generate_commit_message", return_value="AI message"):
        # Run command with custom config
        result = runner.invoke(
            main, ["commit", "--print-message", "--config-dir", str(config_dir)]
        )

    # Assertions - should use AI because uv.lock is not excluded in this config
    assert result.exit_code == 0
    assert "AI message" in result.output


def test_static_commit_terraform(runner, git_repo):
    git_repo.create_file(".terraform.lock.hcl", "content\n")
    git_repo.git_add(".terraform.lock.hcl")
    git_repo.cleanup_commit_editmsg()

    result = runner.invoke(main, ["commit", "--print-message"])

    assert result.exit_code == 0
    assert "chore(deps): update .terraform.lock.hcl" in result.output
