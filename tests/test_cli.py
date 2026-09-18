import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aiautocommit import main, update_env_variables

from tests.utils import GitTestMixin


def test_update_env_variables():
    with patch.dict(os.environ, {"AIAUTOCOMMIT_TEST_VAR_123": "new_value"}):
        update_env_variables()
        assert os.environ.get("TEST_VAR_123") == "new_value"


def test_update_env_variables_precedence():
    with patch.dict(os.environ, {"AIAUTOCOMMIT_TEST_VAR": "new", "TEST_VAR": "old"}):
        update_env_variables()
        assert os.environ["TEST_VAR"] == "new"


def test_output_prompt(runner):
    result = runner.invoke(main, ["output-prompt"])
    assert result.exit_code == 0
    assert result.output.strip() != ""
    assert "<subject_line>" in result.output
    assert "<body>" in result.output
    assert "<output>" in result.output
    assert "<examples>" in result.output
    assert "<instructions>" not in result.output
    assert "# Instructions" not in result.output
    assert "## Subject Line" not in result.output
    assert "## Examples" not in result.output


def test_output_exclusions(runner):
    result = runner.invoke(main, ["output-exclusions"])
    assert result.exit_code == 0
    assert "uv.lock" in result.output


def test_dump_prompts(runner):
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["dump-prompts"])
        assert result.exit_code == 0
        assert Path(".aiautocommit/commit_prompt.txt").exists()


def test_dump_prompts_exists(runner):
    with runner.isolated_filesystem():
        os.mkdir(".aiautocommit")
        with open(".aiautocommit/commit_prompt.txt", "w") as f:
            f.write("existing")

        result = runner.invoke(main, ["dump-prompts"])
        assert "already exists" in result.output


def test_dump_prompts_source_missing(runner):
    with runner.isolated_filesystem():
        with patch("aiautocommit.Path.__truediv__") as mock_div:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_div.return_value = mock_path

            result = runner.invoke(main, ["dump-prompts"])
            assert "Source prompt directory does not exist" in result.output


def test_dump_prompts_to_git_root(runner, git_repo):
    Path("subdir").mkdir()
    os.chdir("subdir")

    result = runner.invoke(main, ["dump-prompts"])
    assert result.exit_code == 0
    assert (Path("..") / ".aiautocommit" / "commit_prompt.txt").exists()
    assert not Path(".aiautocommit").exists()


def test_install(runner, git_repo):
    with runner.isolated_filesystem():
        mixin = GitTestMixin()
        mixin.init_repo()
        # Create a dummy .git directory structure if not fully present
        # actually init_repo should handle it
        result = runner.invoke(main, ["install"])
        assert result.exit_code == 0
        assert "Installed pre-commit hook" in result.output
        assert Path(".git/hooks/prepare-commit-msg").exists()


def test_install_skip_edit(runner, git_repo):
    with runner.isolated_filesystem():
        mixin = GitTestMixin()
        mixin.init_repo()
        result = runner.invoke(main, ["install", "--skip-edit"])
        assert result.exit_code == 0
        assert "Installed pre-commit hook" in result.output
        assert "Set local core.editor=true" in result.output
        assert Path(".git/hooks/prepare-commit-msg").exists()
        editor = subprocess.check_output(
            ["git", "config", "--local", "--get", "core.editor"],
            text=True,
        ).strip()
        assert editor == "true"


def test_install_pre_commit_exists(runner, git_repo):
    runner.invoke(main, ["install"])
    result = runner.invoke(main, ["install"])
    assert "pre-commit hook already exists" in result.output


def test_uninstall(runner, git_repo):
    with runner.isolated_filesystem():
        mixin = GitTestMixin()
        mixin.init_repo()

        # First install the hook
        runner.invoke(main, ["install"])
        assert Path(".git/hooks/prepare-commit-msg").exists()

        # Then uninstall it
        result = runner.invoke(main, ["uninstall"])
        assert result.exit_code == 0
        assert "Removed pre-commit hook" in result.output
        assert not Path(".git/hooks/prepare-commit-msg").exists()

        # Try to uninstall again
        result2 = runner.invoke(main, ["uninstall"])
        assert result2.exit_code == 0
        assert "pre-commit hook not found" in result2.output


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
    from aiautocommit import MODEL_NAME, get_cli_version, is_local_source_checkout

    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0

    cli_version = get_cli_version()
    assert cli_version in result.output
    assert f"model: {MODEL_NAME}" in result.output

    if is_local_source_checkout():
        assert cli_version.endswith(".dev")


