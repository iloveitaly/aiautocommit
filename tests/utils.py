import subprocess
import os

class GitTestMixin:
    """Mixin to provide git helper methods for tests."""

    def init_repo(self):
        """Initialize a fresh git repository with user config."""
        subprocess.check_call(["git", "init"])
        subprocess.check_call(["git", "config", "user.email", "test@example.com"])
        subprocess.check_call(["git", "config", "user.name", "Test User"])
        subprocess.check_call(["git", "config", "init.defaultBranch", "master"])

    def create_file(self, filename, content):
        """Create a file with specific content."""
        with open(filename, "w") as f:
            f.write(content)

    def git_add(self, filename):
        """Stage a file."""
        subprocess.check_call(["git", "add", filename])

    def git_commit(self, message):
        """Commit staged changes."""
        subprocess.check_call(["git", "commit", "-m", message])

    def cleanup_commit_editmsg(self):
        """Remove COMMIT_EDITMSG to avoid stale detection."""
        if os.path.exists(".git/COMMIT_EDITMSG"):
            os.remove(".git/COMMIT_EDITMSG")
