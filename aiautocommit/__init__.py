import logging
import os
import sys


def update_env_variables():
    """
    Allow keys specific to AIAUTOCOMMIT to be set globally so project-specific keys can be used for openai calls
    """

    prefix = "AIAUTOCOMMIT_"
    env_vars = [
        "LOG_LEVEL",
        "OPENAI_API_KEY",
        "OPENAI_API_VERSION",
        "AZURE_ENDPOINT",
        "AZURE_API_KEY",
    ]

    for var in env_vars:
        if value := os.environ.get(prefix + var):
            os.environ[var] = value


update_env_variables()

# if this isn't first, other config can take precedence
logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO),
    **(
        {"filename": os.environ.get("AIAUTOCOMMIT_LOG_PATH")}
        if os.environ.get("AIAUTOCOMMIT_LOG_PATH")
        else {"stream": sys.stderr}
    ),
)

logger = logging.getLogger(__name__)

import re
import shutil
import subprocess
import warnings
from pathlib import Path

import click
from openai import OpenAI

# Config file locations in priority order
LOCAL_REPO_AUTOCOMMIT_DIR_NAME = ".aiautocommit"
CONFIG_PATHS = [
    Path(LOCAL_REPO_AUTOCOMMIT_DIR_NAME),  # $PWD/.aiautocommit
    Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
    / "aiautocommit",  # XDG config dir
    Path(__file__).parent / "prompt",  # package config dir
]

if custom_config_path := os.environ.get("AIAUTOCOMMIT_CONFIG", None):
    CONFIG_PATHS.insert(-2, Path(custom_config_path))

COMMIT_PROMPT_FILE = "commit_prompt.txt"
EXCLUSIONS_FILE = "excluded_files.txt"
COMMIT_SUFFIX_FILE = "commit_suffix.txt"

# https://platform.openai.com/docs/models
# gpt-4o-mini is cheaper, basically free
MODEL_NAME = os.environ.get("AIAUTOCOMMIT_MODEL", "gpt-4o")

COMMIT_PROMPT = ""
EXCLUDED_FILES = []

# trailers are a native git feature that can be used to add metadata to a commit
# https://git-scm.com/docs/git-interpret-trailers
# let's indicate that this message was generated by aiautocommit
COMMIT_SUFFIX = ""

# characters, not tokens
PROMPT_CUTOFF = 10_000


# this is called within py dev environments. Unless it looks like we are explicitly debugging aiautocommit, we force a
# more silent operation. Checking for AIAUTOCOMMIT_LOG_PATH is not a perfect heuristic, but it works for now.
if not os.environ.get("AIAUTOCOMMIT_LOG_PATH"):
    # Suppress ResourceWarnings
    warnings.filterwarnings("ignore", category=ResourceWarning)

    # Optional: Disable httpx logging if desired
    logging.getLogger("httpx").setLevel(logging.WARNING)


def configure_prompts(config_dir=None):
    global COMMIT_PROMPT, COMMIT_SUFFIX, EXCLUDED_FILES, CONFIG_PATHS

    # Use custom config_dir if provided; otherwise use the default prompt directory
    if config_dir:
        CONFIG_PATHS.insert(0, Path(config_dir))

    # Find first existing config dir
    config_dir = next((path for path in CONFIG_PATHS if path and path.exists()), None)

    if not config_dir:
        logging.debug("No config directory found")
        return

    logging.debug(f"Found config directory at {config_dir}")

    commit_file = config_dir / COMMIT_PROMPT_FILE
    if commit_file.exists():
        logging.debug("Loading commit prompt")
        COMMIT_PROMPT = commit_file.read_text().strip()
    else:
        logging.debug(f"'commit_prompt.txt' does not exist in {config_dir}")

    examples_dir = config_dir / "examples"
    if examples_dir.exists():
        logging.debug("Loading examples")
        pattern = re.compile(r"example_\d\.md$")
        example_files = sorted(
            [
                file
                for file in examples_dir.iterdir()
                if file.is_file() and pattern.match(file.name)
            ],
            key=lambda f: f.name,
        )

        for file in example_files:
            logging.debug(f"Adding example from {file}")
            COMMIT_PROMPT += "\n\n" + file.read_text().strip() + "\n\n"
    else:
        logging.debug(f"'examples' directory does not exist in {config_dir}")

    exclusions_file = config_dir / EXCLUSIONS_FILE
    if exclusions_file.exists():
        logging.debug("Loading exclusions")
        EXCLUDED_FILES = [
            line.strip()
            for line in exclusions_file.read_text().splitlines()
            if line.strip()
        ]
    else:
        logging.debug(f"'{EXCLUSIONS_FILE}' does not exist in {config_dir.absolute()}")

    commit_suffix_file = config_dir / COMMIT_SUFFIX_FILE
    if commit_suffix_file.exists():
        logging.debug("Loading custom commit suffix")
        if commit_suffix_file.exists():
            COMMIT_SUFFIX = "\n\n" + commit_suffix_file.read_text().strip()
        else:
            logging.debug("Custom commit suffix file does not exist")


