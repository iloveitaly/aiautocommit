import re
from pathlib import Path
from typing import NamedTuple

GLOBAL_IGNORE_PATTERNS = ("commands.md", "instructions.md")

# Home-level gitignore-style files used by AI coding harnesses.
# `commands.md` / `instructions.md` with no slash match in any directory.
HARNESS_IGNORE_FILES = {
    "cursor": ".cursorignore",
    "claude": ".claudeignore",
    "gemini": ".geminiignore",
    "github": ".copilotignore",
    "opencode": ".opencodeignore",
    "antigravity": ".aiexclude",
    "jetbrains": ".aiignore",
    "windsurf": ".codeiumignore",
}

START_MARKER = "# START AIAUTOCOMMIT GLOBAL IGNORES"
END_MARKER = "# END AIAUTOCOMMIT GLOBAL IGNORES"


class PlannedIgnoreWrite(NamedTuple):
    harness: str
    path: Path
    action: str
    new_content: str


def home_dir() -> Path:
    return Path.home()


def ignore_block() -> str:
    return "\n".join((START_MARKER, *GLOBAL_IGNORE_PATTERNS, END_MARKER))


def upsert_ignore_content(existing: str) -> str:
    block = ignore_block()

    if START_MARKER in existing and END_MARKER in existing:
        pattern = f"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}"
        return re.sub(pattern, block, existing, count=1, flags=re.DOTALL)

    content = existing
    if content and not content.endswith("\n"):
        content += "\n"

    if content:
        content += "\n"

    return content + block + "\n"


def plan_global_ignores(home: Path | None = None) -> list[PlannedIgnoreWrite]:
    root = home if home is not None else home_dir()
    planned: list[PlannedIgnoreWrite] = []

    for harness, filename in HARNESS_IGNORE_FILES.items():
        path = root / filename
        existing = path.read_text() if path.exists() else ""
        new_content = upsert_ignore_content(existing)

        if not path.exists():
            action = "create"
        elif new_content == existing:
            action = "unchanged"
        else:
            action = "update"

        planned.append(
            PlannedIgnoreWrite(
                harness=harness,
                path=path,
                action=action,
                new_content=new_content,
            )
        )

    return planned


def apply_global_ignores(
    *, dry_run: bool = False, home: Path | None = None
) -> list[PlannedIgnoreWrite]:
    planned = plan_global_ignores(home)

    if dry_run:
        return planned

    for item in planned:
        if item.action == "unchanged":
            continue

        item.path.write_text(item.new_content)

    return planned


def format_ignore_plan(planned: list[PlannedIgnoreWrite], *, dry_run: bool) -> str:
    verb = {
        "create": "Would create" if dry_run else "Created",
        "update": "Would update" if dry_run else "Updated",
        "unchanged": "Unchanged",
    }
    patterns = ", ".join(GLOBAL_IGNORE_PATTERNS)
    lines: list[str] = []

    for item in planned:
        lines.append(
            f"{verb[item.action]} {item.path} ({item.harness}): {patterns}"
        )

    return "\n".join(lines)
