import asyncio
import os
import subprocess
import sys
import logging
from pathlib import Path
import click

# Config file locations in priority order
CONFIG_PATHS = [
    Path(".autocommit"),  # $PWD/.autocommit
    Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
    / "autocommit",  # XDG config dir
    Path(os.environ.get("AUTOCOMMIT_CONFIG", "")),  # Custom config path
]

DIFF_PROMPT_FILE = "diff_prompt.txt"
COMMIT_PROMPT_FILE = "commit_prompt.txt"
EXCLUSIONS_FILE = "exclusions.txt"


MODEL_NAME = os.environ.get("AUTOCOMMIT_MODEL", "gpt-4o-mini")
DIFF_PROMPT = """
Generate a succinct summary using these rules:

* Indicate if this is a large, medium, or small (less than 100 lines) change
* Omit comments or whitespace changes

Of the following code changes:
"""
COMMIT_MSG_PROMPT = """
Generate a commit message using these rules:

* No more than 50 characters
* Conventional commit format
* When a large diff is , include extended commit message with markdown bullets if there are many details to include
* Do not wrap in a codeblock

From these summaries:
"""
EXCLUDED_FILES = [
    "Gemfile.lock",
    "uv.lock",
    "poetry.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "pnpm-lock.yaml",
    "composer.lock",
    "cargo.lock",
    "mix.lock",
    "Pipfile.lock",
    "pdm.lock",
    "flake.lock",
    "bun.lockb",
]

PROMPT_CUTOFF = 10_000

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    **(
        {"filename": os.environ.get("AUTOCOMMIT_LOG_PATH")}
        if os.environ.get("AUTOCOMMIT_LOG_PATH")
        else {"stream": sys.stderr}
    ),
)


def configure_prompts(config_dir=None):
    global DIFF_PROMPT, COMMIT_MSG_PROMPT, EXCLUDED_FILES, CONFIG_PATHS

    if config_dir:
        CONFIG_PATHS.insert(0, Path(config_dir))

    # Find first existing config dir
    config_dir = next((path for path in CONFIG_PATHS if path and path.exists()), None)

    if not config_dir:
        logging.debug("No config directory found")
        return

    logging.debug(f"Found config directory at {config_dir}")

    # Load diff prompt
    diff_file = config_dir / DIFF_PROMPT_FILE
    if diff_file.exists():
        logging.debug("Loading custom diff prompt from diff.txt")
        DIFF_PROMPT = diff_file.read_text().strip()

    # Load commit prompt
    commit_file = config_dir / COMMIT_PROMPT_FILE
    if commit_file.exists():
        logging.debug("Loading custom commit prompt from commit.txt")
        COMMIT_MSG_PROMPT = commit_file.read_text().strip()

    # Load exclusions
    exclusions_file = config_dir / EXCLUSIONS_FILE
    if exclusions_file.exists():
        logging.debug("Loading custom exclusions from exclusions.txt")
        EXCLUDED_FILES = [
            line.strip()
            for line in exclusions_file.read_text().splitlines()
            if line.strip()
        ]


def get_diff(ignore_whitespace=True):
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
        arguments += [f":(exclude){file}"]

    diff_process = subprocess.run(arguments, capture_output=True, text=True)
    diff_process.check_returncode()
    normalized_diff = diff_process.stdout.strip()

    logging.debug(f"Discovered Diff:\n{normalized_diff}")

    return normalized_diff


def parse_diff(diff):
    file_diffs = diff.split("\ndiff")
    file_diffs = [file_diffs[0]] + [
        "\ndiff" + file_diff for file_diff in file_diffs[1:]
    ]
    chunked_file_diffs = []
    for file_diff in file_diffs:
        [head, *chunks] = file_diff.split("\n@@")
        chunks = ["\n@@" + chunk for chunk in reversed(chunks)]
        chunked_file_diffs.append((head, chunks))
    return chunked_file_diffs


