import os
import subprocess
from pathlib import Path
from unittest.mock import patch

from aiautocommit import configure_prompts


def test_configure_prompts_custom(runner, git_repo):
    config_dir = Path("custom_config")
    config_dir.mkdir()
    (config_dir / "commit_prompt.txt").write_text("custom prompt")

    configure_prompts(config_dir=str(config_dir))
    from aiautocommit import COMMIT_PROMPT

    assert COMMIT_PROMPT == "custom prompt"


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


def test_configure_prompts_no_config():
    with patch("aiautocommit.CONFIG_PATHS", [Path("/non/existent/path")]):
        configure_prompts()


def test_configure_prompts_from_subdirectory(runner, git_repo):
    config_dir = Path(".aiautocommit")
    config_dir.mkdir()
    (config_dir / "commit_prompt.txt").write_text("from repo root")

    nested = Path("src/pkg")
    nested.mkdir(parents=True)
    os.chdir(nested)

    configure_prompts()
    from aiautocommit import COMMIT_PROMPT

    assert COMMIT_PROMPT == "from repo root"


def test_configure_prompts_appends_file_from_subdirectory(runner, git_repo):
    Path(".aiautocommit").write_text("Always mention JIRA tickets")

    nested = Path("src/pkg")
    nested.mkdir(parents=True)
    os.chdir(nested)

    configure_prompts()
    from aiautocommit import COMMIT_PROMPT

    assert "Always mention JIRA tickets" in COMMIT_PROMPT
    assert "<project_instructions>" in COMMIT_PROMPT
    assert "</project_instructions>" in COMMIT_PROMPT


def test_configure_prompts_with_examples(runner, git_repo):
    config_dir = Path("examples_config")
    config_dir.mkdir()
    (config_dir / "commit_prompt.txt").write_text("base prompt")
    examples_dir = config_dir / "examples"
    examples_dir.mkdir()
    (examples_dir / "example_1.md").write_text("example 1 content")
    (examples_dir / "example_2.md").write_text("example 2 content")

    configure_prompts(config_dir=str(config_dir))
    from aiautocommit import COMMIT_PROMPT

    assert "base prompt" in COMMIT_PROMPT
    assert "example 1 content" in COMMIT_PROMPT
    assert "example 2 content" in COMMIT_PROMPT
    assert COMMIT_PROMPT.index("<examples>") < COMMIT_PROMPT.index("example 1 content")
    assert COMMIT_PROMPT.index("example 2 content") < COMMIT_PROMPT.index("</examples>")
    assert "## Examples" not in COMMIT_PROMPT


def test_configure_prompts_uses_worktree_root(runner, git_repo, tmp_path):
    git_repo.create_file("README", "main")
    git_repo.git_add("README")
    git_repo.git_commit("init")

    Path(".aiautocommit").mkdir()
    (Path(".aiautocommit") / "commit_prompt.txt").write_text("main repo prompt")

    worktree = tmp_path / "worktree"
    subprocess.check_call(["git", "worktree", "add", str(worktree), "-b", "feature"])

    wt_config = worktree / ".aiautocommit"
    wt_config.mkdir()
    (wt_config / "commit_prompt.txt").write_text("worktree prompt")

    nested = worktree / "nested"
    nested.mkdir()
    os.chdir(nested)

    configure_prompts()
    from aiautocommit import COMMIT_PROMPT

    assert COMMIT_PROMPT == "worktree prompt"


def test_configure_prompts_worktree_ignores_main_repo_config(
    runner, git_repo, tmp_path
):
    git_repo.create_file("README", "main")
    git_repo.git_add("README")
    git_repo.git_commit("init")

    Path(".aiautocommit").mkdir()
    (Path(".aiautocommit") / "commit_prompt.txt").write_text("main repo prompt")

    worktree = tmp_path / "worktree"
    subprocess.check_call(["git", "worktree", "add", str(worktree), "-b", "other"])

    os.chdir(worktree)

    configure_prompts()
    from aiautocommit import COMMIT_PROMPT

    assert "main repo prompt" not in COMMIT_PROMPT