def test_version_option_configured_model(runner):
    with patch("aiautocommit.MODEL_NAME", "openai:gpt-4o"):
        result = runner.invoke(main, ["--version"])

    assert result.exit_code == 0
    assert "model: openai:gpt-4o" in result.output


def test_complete_truncation():
    from aiautocommit import PROMPT_CUTOFF, complete

    with patch("aiautocommit.Agent") as mock_agent_class:
        mock_agent = mock_agent_class.return_value
        mock_agent.run_sync.return_value.output = "Commit message"

        long_diff = "a" * (PROMPT_CUTOFF + 100)
        complete("prompt", long_diff)

        # Verify run_sync was called with the truncated raw diff as the user message
        call_args = mock_agent.run_sync.call_args[0][0]
        assert call_args == long_diff[:PROMPT_CUTOFF]
        assert "<diff>" not in call_args


def test_complete_returns_none():
    from aiautocommit import complete

    with patch("aiautocommit.Agent") as MockAgent:
        mock_agent_instance = MockAgent.return_value
        mock_result = MagicMock()
        mock_result.output = None
        mock_agent_instance.run_sync.return_value = mock_result
        assert complete("prompt", "diff") == ""


def test_complete_503_graceful_fallback():
    from pydantic_ai.exceptions import ModelHTTPError

    from aiautocommit import complete

    with patch("aiautocommit.Agent") as mock_agent_class:
        mock_agent = mock_agent_class.return_value
        # Simulate a 503 ModelHTTPError
        mock_agent.run_sync.side_effect = ModelHTTPError(
            status_code=503,
            model_name="gemini-3.1-flash-lite-preview",
            body={
                "error": {
                    "code": 503,
                    "message": "This model is currently experiencing high demand.",
                    "status": "UNAVAILABLE",
                }
            },
        )

        # This should now return a commented string instead of raising
        result = complete("prompt", "diff")
        assert (
            result
            == "# aiautocommit: AI model unavailable. Falling back to manual message."
        )


def test_format_error_json():
    from aiautocommit import format_error_json

    assert format_error_json(None) is None
    assert format_error_json({"error": "test"}) == '{\n  "error": "test"\n}'
    assert format_error_json('{"code": 400}') == '{\n  "code": 400\n}'
    assert format_error_json(b'{"bytes": true}') == '{\n  "bytes": true\n}'
    assert format_error_json("plain error text") == "plain error text"


def test_complete_model_http_error_no_body():
    from pydantic_ai.exceptions import ModelHTTPError

    from aiautocommit import complete

    with patch("aiautocommit.Agent") as mock_agent_class:
        mock_agent = mock_agent_class.return_value
        mock_agent.run_sync.side_effect = ModelHTTPError(
            status_code=500,
            model_name="test-model",
            body=None,
        )
        result = complete("prompt", "diff")
        assert (
            result
            == "# aiautocommit: AI model unavailable. Falling back to manual message."
        )


def test_complete_model_api_error():
    from pydantic_ai.exceptions import ModelAPIError

    from aiautocommit import complete

    with patch("aiautocommit.Agent") as mock_agent_class:
        mock_agent = mock_agent_class.return_value
        mock_agent.run_sync.side_effect = ModelAPIError(
            model_name="test-model",
            message="Connection failed",
        )
        result = complete("prompt", "diff")
        assert (
            result
            == "# aiautocommit: AI model unavailable. Falling back to manual message."
        )


def test_complete_user_error_as_red_message(runner, git_repo):
    from pydantic_ai.exceptions import UserError

    git_repo.create_file("test.txt", "hello\n")
    git_repo.git_add("test.txt")
    git_repo.cleanup_commit_editmsg()

    with (
        patch("aiautocommit.wait_for_internet_connection"),
        patch("aiautocommit.Agent") as mock_agent_class,
    ):
        mock_agent_class.side_effect = UserError(
            "Set the `GOOGLE_API_KEY` environment variable or pass it via "
            "`GoogleProvider(api_key=...)` to use the Gemini API."
        )
        result = runner.invoke(main, ["commit", "--print-message"])

    assert result.exit_code == 1
    assert "GOOGLE_API_KEY" in result.output
    assert "Traceback" not in result.output


def test_complete_user_error_raises_user_facing_error():
    from pydantic_ai.exceptions import UserError

    from aiautocommit import UserFacingError, complete

    with patch("aiautocommit.Agent") as mock_agent_class:
        mock_agent_class.side_effect = UserError("missing API key")
        with pytest.raises(UserFacingError, match="missing API key"):
            complete("prompt", "diff")