def assemble_diffs(parsed_diffs, cutoff):
    """
    Create multiple well-formatted diff strings, each being shorter than cutoff
    """
    assembled_diffs = [""]

    def add_chunk(chunk):
        if len(assembled_diffs[-1]) + len(chunk) <= cutoff:
            assembled_diffs[-1] += "\n" + chunk
            return True
        else:
            assembled_diffs.append(chunk)
            return False

    for head, chunks in parsed_diffs:
        if not chunks:
            add_chunk(head)
        else:
            add_chunk(head + chunks.pop())
        while chunks:
            if not add_chunk(chunks.pop()):
                assembled_diffs[-1] = head + assembled_diffs[-1]
    return assembled_diffs


async def complete(prompt):
    from openai import AsyncOpenAI

    aclient = AsyncOpenAI()
    completion_resp = await aclient.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt[: PROMPT_CUTOFF + 100]}],
        # TODO this seems awfully small?
        max_tokens=128,
    )
    completion = completion_resp.choices[0].message.content.strip()
    return completion


async def summarize_diff(diff):
    assert diff

    summarized_diff = await complete(DIFF_PROMPT + "\n\n" + diff + "\n\n")
    logging.debug(f"Summarized Diff:\n{summarized_diff}")
    return summarized_diff


async def summarize_summaries(summaries):
    assert summaries
    return await complete(COMMIT_MSG_PROMPT + "\n\n" + summaries + "\n\n")


async def generate_commit_message(diff):
    if not diff:
        logging.debug("No commit message generated")
        return ""

    assembled_diffs = assemble_diffs(parse_diff(diff), PROMPT_CUTOFF)

    summaries = await asyncio.gather(
        *[summarize_diff(diff) for diff in assembled_diffs]
    )
    return await summarize_summaries("\n".join(summaries))


def git_commit(message):
    # will ignore message if diff is empty
    return subprocess.run(["git", "commit", "--message", message, "--edit"]).returncode


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

    configure_prompts(config_dir)

    try:
        if not get_diff(ignore_whitespace=False):
            click.echo(
                "No changes staged. Use `git add` to stage files before invoking gpt-commit.",
                err=True,
            )
            return 1

        # run async so when multiple chunks exist we can get summaries concurrently
        commit_message = asyncio.run(generate_commit_message(get_diff()))
    except UnicodeDecodeError:
        click.echo("gpt-commit does not support binary files", err=True)
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
def install_pre_commit():
    """Install pre-commit script into git hooks directory"""
    git_result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
    )
    git_result.check_returncode()

    git_dir = git_result.stdout.strip()
    hooks_dir = Path(git_dir) / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    pre_commit = hooks_dir / "pre-commit"

    if not pre_commit.exists():
        pre_commit_script = Path(__file__).parent / "pre-commit"
        pre_commit.write_text(pre_commit_script.read_text())
        pre_commit.chmod(0o755)
        click.echo("Installed pre-commit hook")
    else:
        click.echo(
            "pre-commit hook already exists. Here's the contents we would have written:"
        )
        click.echo(pre_commit.read_text())


@main.command()
def dump_prompts():
    """Dump default prompts into .autocommit directory for easy customization"""
    config_dir = Path(".autocommit")
    config_dir.mkdir(exist_ok=True)

    diff_prompt = config_dir / DIFF_PROMPT_FILE
    commit_prompt = config_dir / COMMIT_PROMPT_FILE
    exclusions = config_dir / EXCLUSIONS_FILE

    if not diff_prompt.exists():
        diff_prompt.write_text(DIFF_PROMPT)
    if not commit_prompt.exists():
        commit_prompt.write_text(COMMIT_MSG_PROMPT)
    if not exclusions.exists():
        exclusions.write_text("\n".join(EXCLUDED_FILES))

    click.echo(
        """Dumped default prompts to .autocommit directory:

- diff_prompt.txt: Template for generating diff summaries, this is passed to commit_prompt.txt
- commit_prompt.txt: Template for generating commit messages
- exclusions.txt: List of file patterns to exclude from processing"""
    )
