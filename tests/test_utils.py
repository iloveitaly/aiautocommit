import subprocess
from pathlib import Path
from unittest.mock import ANY, patch

import pytest

from aiautocommit.utils import get_current_branch, get_git_toplevel, run_command


def test_run_command_success():
    result = run_command(["echo", "hello"])
    assert result.stdout.strip() == "hello"
    assert result.returncode == 0


def test_run_command_uses_custom_timing_label():
    with patch("aiautocommit.timing.log.debug") as mock_debug:
        run_command(["echo", "hello"], timing_label="git_diff")

    mock_debug.assert_called_once_with(
        "git_diff",
        execution_time=ANY,
        function_name="git_diff",
    )


def test_run_command_failure():

    with pytest.raises(subprocess.CalledProcessError):
        run_command(["ls", "/non-existent-directory-12345"], check=True)


def test_get_current_branch():
    branch = get_current_branch()
    # In a git repo, this should return something
    assert branch is not None


def _init_git_repo(path: Path) -> None:
    subprocess.check_call(["git", "init"], cwd=path)
    subprocess.check_call(["git", "config", "user.email", "test@example.com"], cwd=path)
    subprocess.check_call(["git", "config", "user.name", "Test User"], cwd=path)


def test_get_git_toplevel_repo_root(tmp_path, monkeypatch):
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert get_git_toplevel().resolve() == tmp_path.resolve()


def test_get_git_toplevel_from_subdirectory(tmp_path, monkeypatch):
    _init_git_repo(tmp_path)
    nested = tmp_path / "src" / "pkg"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    assert get_git_toplevel().resolve() == tmp_path.resolve()


def test_get_git_toplevel_outside_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert get_git_toplevel() is None


def test_get_git_toplevel_worktree(tmp_path, monkeypatch):
    main = tmp_path / "main"
    worktree = tmp_path / "worktree"
    main.mkdir()
    _init_git_repo(main)
    (main / "file.txt").write_text("hello")
    subprocess.check_call(["git", "add", "file.txt"], cwd=main)
    subprocess.check_call(["git", "commit", "-m", "init"], cwd=main)
    subprocess.check_call(
        ["git", "worktree", "add", str(worktree), "-b", "feature"], cwd=main
    )

    nested = worktree / "nested"
    nested.mkdir()
    monkeypatch.chdir(nested)
    assert get_git_toplevel().resolve() == worktree.resolve()

    monkeypatch.chdir(main)
    assert get_git_toplevel().resolve() == main.resolve()


def test_get_git_toplevel_git_missing():
    with patch("aiautocommit.utils.run_command", side_effect=FileNotFoundError):
        assert get_git_toplevel() is None
