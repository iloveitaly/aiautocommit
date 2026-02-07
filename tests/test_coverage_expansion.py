import os
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner
from aiautocommit import (
    main,
    is_reversion,
    check_lock_files,
    LOCK_FILE_MESSAGES,
    update_env_variables,
    configure_prompts,
)
from aiautocommit.internet import wait_for_internet_connection
from aiautocommit.utils import run_command
from aiautocommit import sort_git_diff, get_diff_size
from aiautocommit.difftastic import get_difftastic_diff
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


def test_is_reversion_revert_head(git_repo):
    git_dir = Path(".git")
    (git_dir / "REVERT_HEAD").touch()
    assert is_reversion() is True


def test_is_reversion_merge_msg(git_repo):
    git_dir = Path(".git")
    (git_dir / "MERGE_MSG").touch()
    assert is_reversion() is True


def test_is_reversion_fixup(git_repo):
    msg_path = Path("COMMIT_EDITMSG")
    msg_path.write_text("fixup! something")
    assert is_reversion(str(msg_path)) is True


def test_is_reversion_none(git_repo):
    assert is_reversion() is False


def test_check_lock_files_exhaustive(git_repo):
    for lock_file, expected_msg in LOCK_FILE_MESSAGES.items():
        subprocess.run(
            ["git", "rm", "-rf", "--cached", "."],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )

        git_repo.create_file(lock_file, "content")
        git_repo.git_add(lock_file)

        result = check_lock_files()
        assert result.startswith(expected_msg)


def test_check_lock_files_not_only_lock(git_repo):
    git_repo.create_file("uv.lock", "content")
    git_repo.create_file("main.py", "content")
    git_repo.git_add("uv.lock")
    git_repo.git_add("main.py")

    assert check_lock_files() is None


def test_check_lock_files_no_staged(git_repo):
    assert check_lock_files() is None


def test_commit_binary_file(runner, git_repo):
    binary_path = Path("test.bin")
    binary_path.write_bytes(b"\x80\x81\x82")
    git_repo.git_add("test.bin")

    result = runner.invoke(main, ["commit", "--print-message"])
    assert "aiautocommit does not support binary files" in result.output
    assert result.exit_code == 0


def test_update_env_variables_precedence():
    with patch.dict(os.environ, {"AIAUTOCOMMIT_TEST_VAR": "new", "TEST_VAR": "old"}):
        update_env_variables()
        assert os.environ["TEST_VAR"] == "new"


def test_configure_prompts_custom_dir(runner):
    with runner.isolated_filesystem():
        custom_dir = Path("custom_config")
        custom_dir.mkdir()
        (custom_dir / "commit_prompt.txt").write_text("custom prompt")
        (custom_dir / "excluded_files.txt").write_text("file1\nfile2")
        (custom_dir / "commit_suffix.txt").write_text("custom suffix")

        configure_prompts(config_dir=str(custom_dir))

        import aiautocommit

        assert aiautocommit.COMMIT_PROMPT == "custom prompt"
        assert "file1" in aiautocommit.EXCLUDED_FILES
        assert "custom suffix" in aiautocommit.COMMIT_SUFFIX


def test_configure_prompts_examples(runner):
    with runner.isolated_filesystem():
        config_dir = Path(".aiautocommit")
        config_dir.mkdir()
        examples_dir = config_dir / "examples"
        examples_dir.mkdir()
        (examples_dir / "example_1.md").write_text("example 1 content")
        (examples_dir / "example_2.md").write_text("example 2 content")

        with patch("aiautocommit.CONFIG_PATHS", [config_dir]):
            configure_prompts()
            import aiautocommit

            assert "example 1 content" in aiautocommit.COMMIT_PROMPT
            assert "example 2 content" in aiautocommit.COMMIT_PROMPT


def test_wait_for_internet_connection_success():
    with patch("aiautocommit.internet.is_internet_connected", return_value=True):
        wait_for_internet_connection()


def test_wait_for_internet_connection_failure():
    with patch("aiautocommit.internet.is_internet_connected", return_value=False):
        with patch("backoff.on_exception", lambda *args, **kwargs: lambda f: f):
            with pytest.raises(Exception, match="no internet connection"):
                wait_for_internet_connection()


def test_get_difftastic_diff_no_binary():
    with patch("shutil.which", return_value=None):
        with pytest.raises(FileNotFoundError):
            get_difftastic_diff()


