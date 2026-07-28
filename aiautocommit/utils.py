import subprocess
from pathlib import Path
from typing import List, Optional, Union

from .log import log
from .timing import log_execution_time

# Git config overrides to ensure clean, parseable diff output regardless of
# user's local git configuration.
_GIT_SAFE_CONFIG = [
    "-c",
    "color.diff=false",
    "-c",
    "color.ui=false",
    "-c",
    "diff.noprefix=false",
    "-c",
    "diff.mnemonicPrefix=false",
    "-c",
    "diff.colorMoved=false",
    "-c",
    "core.pager=",
]

# --no-ext-diff disables GIT_EXTERNAL_DIFF and diff.external config, which
# would otherwise replace the output with an external tool's format.
GIT_SAFE_DIFF_FLAGS = ["--no-ext-diff"]


def safe_git_cmd() -> list[str]:
    """Return a base git command with user config overrides applied."""
    return ["git", *_GIT_SAFE_CONFIG]


def safe_git_diff_cmd() -> list[str]:
    """Return a base git diff --staged command with user config overrides applied."""
    return [*safe_git_cmd(), "diff", *GIT_SAFE_DIFF_FLAGS, "--staged"]


def run_command(
    args: List[str],
    check: bool = False,
    capture_output: bool = True,
    text: bool = True,
    timeout: Optional[float] = None,
    env: Optional[dict[str, str]] = None,
    cwd: Optional[Union[str, Path]] = None,
) -> subprocess.CompletedProcess:
    """
    Run a shell command using subprocess.run with logging.

    Args:
        args: List of command arguments
        check: If True, raise CalledProcessError if return code is non-zero
        capture_output: If True, capture stdout and stderr
        text: If True, decode stdout and stderr as text
        timeout: Timeout in seconds
        env: Environment variables
        cwd: Current working directory

    Returns:
        CompletedProcess object
    """
    with log_execution_time(f"Running command: {args}"):
        try:
            return subprocess.run(
                args,
                check=check,
                capture_output=capture_output,
                text=text,
                timeout=timeout,
                env=env,
                cwd=cwd,
            )
        except subprocess.CalledProcessError as e:
            log.debug(f"Command failed with exit code {e.returncode}")
            if e.stderr:
                log.debug(f"Stderr: {e.stderr.strip()}")
            raise


def get_current_branch() -> Optional[str]:
    """Get the name of the current git branch."""
    try:
        result = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], check=True)
        return result.stdout.strip()
    except Exception:
        return None


def get_default_branch() -> str | None:
    """Detect the repo's default branch via the remote HEAD ref."""
    result = run_command(
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        check=False,
    )
    if result.returncode != 0:
        return None

    # Returns e.g. "origin/main" — strip the remote prefix
    ref = result.stdout.strip()
    return ref.split("/", 1)[-1] if "/" in ref else ref


def is_default_branch(branch: str | None) -> bool:
    if not branch:
        return False

    default = get_default_branch()
    if default:
        return branch == default

    return branch in ("main", "master", "trunk", "develop")
