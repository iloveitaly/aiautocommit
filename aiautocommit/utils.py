import subprocess
from pathlib import Path
from typing import List, Optional, Union

from .log import log


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
