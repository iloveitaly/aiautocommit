import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Union

from .log import log

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


@contextmanager
def time_it(name: str):
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        duration = end_time - start_time
        log.debug("execution_time", name=name, duration=duration)


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
    log.debug(f"Running command: {args}")
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