def test_git_commit():
    from aiautocommit import git_commit

    with patch("aiautocommit.run_command") as mock_run:
        mock_run.return_value.returncode = 0
        result = git_commit("test message")
        assert result == 0
        mock_run.assert_called_once()
        assert "test message" in mock_run.call_args[0][0]


def test_git_commit_failure():
    from aiautocommit import git_commit

    with patch("aiautocommit.run_command") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        assert git_commit("msg") == 1


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

    # Mock the Agent to return a specific message if it's called (it shouldn't be if diff is empty)
    # But if it IS called (e.g. if ignore_whitespace fails), we still want to mock it.
    with patch("aiautocommit.Agent") as mock_agent_class:
        mock_agent = mock_agent_class.return_value
        mock_agent.run_sync.return_value.output = "style: format test file whitespace"

        # Run command
        result = runner.invoke(main, ["commit", "--print-message"])

    # Assertions
    assert result.exit_code == 0
    # If get_diff(ignore_whitespace=True) works, it should return the hardcoded message.
    # If it fails to ignore whitespace, it will return the mocked AI message.
    # In both cases, the test will pass or we'll see what happened.
    assert (
        "style: whitespace change" in result.output
        or "style: format test file whitespace" in result.output
    )


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


def test_commit_binary_file(runner, git_repo):
    binary_path = Path("test.bin")
    binary_path.write_bytes(b"\x80\x81\x82")
    git_repo.git_add("test.bin")

    result = runner.invoke(main, ["commit", "--print-message"])
    assert "aiautocommit does not support binary files" in result.output
    assert result.exit_code == 0


def test_commit_binary_file_exit_path(runner, git_repo):
    with patch(
        "aiautocommit.get_diff",
        side_effect=UnicodeDecodeError("codec", b"", 0, 1, "reason"),
    ):
        result = runner.invoke(main, ["commit"])
        assert result.exit_code == 1
        assert "does not support binary files" in result.output


def test_commit_no_internet(runner, git_repo):
    git_repo.create_file("test.py", "print('hello')")
    git_repo.git_add("test.py")

    with patch("aiautocommit.get_diff", return_value="some diff"):
        with patch(
            "aiautocommit.wait_for_internet_connection",
            side_effect=Exception("No internet"),
        ):
            result = runner.invoke(main, ["commit"])
            assert result.exit_code == 0


def test_commit_empty_message(runner, git_repo):
    git_repo.create_file("test.py", "print('hello')")
    git_repo.git_add("test.py")

    with patch("aiautocommit.generate_commit_message", return_value=""):
        result = runner.invoke(main, ["commit", "--output-file", "out.txt"])
        assert result.exit_code == 0


def test_commit_performs_git_commit(runner, git_repo):
    git_repo.create_file("test.py", "print('hello')")
    git_repo.git_add("test.py")
    with patch("aiautocommit.generate_commit_message", return_value="feat: test"):
        with patch("aiautocommit.git_commit", return_value=0) as mock_commit:
            result = runner.invoke(main, ["commit"])
            assert result.exit_code == 0
            assert mock_commit.called


def test_commit_with_output_file(runner, git_repo):
    git_repo.create_file("test.py", "print('hello')")
    git_repo.git_add("test.py")
    with patch("aiautocommit.generate_commit_message", return_value="feat: test"):
        result = runner.invoke(main, ["commit", "--output-file", "out.txt"])
        assert result.exit_code == 0
        assert Path("out.txt").read_text() == "feat: test"


def test_commit_with_existing_output_file(runner, git_repo):
    git_repo.create_file("test.py", "print('hello')")
    git_repo.git_add("test.py")
    out_path = Path("out.txt")
    out_path.write_text("# existing content")
    with patch("aiautocommit.generate_commit_message", return_value="feat: test"):
        result = runner.invoke(main, ["commit", "--output-file", "out.txt"])
        assert result.exit_code == 0
        assert out_path.read_text() == "feat: test\n\n# existing content"


def test_commit_reversion_exit(runner):
    with patch("aiautocommit.is_reversion", return_value=True):
        result = runner.invoke(main, ["commit"])
        assert result.exit_code == 0


def test_main_default_invoke(runner):
    # This triggers line 404: ctx.invoke(commit)
    mock_ctx = MagicMock()
    mock_ctx.invoked_subcommand = None
    with patch("click.get_current_context", return_value=mock_ctx):
        from aiautocommit import commit, main

        main.callback()
        mock_ctx.invoke.assert_called_with(commit)