def test_get_difftastic_diff_success():
    with patch("shutil.which", return_value="/usr/local/bin/difft"):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "difftastic output"
        with patch(
            "aiautocommit.difftastic.run_command", return_value=mock_result
        ) as mock_run:
            output = get_difftastic_diff(excluded_files=["*.lock"])
            assert output == "difftastic output"
            args, kwargs = mock_run.call_args
            assert kwargs["env"]["GIT_EXTERNAL_DIFF"] == "/usr/local/bin/difft"
            assert ":(exclude)***.lock" in args[0]


def test_get_difftastic_diff_error():
    with patch("shutil.which", return_value="/usr/local/bin/difft"):
        mock_result = MagicMock()
        mock_result.returncode = 2
        mock_result.stdout = ""
        mock_result.stderr = "error"
        with patch("aiautocommit.difftastic.run_command", return_value=mock_result):
            with pytest.raises(subprocess.CalledProcessError):
                get_difftastic_diff()


def test_run_command_error():
    with pytest.raises(subprocess.CalledProcessError):
        run_command(["false"], check=True)


def test_get_diff_size():
    section = ["@@ -1,1 +1,1 @@", "-old", "+new", " unchanged"]
    assert get_diff_size(section) == 2


def test_sort_git_diff():
    complex_diff = (
        "diff --git a/large.py b/large.py\n"
        "@@ -1,1 +1,1 @@\n"
        "-1\n-2\n-3\n+4\n+5\n+6\n"
        "diff --git a/small.py b/small.py\n"
        "@@ -1,1 +1,1 @@\n"
        "-1\n+2\n"
    )
    sorted_diff = sort_git_diff(complex_diff)
    assert sorted_diff.index("small.py") < sorted_diff.index("large.py")


def test_sort_git_diff_empty():
    assert sort_git_diff("") == ""


def test_configure_prompts_no_config():
    with patch("aiautocommit.CONFIG_PATHS", [Path("/non/existent/path")]):
        configure_prompts()


def test_get_diff_size_malformed():
    assert get_diff_size(["not a diff line"]) == 0


def test_generate_commit_message_empty_diff():
    from aiautocommit import generate_commit_message

    assert generate_commit_message("") == ""


def test_generate_commit_message_empty_completion():
    from aiautocommit import generate_commit_message

    with patch("aiautocommit.complete", return_value=""):
        assert generate_commit_message("some diff") == ""


def test_generate_commit_message_quoted_empty():
    from aiautocommit import generate_commit_message

    with patch("aiautocommit.complete", return_value='""'):
        assert generate_commit_message("some diff") == ""


def test_generate_commit_message_with_suffix():
    from aiautocommit import generate_commit_message

    with patch("aiautocommit.complete", return_value="feat: test"):
        with patch("aiautocommit.COMMIT_SUFFIX", " [suffix]"):
            assert generate_commit_message("some diff") == "feat: test [suffix]"


def test_install_pre_commit_exists(runner, git_repo):
    runner.invoke(main, ["install-pre-commit"])
    result = runner.invoke(main, ["install-pre-commit"])
    assert "pre-commit hook already exists" in result.output


def test_dump_prompts_exists(runner):
    with runner.isolated_filesystem():
        os.mkdir(".aiautocommit")
        with open(".aiautocommit/commit_prompt.txt", "w") as f:
            f.write("existing")

        result = runner.invoke(main, ["dump-prompts"])
        assert "already exists" in result.output


def test_is_reversion_no_git_dir():
    with patch("aiautocommit.get_git_dir", return_value=None):
        assert is_reversion() is False


def test_is_reversion_amend_fail(git_repo):
    git_repo.create_file("test.txt", "content")
    git_repo.git_add("test.txt")
    git_repo.git_commit("First")

    msg_path = Path("COMMIT_EDITMSG")
    msg_path.write_text("Different")

    with patch("aiautocommit.run_command") as mock_run:
        mock_result_dir = MagicMock()
        mock_result_dir.stdout = ".git"

        mock_run.side_effect = [mock_result_dir, Exception("git log failed")]
        assert is_reversion(str(msg_path)) is False


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
            assert "No internet connection" in result.output


