"""
Difftastic integration for semantic diff analysis.

This module provides functionality to shell out to the difftastic CLI tool
for syntax-aware structural diffing, with graceful fallback to standard git diff.
"""

import logging
import os
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


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
    difft_path = shutil.which("difft")
    if not difft_path:
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

    logger.info("Using difftastic for syntax-aware diff analysis")

    excluded_files = excluded_files or []

    try:
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

        logger.debug(f"Running git diff with difftastic: {' '.join(cmd)}")

        # Set up environment to use difftastic as external diff
        env = os.environ.copy()
        env["GIT_EXTERNAL_DIFF"] = difft_path
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
