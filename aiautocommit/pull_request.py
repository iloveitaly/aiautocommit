import json
import os
import re
import shutil
import time
from pathlib import Path

from .log import log
from .utils import is_default_branch, run_command

# Cache durations in seconds
PR_CONTENT_CACHE_TTL = 7200  # 2 hours
NEGATIVE_CACHE_TTL = 3600  # 1 hour


def get_git_dir() -> Path | None:
    try:
        return Path(
            run_command(["git", "rev-parse", "--git-dir"], check=True).stdout.strip()
        )
    except Exception:
        return None


def get_pr_number_from_git_config(branch: str) -> str | None:
    """Check git config for a stored PR number."""
    try:
        result = run_command(
            ["git", "config", "--get", f"branch.{branch}.pr-number"],
            check=True,
        )
        if result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    # Check upstream tracking ref for a PR number
    try:
        result = run_command(
            ["git", "config", "--get", f"branch.{branch}.merge"],
            check=True,
        )
        ref = result.stdout.strip()
        # GitHub uses refs/pull/123/head or similar
        match = re.search(r"refs/pull/(\d+)/head", ref)
        if match:
            return match.group(1)
    except Exception:
        pass

    return None


def get_pull_request_context(branch: str) -> str | None:
    """
    Fetch the pull request context for the given branch.
    Requires AIAUTOCOMMIT_INCLUDE_PR_CONTEXT environment variable to be truthy.
    """
    if os.environ.get("AIAUTOCOMMIT_INCLUDE_PR_CONTEXT", "false").lower() not in (
        "1",
        "true",
        "t",
    ):
        return None

    if not branch:
        return None

    if is_default_branch(branch):
        log.debug(f"On default branch '{branch}', skipping PR context fetch")
        return None

    git_dir = get_git_dir()
    if not git_dir:
        return None

    cache_dir = git_dir / "aiautocommit"
    cache_dir.mkdir(parents=True, exist_ok=True)

    pr_number = get_pr_number_from_git_config(branch)
    if pr_number:
        log.debug(f"Found PR #{pr_number} in git config for branch {branch}")

    # Check for negative cache
    # To prevent slow `gh` calls on branches without PRs
    # We create a not_found marker
    safe_branch = re.sub(r"[^a-zA-Z0-9_.-]", "_", branch)
    not_found_cache = cache_dir / f"not_found_{safe_branch}_pull_request.md"

    if not pr_number and not_found_cache.exists():
        # Check if the cache is still valid
        if time.time() - not_found_cache.stat().st_mtime < NEGATIVE_CACHE_TTL:
            log.debug(f"Hit negative cache for branch {branch}, skipping PR fetch")
            return None
        else:
            # Stale negative cache, remove it
            not_found_cache.unlink(missing_ok=True)

    # If we have a PR number, check the cache
    if pr_number:
        cache_file = cache_dir / f"{pr_number}_pull_request.md"
        if cache_file.exists():
            # Check if the cache is still valid
            if time.time() - cache_file.stat().st_mtime < PR_CONTENT_CACHE_TTL:
                log.debug(f"Hit PR cache for PR #{pr_number}")
                return cache_file.read_text(encoding="utf-8")
            else:
                # Stale cache, we'll fetch a fresh copy
                cache_file.unlink(missing_ok=True)

    # Fallback: Query GitHub API via gh
    if not shutil.which("gh"):
        log.error(
            "GitHub CLI (gh) is not installed or not in PATH, but AIAUTOCOMMIT_INCLUDE_PR_CONTEXT is enabled."
        )
        return None

    try:
        # Use branch name if we don't have a PR number
        target = pr_number if pr_number else branch

        log.debug(f"Querying GitHub API for PR info on {target}")
        result = run_command(
            ["gh", "pr", "view", target, "--json", "number,title,body"],
            check=False,
        )

        if result.returncode == 0:
            pr_data = json.loads(result.stdout)
            number = str(pr_data.get("number"))
            title = pr_data.get("title", "")
            body = pr_data.get("body", "")

            # Save PR number to git config for next time
            if not pr_number:
                run_command(
                    ["git", "config", "--local", f"branch.{branch}.pr-number", number],
                    check=False,
                )

            md_content = f"<pull_request_title>PR #{number}: {title}</pull_request_title>\n<pull_request_description>\n{body}\n</pull_request_description>\n"

            # Cache the PR description
            cache_file = cache_dir / f"{number}_pull_request.md"
            cache_file.write_text(md_content, encoding="utf-8")

            return md_content
        else:
            # PR not found or error, create negative cache
            not_found_cache.write_text("<!-- error: not_found -->\n", encoding="utf-8")
            return None

    except Exception as e:
        log.debug(f"Failed to fetch PR info: {e}")
        return None