def get_diff(ignore_whitespace=True):
    """Generate diff for staged changes (ignores whitespace and file exclusions)."""

    arguments = [
        "git",
        "--no-pager",
        "diff",
        "--staged",
    ]
    if ignore_whitespace:
        arguments += [
            "--ignore-space-change",
            "--ignore-blank-lines",
        ]

    for file in EXCLUDED_FILES:
        arguments += [f":(exclude)**{file}"]

    logging.debug(f"Running git diff command: {arguments}")

    diff_process = subprocess.run(arguments, capture_output=True, text=True)
    diff_process.check_returncode()
    normalized_diff = diff_process.stdout.strip()

    logging.debug(f"Discovered Diff:\n{normalized_diff}")

    return normalized_diff


def complete(prompt, diff):
    if len(diff) > PROMPT_CUTOFF:
        logging.warning(
            f"Prompt length ({len(diff)}) exceeds the maximum allowed length, truncating."
        )

    client = OpenAI()
    completion_resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            # TODO not all models support system vs user messages...
            {"role": "system", "content": prompt},
            {"role": "user", "content": diff[:PROMPT_CUTOFF]},
        ],
        # TODO this seems awfully small?
        # max_completion_tokens=128,
    )

    completion = completion_resp.choices[0].message.content.strip()
    return completion


def generate_commit_message(diff):
    if not diff:
        logging.debug("No commit message generated")
        return ""

    message = complete(COMMIT_PROMPT, diff)
    # If the generated message is empty, do not add the commit suffix.
    if not message.strip() or message.strip() == '""':
        return ""
    return message + COMMIT_SUFFIX


def git_commit(message):
    # will ignore message if diff is empty
    return subprocess.run(["git", "commit", "--message", message, "--edit"]).returncode


def is_reversion():
    # Check if we're in the middle of a git revert
    if (Path(".git") / "REVERT_HEAD").exists():
        return True

    # Or a merge
    if (Path(".git") / "MERGE_MSG").exists():
        return True

    # Detect fixup commits by checking if the commit message starts with "fixup!"
    commit_editmsg = Path(".git") / "COMMIT_EDITMSG"
    if commit_editmsg.exists():
        try:
            first_line = commit_editmsg.read_text(
                encoding="utf-8", errors="ignore"
            ).splitlines()[0]
            if first_line.startswith("fixup!"):
                return True
        except IndexError:
            pass

        # Check if a commit amend is happening by comparing the commit edit message
        # with the last commit message (which is pre-populated during amend)
        try:
            current_first_line = (
                commit_editmsg.read_text(encoding="utf-8", errors="ignore")
                .splitlines()[0]
                .strip()
            )
            head_first_line = (
                subprocess.run(
                    ["git", "log", "-1", "--pretty=%B"],
                    capture_output=True,
                    text=True,
                )
                .stdout.splitlines()[0]
                .strip()
            )
            if current_first_line == head_first_line:
                return True
        except Exception:
            pass

    return False


@click.group(invoke_without_command=True)
def main():
    """
    Generate a commit message for staged files and commit them.
    Git will prompt you to edit the generated commit message.
    """
    ctx = click.get_current_context()
    if ctx.invoked_subcommand is None:
        ctx.invoke(commit)