def test_commit_difftastic_missing(runner, git_repo):
    git_repo.create_file("test.py", "print('hello')")
    git_repo.git_add("test.py")

    with patch("shutil.which", return_value=None):
        with patch.dict(os.environ, {"AIAUTOCOMMIT_DIFFTASTIC": "1"}):
            with patch("aiautocommit.get_diff") as mock_diff:
                mock_diff.return_value = "diff"
                runner.invoke(main, ["commit", "--print-message"])
                assert mock_diff.called


def test_commit_empty_message(runner, git_repo):
    git_repo.create_file("test.py", "print('hello')")
    git_repo.git_add("test.py")

    with patch("aiautocommit.generate_commit_message", return_value=""):
        result = runner.invoke(main, ["commit", "--output-file", "out.txt"])
        assert result.exit_code == 1


def test_dump_prompts_source_missing(runner):
    with runner.isolated_filesystem():
        with patch("aiautocommit.Path.__truediv__") as mock_div:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_div.return_value = mock_path

            result = runner.invoke(main, ["dump-prompts"])
            assert "Source prompt directory does not exist" in result.output


def test_git_commit_failure():
    from aiautocommit import git_commit

    with patch("aiautocommit.run_command") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        assert git_commit("msg") == 1


def test_commit_performs_git_commit(runner, git_repo):
    git_repo.create_file("test.py", "print('hello')")
    git_repo.git_add("test.py")
    with patch("aiautocommit.generate_commit_message", return_value="feat: test"):
        with patch("aiautocommit.git_commit", return_value=0) as mock_commit:
            result = runner.invoke(main, ["commit"])
            assert result.exit_code == 0
            assert mock_commit.called


def test_is_reversion_empty_msg(git_repo):
    msg_path = Path("COMMIT_EDITMSG")
    msg_path.write_text("")
    assert is_reversion(str(msg_path)) is False


def test_sort_git_diff_trailing_section():
    diff = "diff --git a/a.py b/a.py\n+content"
    assert "diff --git" in sort_git_diff(diff)


def test_complete_returns_none():
    from aiautocommit import complete

    with patch("aiautocommit.Agent") as MockAgent:
        mock_agent_instance = MockAgent.return_value
        mock_result = MagicMock()
        mock_result.output = None
        mock_agent_instance.run_sync.return_value = mock_result
        assert complete("prompt", "diff") == ""


def test_commit_with_output_file(runner, git_repo):
    git_repo.create_file("test.py", "print('hello')")
    git_repo.git_add("test.py")
    with patch("aiautocommit.generate_commit_message", return_value="feat: test"):
        result = runner.invoke(main, ["commit", "--output-file", "out.txt"])
        assert result.exit_code == 0
        assert Path("out.txt").read_text() == "feat: test"


def test_is_reversion_amend_success_real(git_repo):
    git_repo.create_file("test.txt", "content")
    git_repo.git_add("test.txt")
    git_repo.git_commit("First")

    msg_path = Path("COMMIT_EDITMSG")
    msg_path.write_text("First")

    assert is_reversion(str(msg_path)) is True


def test_is_reversion_amend_mismatch(git_repo):
    git_repo.create_file("test.txt", "content")
    git_repo.git_add("test.txt")
    git_repo.git_commit("First")

    msg_path = Path("COMMIT_EDITMSG")
    msg_path.write_text("Second")

    assert is_reversion(str(msg_path)) is False


def test_sort_git_diff_no_current_section():
    assert sort_git_diff("something else") == "something else"


def test_commit_binary_file_exit_path(runner, git_repo):
    with patch(
        "aiautocommit.get_diff",
        side_effect=UnicodeDecodeError("codec", b"", 0, 1, "reason"),
    ):
        result = runner.invoke(main, ["commit"])
        assert result.exit_code == 1
        assert "does not support binary files" in result.output


def test_commit_reversion_exit(runner):
    with patch("aiautocommit.is_reversion", return_value=True):
        result = runner.invoke(main, ["commit"])
        assert result.exit_code == 0


def test_main_default_invoke(runner):
    # This triggers line 404: ctx.invoke(commit)
    mock_ctx = MagicMock()
    mock_ctx.invoked_subcommand = None
    with patch("click.get_current_context", return_value=mock_ctx):
        from aiautocommit import main, commit

        main.callback()
        mock_ctx.invoke.assert_called_with(commit)
