"""
Difftastic integration for semantic diff analysis.

This module provides functionality to shell out to the difftastic CLI tool
for syntax-aware structural diffing, with graceful fallback to standard git diff.
"""

import logging
import os
import shutil
import subprocess

from .log import log
from .utils import run_command


def get_difftastic_diff(excluded_files: list[str] | None = None) -> str:
    """
    Get semantic diff using difftastic.

    Assumes difftastic is installed and available in PATH. Caller should
    verify availability before calling this function.

    Args:
        excluded_files: List of file patterns to exclude from diff

    Returns:
        Difftastic output string.

    Raises:
        FileNotFoundError: If difftastic binary not found
        subprocess.TimeoutExpired: If difftastic times out
        subprocess.CalledProcessError: If difftastic fails
    """
    difft_path = shutil.which("difft")
    if not difft_path:
        raise FileNotFoundError("difftastic binary 'difft' not found in PATH")

    log.info("Using difftastic for syntax-aware diff analysis")

    excluded_files = excluded_files or []

    # Build the git diff command
    cmd = [
        "git",
        "--no-pager",
        "diff",
        "--staged",
    ]

    # Add exclusions
    for pattern in excluded_files:
        cmd.append(f":(exclude)**{pattern}")

    # Set up environment to use difftastic as external diff
    env = os.environ.copy()
    env["GIT_EXTERNAL_DIFF"] = difft_path
    env["DFT_DISPLAY"] = "inline"  # Compact display mode
    env["DFT_COLOR"] = "never"  # No color for LLM consumption

    result = run_command(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,  # 60 second timeout for large diffs
        env=env,
    )

    # git diff returns 0 for no changes, 1 for changes found
    if result.returncode not in (0, 1):
        raise subprocess.CalledProcessError(
            result.returncode, cmd, output=result.stdout, stderr=result.stderr
        )

    output = result.stdout.strip()
    log.debug(f"difftastic output length: {len(output)} characters")
    return output
