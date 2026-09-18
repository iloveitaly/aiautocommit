from pathlib import Path
from unittest.mock import MagicMock, patch

from aiautocommit import is_reversion


def test_is_reversion_none(git_repo):
    assert is_reversion() is False


def test_is_reversion_no_git_dir():
    with patch("aiautocommit.get_git_dir", return_value=None):
        assert is_reversion() is False


def test_is_reversion_revert_head(runner, git_repo):
    # REVERT_HEAD exists in .git
    Path(".git/REVERT_HEAD").write_text("reverting")
    assert is_reversion() is True


def test_is_reversion_merge_msg(runner, git_repo):
    # MERGE_MSG exists in .git
    Path(".git/MERGE_MSG").write_text("merging")
    assert is_reversion() is True


def test_is_reversion_fixup(git_repo):
    msg_path = Path("COMMIT_EDITMSG")
    msg_path.write_text("fixup! something")
    assert is_reversion(str(msg_path)) is True


def test_is_reversion_empty_msg(git_repo):
    msg_path = Path("COMMIT_EDITMSG")
    msg_path.write_text("")
    assert is_reversion(str(msg_path)) is False


def test_is_reversion_amend(runner, git_repo):
    git_repo.create_file("test.txt", "content")
    git_repo.git_add("test.txt")
    git_repo.git_commit("First commit")

    # Create a mock COMMIT_EDITMSG with same content as last commit
    msg_path = Path("COMMIT_EDITMSG")
    msg_path.write_text("First commit")

    # Should detect as "amend" (returning True)
    assert is_reversion(str(msg_path)) is True


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
