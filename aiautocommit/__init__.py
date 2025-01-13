import logging
import os
import subprocess
import sys
import warnings
from pathlib import Path

import click
from openai import OpenAI

# Config file locations in priority order
CONFIG_PATHS = [
    Path(".aiautocommit"),  # $PWD/.aiautocommit
    Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
    / "aiautocommit",  # XDG config dir
    Path(os.environ.get("AIAUTOCOMMIT_CONFIG", "")),  # Custom config path
]

COMMIT_PROMPT_FILE = "commit_prompt.txt"
EXCLUSIONS_FILE = "exclusions.txt"
COMMIT_SUFFIX_FILE = "commit_suffix.txt"

# https://platform.openai.com/docs/models
# gpt-4o-mini is cheaper, basically free
MODEL_NAME = os.environ.get("AIAUTOCOMMIT_MODEL", "gpt-4o")

COMMIT_PROMPT = """
You are a expert senior software developer.

Generate a commit message from the `git diff` output below using the following rules:

1. **Subject Line**:

   - Use a conventional commit prefix (e.g., `feat`, `fix`, `docs`, `style`, `refactor`, `build`, `deploy`).
     - Use `docs` if **documentation files** (like `.md`, `.rst`, or documentation comments in code) are the **only files changed**, even if they include code examples.
     - Use `docs` if **comments in code** are the **only changes made**.
     - Use `style` for **formatting**, **code style**, **linting**, or related configuration changes within code files.
     - Use `refactor` only for changes that do not alter behavior but improve the code structure.
     - Use `build` when updating **build scripts**, **configuration files**, or **build system setup** (e.g., `Makefile`, `Justfile`, `package.json`).
     - Use `deploy` when updating deployment scripts.
     - Do not use `feat` for changes that users wouldn't notice.
   - Limit the subject line to **50 characters** after the conventional commit prefix.
   - Write the subject in the **imperative mood**, as if completing the sentence "If applied, this commit will...".
   - Analyze **all changes**, including modifications in build scripts and configurations, when determining the commit message.

2. **Extended Commit Message**:

   - **Do not include an extended commit message** if the changes are **documentation-only**, involve **comment updates**, **simple formatting changes**, or are **not complex**.
   - Include an extended commit message **only if the diff is complex and affects functionality or build processes**.
   - In the extended message:
     - Focus on **what** and **why**, not **how** (the code explains how).
     - Use **markdown bullet points** to describe changes.
     - Explain the **problem** the commit solves and the reasons for the change.
     - Mention any **side effects** or important considerations.
     - **Do not include descriptions of trivial formatting or comment changes** in the extended message.

3. **General Guidelines**:

   - Do **not** wrap the output in a code block.
   - Do **not** include obvious statements easily inferred from the diff.
   - **Simplify** general statements. For example:
     - Replace "update dependency versions in package.json and pnpm.lock" with "update dependencies".
     - Replace "These changes resolve..." with "Resolved...".
   - **Handling Formatting Changes**:
     - If simple formatting updates (like changing quotes, code reformatting) are the **only changes** in code files, use the subject line "style: formatting update".
     - **Do not** treat changes in build scripts or configurations that affect functionality as mere formatting changes. They should be described appropriately.

4. **File Type Hints**:

   - Recognize that a `Justfile` is like a `Makefile` and is part of the **build system**.
   - Changes to the build system are significant and should be reflected in the commit message.
   - Recognize other build-related files (e.g., `Dockerfile`, `package.json`, `webpack.config.js`) as part of the build or configuration.

5. **Avoid Verbose Details**:

   - Do not mention specific variables or excessive details.
   - Keep the commit message concise and focused on the overall changes.

6. **Focus on Functionality Over Documentation**:

   - If both documentation and functionality are modified, **emphasize the functional changes**.

7. **Insufficient Information**:

   - If there isn't enough information to generate a summary, **return an empty string**.

## Example 1

```
diff --git c/.tmux-shell.sh i/.tmux-shell.sh
index a34433f..01d2e9f 100755
--- c/.tmux-shell.sh
+++ i/.tmux-shell.sh
@@ -14,8 +14,8 @@ while [[ $counter -lt 20 ]]; do
   session="${session_uid}-${counter}"
 
   # if the session doesn't exist, create it
-  if ! tmux has-session -t "$session" 2>/dev/null; then
-    tmux new -ADs "$session"
+  if ! /opt/homebrew/bin/tmux has-session -t "$session" 2>/dev/null; then
+    /opt/homebrew/bin/tmux new -ADs "$session"
     break
   fi
```

This diff is short and should have no extended commit message.

The generated commit message should be: fix: use full path to tmux in .tmux-shell.sh
"""


