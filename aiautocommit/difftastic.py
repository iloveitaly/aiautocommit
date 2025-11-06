"""
Difftastic integration for semantic diff analysis.

This module provides functionality to shell out to the difftastic CLI tool
for syntax-aware structural diffing, with graceful fallback to standard git diff.
"""

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def find_difftastic() -> Optional[str]:
    """
    Find difftastic binary in PATH.

    Returns:
        Path to difft binary if found, None otherwise.
    """
    difft_path = shutil.which("difft")

    if difft_path:
        logger.debug(f"Found difftastic at: {difft_path}")
    else:
        logger.debug("difftastic not found in PATH")

    return difft_path


def check_difftastic_version() -> Optional[str]:
    """
    Check if difftastic is available and return its version.

    Returns:
        Version string if available, None if difftastic not found.
    """
    difft_path = find_difftastic()

    if not difft_path:
        return None

    try:
        result = subprocess.run(
            [difft_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )
        version = result.stdout.strip()
        logger.debug(f"Difftastic version: {version}")
        return version
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(f"Failed to get difftastic version: {e}")
        return None


def get_staged_files() -> list[str]:
    """
    Get list of staged files for diffing.

    Returns:
        List of staged file paths.
    """
    result = subprocess.run(
        ["git", "diff", "--staged", "--name-only"],
        capture_output=True,
        text=True,
        check=True
    )

    files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    logger.debug(f"Found {len(files)} staged files")
    return files


def run_difftastic_on_staged(excluded_files: list[str] = None) -> Optional[str]:
    """
    Run difftastic on all staged changes using GIT_EXTERNAL_DIFF.

    This uses git's external diff mechanism to run difftastic on staged changes.

    Args:
        excluded_files: List of file patterns to exclude (e.g., ['*.lock', 'package-lock.json'])

    Returns:
        Difftastic output as string, or None if difftastic failed or is not available.
    """
    difft_path = find_difftastic()

    if not difft_path:
        logger.info("difftastic not found - install with: brew install difftastic")
        return None

    excluded_files = excluded_files or []

    try:
        # Use GIT_EXTERNAL_DIFF to tell git to use difftastic
        # We need to wrap difft in a script that handles git's diff interface
        # Git passes: path old-file old-hex old-mode new-file new-hex new-mode
        # But difft just wants: old-file new-file

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

        logger.debug(f"Running git diff for difftastic: {' '.join(cmd)}")

        # Set up environment to use difftastic as external diff
        env = os.environ.copy()
        env["GIT_EXTERNAL_DIFF"] = difft_path
        # Configure difftastic options
        env["DFT_DISPLAY"] = "inline"  # Compact display mode
        env["DFT_COLOR"] = "never"     # No color for LLM consumption

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout for large diffs
            env=env,
        )

        # git diff returns 0 for no changes, 1 for changes
        if result.returncode not in (0, 1):
            logger.warning(f"git diff with difftastic failed with code {result.returncode}: {result.stderr}")
            return None

        output = result.stdout.strip()

        if not output:
            logger.debug("difftastic produced no output")
            return None

        logger.debug(f"difftastic output length: {len(output)} characters")
        return output

    except subprocess.TimeoutExpired:
        logger.warning("difftastic timed out after 60 seconds")
        return None
    except subprocess.CalledProcessError as e:
        logger.warning(f"difftastic failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error running difftastic: {e}")
        return None


def get_difftastic_diff(excluded_files: list[str] = None) -> Optional[str]:
    """
    Get semantic diff using difftastic with fallback handling.

    This is the main entry point for getting a difftastic diff. It handles
    detection, execution, and error cases gracefully.

    Args:
        excluded_files: List of file patterns to exclude from diff

    Returns:
        Difftastic output string, or None if unavailable/failed.
    """
    # Check if difftastic is available
    version = check_difftastic_version()
    if not version:
        logger.warning(
            "difftastic was requested but is not installed. "
            "Falling back to standard git diff. "
            "Install difftastic to get syntax-aware diffs:\n"
            "  macOS:   brew install difftastic\n"
            "  Linux:   cargo install difftastic\n"
            "  Windows: cargo install difftastic\n"
            "  Or download from: https://github.com/Wilfred/difftastic/releases"
        )
        return None

    logger.info(f"Using difftastic for syntax-aware diff analysis ({version})")

    return run_difftastic_on_staged(excluded_files)
