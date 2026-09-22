import subprocess
from pathlib import Path

from aiautocommit import LOCK_FILE_MESSAGES, check_lock_files


def test_check_lock_files_no_staged(git_repo):
    assert check_lock_files() is None


def test_check_lock_files_not_only_lock(git_repo):
    git_repo.create_file("uv.lock", "content")
    git_repo.create_file("main.py", "content")
    git_repo.git_add("uv.lock")
    git_repo.git_add("main.py")

    assert check_lock_files() is None


def test_check_lock_files_not_mise_lock(git_repo):
    # Test a file that starts with mise but isn't a lock file
    git_repo.create_file("mise_is_cool.txt", "content")
    git_repo.git_add("mise_is_cool.txt")
    assert check_lock_files() is None


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


def test_check_lock_files_mise_variations(git_repo):
    # Test mise.dev.lock
    git_repo.create_file("mise.dev.lock", "content")
    git_repo.git_add("mise.dev.lock")
    result = check_lock_files()
    assert result.startswith("chore(deps): update mise.dev.lock")

    # Test .config/mise.lock
    subprocess.run(["git", "rm", "-f", "mise.dev.lock"], capture_output=True)
    config_dir = Path("config")
    config_dir.mkdir()
    git_repo.create_file("config/mise.lock", "content")
    git_repo.git_add("config/mise.lock")
    result = check_lock_files()
    assert result.startswith("chore(deps): update mise.lock")

    # Test multiple mise lock files
    git_repo.create_file("mise.dev.lock", "content")
    git_repo.git_add("mise.dev.lock")
    result = check_lock_files()
    assert result.startswith("chore(deps): update lock files")


def test_check_lock_files_mixed(runner, git_repo):
    # If we have two different types of lock files, it should return a generic message
    git_repo.create_file("uv.lock", "content")
    git_repo.create_file("package-lock.json", "content")
    git_repo.git_add("uv.lock")
    git_repo.git_add("package-lock.json")

    result = check_lock_files()
    assert result.startswith("chore(deps): update lock files")
    assert "Generated-by: aiautocommit" in result