# trailers are a native git feature that can be used to add metadata to a commit
# https://git-scm.com/docs/git-interpret-trailers
# let's indicate that this message was generated by aiautocommit
COMMIT_SUFFIX = """

Generated-by: aiautocommit
"""

# TODO should we ignore files without an extension? can we detect binary files?
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
    ".terraform.lock.hcl",
]

# characters, not tokens
PROMPT_CUTOFF = 10_000

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    **(
        {"filename": os.environ.get("AIAUTOCOMMIT_LOG_PATH")}
        if os.environ.get("AIAUTOCOMMIT_LOG_PATH")
        else {"stream": sys.stderr}
    ),
)

# this is called within py dev environments. Unless it looks like we are explicitly debugging aiautocommit, we force a
# more silent operation. Checking for AIAUTOCOMMIT_LOG_PATH is not a perfect heuristic, but it works for now.
if not os.environ.get("AIAUTOCOMMIT_LOG_PATH"):
    # Suppress ResourceWarnings
    warnings.filterwarnings("ignore", category=ResourceWarning)

    # Optional: Disable httpx logging if desired
    logging.getLogger("httpx").setLevel(logging.WARNING)

# allow a unique API key to be set for OpenAI, for tracking/costing
if os.environ.get("AIAUTOCOMMIT_OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.environ["AIAUTOCOMMIT_OPENAI_API_KEY"]


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

    # Load commit suffix
    commit_suffix_file = config_dir / COMMIT_SUFFIX_FILE
    if commit_suffix_file.exists():
        logging.debug("Loading custom commit suffix from commit_suffix.txt")
        global COMMIT_SUFFIX
        COMMIT_SUFFIX = commit_suffix_file.read_text().strip()


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


def complete(prompt, diff):
    if len(prompt) > PROMPT_CUTOFF:
        logging.warning(
            f"Prompt length ({len(prompt)}) exceeds the maximum allowed length, truncating."
        )

    client = OpenAI()
    completion_resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
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

    return (complete(COMMIT_PROMPT, diff)) + COMMIT_SUFFIX


def git_commit(message):
    # will ignore message if diff is empty
    return subprocess.run(["git", "commit", "--message", message, "--edit"]).returncode


def is_reversion():
    # Check if we're in the middle of a git revert
    if (Path(".git") / "REVERT_HEAD").exists():
        return True

    if (Path(".git") / "MERGE_MSG").exists():
        return True

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
            "pre-commit hook already exists. Here's the contents we would have written:"
        )
        click.echo(pre_commit_script.read_text())


@main.command()
def dump_prompts():
    """Dump default prompts into .aiautocommit directory for easy customization"""
    config_dir = Path(".aiautocommit")
    config_dir.mkdir(exist_ok=True)

    commit_prompt = config_dir / COMMIT_PROMPT_FILE
    exclusions = config_dir / EXCLUSIONS_FILE
    commit_suffix = config_dir / COMMIT_SUFFIX_FILE

    if not commit_prompt.exists():
        commit_prompt.write_text(COMMIT_MSG_PROMPT)
    if not exclusions.exists():
        exclusions.write_text("\n".join(EXCLUDED_FILES))
    if not commit_suffix.exists():
        commit_suffix.write_text(COMMIT_SUFFIX)

    click.echo(
        f"""Dumped default prompts to .aiautocommit directory:

- {COMMIT_PROMPT_FILE}: Template for generating commit messages
- {EXCLUSIONS_FILE}: List of file patterns to exclude from processing
- {COMMIT_SUFFIX}: Text appended to the end of every commit message
"""
    )