@main.command()
@click.option(
    "-p",
    "--print-message",
    is_flag=True,
    default=False,
    help="print commit msg to stdout instead of performing commit",
)
@click.option(
    "-o",
    "--output-file",
    type=click.Path(writable=True),
    help="write commit message to specified file",
)
@click.option(
    "--config-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="specify custom config directory",
)
def commit(print_message, output_file, config_dir):
    """
    Generate commit message from git diff.
    """

    if is_reversion():
        return 0

    configure_prompts(config_dir)

    try:
        if not get_diff(ignore_whitespace=False):
            click.echo(
                "No changes staged. Use `git add` to stage files before invoking gpt-commit.",
                err=True,
            )
            return 1

        commit_message = generate_commit_message(get_diff())
    except UnicodeDecodeError:
        click.echo("aiautocommit does not support binary files", err=True)

        commit_message = (
            # TODO use heredoc
            "# gpt-commit does not support binary files. "
            "Please enter a commit message manually or unstage any binary files."
        )

    if output_file:
        if commit_message:
            Path(output_file).write_text(commit_message)
            return 0
        return 1
    elif print_message:
        click.echo(commit_message)
        return 0
    else:
        return git_commit(commit_message)


@main.command()
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing pre-commit hook if it exists",
)
def install_pre_commit(overwrite):
    """Install pre-commit script into git hooks directory"""
    git_result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
    )
    git_result.check_returncode()

    git_dir = git_result.stdout.strip()

    target_hooks_dir = Path(git_dir) / "hooks"
    target_hooks_dir.mkdir(exist_ok=True)

    commit_msg_git_hook_name = "prepare-commit-msg"
    pre_commit = target_hooks_dir / commit_msg_git_hook_name
    pre_commit_script = Path(__file__).parent / commit_msg_git_hook_name

    if not pre_commit.exists() or overwrite:
        pre_commit.write_text(pre_commit_script.read_text())
        pre_commit.chmod(0o755)
        click.echo("Installed pre-commit hook")
    else:
        click.echo(
            "pre-commit hook already exists. Here's the contents we would have written:\n"
        )
        click.echo(pre_commit_script.read_text())


@main.command()
def dump_prompts():
    "Dump default prompts by copying the contents of the prompt directory to PWD for customization"

    config_dir = Path(LOCAL_REPO_AUTOCOMMIT_DIR_NAME)
    config_dir.mkdir(exist_ok=True)
    source_prompt_dir = Path(__file__).parent / "prompt"

    if not source_prompt_dir.exists():
        click.echo("Source prompt directory does not exist; nothing to copy.")
        return

    # Copy each item from source_prompt_dir into config_dir
    for item in source_prompt_dir.iterdir():
        target = config_dir / item.name
        if target.exists():
            click.echo(f"{target} already exists. Skipping copy of {item.name}.")
            continue
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy(item, target)

    click.echo(f"Copied contents of {source_prompt_dir} to {config_dir}")


@main.command()
def output_prompt():
    "Dump compiled prompt, helpful for debugging"

    configure_prompts()
    click.echo(COMMIT_PROMPT)


@main.command()
def output_exclusions():
    "Dump file exclusions, helpful for debugging"

    configure_prompts()
    click.echo(EXCLUDED_FILES)


@main.command()
@click.argument("sha")
@click.argument("message")
def debug_prompt(sha, message):
    """
    Show debug info for a given commit SHA:
    - the git diff as a Markdown block
    - the entire prompt as a Markdown block
    - the full commit message
    """
    configure_prompts()

    diff_cmd = ["git", "show", sha, "--pretty="]
    diff_output = subprocess.run(diff_cmd, capture_output=True, text=True).stdout

    commit_msg_cmd = ["git", "log", "--format=%B", "-n", "1", sha]
    commit_message = subprocess.run(
        commit_msg_cmd, capture_output=True, text=True
    ).stdout

    # remove the fixed commit suffix
    commit_message = commit_message.replace(COMMIT_SUFFIX, "").strip()

    click.echo(f"""
Your job is to help me improve a prompt that is being sent to an LLM in order to write a get commit message.

{message}

Explain why and suggest a improved prompt (without examples). Keep your response concise.

Here is the diff:

```
{diff_output}
```

Here was the commit message that was generated:

```
{commit_message}
```

It was written using the following LLM prompt:

---

{COMMIT_PROMPT}
""")
