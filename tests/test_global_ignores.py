from pathlib import Path

from click.testing import CliRunner

from aiautocommit import main
from aiautocommit.global_ignores import (
    END_MARKER,
    GLOBAL_IGNORE_PATTERNS,
    HARNESS_IGNORE_FILES,
    START_MARKER,
    apply_global_ignores,
    plan_global_ignores,
    upsert_ignore_content,
)


def test_upsert_appends_marked_block():
    result = upsert_ignore_content("node_modules/")

    assert result.startswith("node_modules/\n")
    assert START_MARKER in result
    assert END_MARKER in result
    for pattern in GLOBAL_IGNORE_PATTERNS:
        assert pattern in result


def test_upsert_replaces_existing_block():
    existing = f"keep-me\n\n{START_MARKER}\nold.md\n{END_MARKER}\n\n*.log\n"

    result = upsert_ignore_content(existing)

    assert "keep-me" in result
    assert "*.log" in result
    assert "old.md" not in result
    assert result.count(START_MARKER) == 1
    assert result.count(END_MARKER) == 1
    for pattern in GLOBAL_IGNORE_PATTERNS:
        assert pattern in result


def test_plan_creates_missing_home_files(tmp_path):
    planned = plan_global_ignores(tmp_path)

    assert {item.harness for item in planned} == set(HARNESS_IGNORE_FILES)
    assert all(item.action == "create" for item in planned)
    assert all(item.path.parent == tmp_path for item in planned)


def test_apply_writes_all_harness_files(tmp_path):
    planned = apply_global_ignores(home=tmp_path)

    assert all(item.action == "create" for item in planned)
    for filename in HARNESS_IGNORE_FILES.values():
        content = (tmp_path / filename).read_text()
        assert START_MARKER in content
        assert "commands.md" in content
        assert "instructions.md" in content


def test_apply_is_idempotent(tmp_path):
    apply_global_ignores(home=tmp_path)
    planned = apply_global_ignores(home=tmp_path)

    assert all(item.action == "unchanged" for item in planned)


def test_apply_preserves_existing_ignore_rules(tmp_path):
    cursorignore = tmp_path / ".cursorignore"
    cursorignore.write_text("**/.env\n")

    apply_global_ignores(home=tmp_path)

    content = cursorignore.read_text()
    assert content.startswith("**/.env\n")
    assert "commands.md" in content
    assert "instructions.md" in content


def test_dry_run_does_not_write(tmp_path):
    planned = apply_global_ignores(dry_run=True, home=tmp_path)

    assert all(item.action == "create" for item in planned)
    assert list(tmp_path.iterdir()) == []


def test_cli_dry_run(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "aiautocommit.global_ignores.home_dir", lambda: tmp_path
    )
    runner = CliRunner()

    result = runner.invoke(main, ["global-ignores", "--dry-run"])

    assert result.exit_code == 0
    assert "Would create" in result.output
    assert str(tmp_path / ".cursorignore") in result.output
    assert "commands.md, instructions.md" in result.output
    assert not (tmp_path / ".cursorignore").exists()


def test_cli_writes_home_files(tmp_path, monkeypatch):
    monkeypatch.setattr("aiautocommit.global_ignores.home_dir", lambda: tmp_path)
    runner = CliRunner()

    result = runner.invoke(main, ["global-ignores"])

    assert result.exit_code == 0
    assert "Created" in result.output
    assert (tmp_path / ".cursorignore").exists()
    assert (tmp_path / ".claudeignore").exists()
    assert (tmp_path / ".geminiignore").exists()
    content = Path(tmp_path / ".cursorignore").read_text()
    assert "commands.md" in content
    assert "instructions.md" in content


def test_cli_help_lists_command():
    runner = CliRunner()
    result = runner.invoke(main, ["global-ignores", "--help"])

    assert result.exit_code == 0
    assert "--dry-run" in result.output
    assert "commands.md" in result.output
