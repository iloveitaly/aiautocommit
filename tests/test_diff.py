from pathlib import Path

from aiautocommit import configure_prompts, get_diff, get_diff_size, sort_git_diff


def test_get_diff_exclusion_glob(git_repo):
    # Setup a custom config with the glob pattern
    config_dir = Path("custom_config")
    config_dir.mkdir()
    (config_dir / "excluded_files.txt").write_text("mise*lock")
    (config_dir / "commit_prompt.txt").write_text("prompt")
    configure_prompts(config_dir=str(config_dir))

    # Create and stage a file that should be excluded
    git_repo.create_file("mise.dev.lock", "changed content")
    git_repo.git_add("mise.dev.lock")

    # Create and stage a file that should NOT be excluded
    git_repo.create_file("main.py", "print('hello')")
    git_repo.git_add("main.py")

    diff = get_diff()

    # The diff should contain main.py but NOT mise.dev.lock
    assert "main.py" in diff
    assert "mise.dev.lock" not in diff


def test_get_diff_size():
    section = ["@@ -1,1 +1,1 @@", "-old", "+new", " unchanged"]
    assert get_diff_size(section) == 2


def test_get_diff_size_malformed():
    assert get_diff_size(["not a diff line"]) == 0


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


def test_sort_git_diff_trailing_section():
    diff = "diff --git a/a.py b/a.py\n+content"
    assert "diff --git" in sort_git_diff(diff)


def test_sort_git_diff_no_current_section():
    assert sort_git_diff("something else") == "something else"
