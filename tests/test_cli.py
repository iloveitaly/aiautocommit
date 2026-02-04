import unittest
from pathlib import Path
from click.testing import CliRunner
from aiautocommit import main
from tests.utils import GitTestMixin


class TestCli(unittest.TestCase, GitTestMixin):
    def setUp(self):
        self.runner = CliRunner()

    def test_whitespace_change(self):
        with self.runner.isolated_filesystem():
            self.init_repo()

            # Create initial file
            self.create_file("test.txt", "hello\n")
            self.git_add("test.txt")
            self.git_commit("initial")

            # Make whitespace change
            self.create_file("test.txt", "hello \n")
            self.git_add("test.txt")

            self.cleanup_commit_editmsg()

            # Run command
            result = self.runner.invoke(main, ["commit", "--print-message"])

            # Assertions
            self.assertEqual(result.exit_code, 0)
            self.assertIn("style: whitespace change", result.output)

    def test_no_changes(self):
        with self.runner.isolated_filesystem():
            self.init_repo()

            # Run command with no staged changes
            result = self.runner.invoke(main, ["commit", "--print-message"])

            # Assertions
            self.assertEqual(result.exit_code, 1)
            self.assertIn("No changes staged", result.output)

    def test_static_commit_python(self):
        with self.runner.isolated_filesystem():
            self.init_repo()

            # Create uv.lock (which is in excluded_files.txt by default in the package)
            # However, in tests, we are in an isolated filesystem.
            # aiautocommit finds the default config in the package directory.
            self.create_file("uv.lock", "content\n")
            self.git_add("uv.lock")

            self.cleanup_commit_editmsg()

            # Run command
            result = self.runner.invoke(main, ["commit", "--print-message"])

            # Assertions
            self.assertEqual(result.exit_code, 0)
            self.assertIn("chore(deps): update uv.lock", result.output)

    def test_static_commit_node(self):
        with self.runner.isolated_filesystem():
            self.init_repo()

            self.create_file("package-lock.json", "content\n")
            self.git_add("package-lock.json")

            self.cleanup_commit_editmsg()

            # Run command
            result = self.runner.invoke(main, ["commit", "--print-message"])

            # Assertions
            self.assertEqual(result.exit_code, 0)
            self.assertIn("chore(deps): update package-lock.json", result.output)

    def test_static_commit_mixed(self):
        with self.runner.isolated_filesystem():
            self.init_repo()

            self.create_file("uv.lock", "content\n")
            self.create_file("package-lock.json", "content\n")
            self.git_add("uv.lock")
            self.git_add("package-lock.json")

            self.cleanup_commit_editmsg()

            # Run command
            result = self.runner.invoke(main, ["commit", "--print-message"])

            # Assertions
            self.assertEqual(result.exit_code, 0)
            self.assertIn("chore(deps): update lock files", result.output)

    def test_lock_file_not_excluded(self):
        from unittest.mock import patch

        with self.runner.isolated_filesystem():
            self.init_repo()

            # Create a lock file that is NOT in the default excluded_files.txt
            config_dir = Path("config")
            config_dir.mkdir()
            (config_dir / "excluded_files.txt").write_text("")
            (config_dir / "commit_prompt.txt").write_text("Write 'AI message'")

            self.create_file("uv.lock", "content\n")
            self.git_add("uv.lock")

            self.cleanup_commit_editmsg()

            # Mock generate_commit_message to return a fixed string
            with patch(
                "aiautocommit.generate_commit_message", return_value="AI message"
            ):
                # Run command with custom config
                result = self.runner.invoke(
                    main, ["commit", "--print-message", "--config-dir", str(config_dir)]
                )

            # Assertions - should use AI because uv.lock is not excluded in this config
            self.assertEqual(result.exit_code, 0)
            self.assertIn("AI message", result.output)

    def test_static_commit_terraform(self):
        with self.runner.isolated_filesystem():
            self.init_repo()

            self.create_file(".terraform.lock.hcl", "content\n")
            self.git_add(".terraform.lock.hcl")

            self.cleanup_commit_editmsg()

            # Run command
            result = self.runner.invoke(main, ["commit", "--print-message"])

            # Assertions
            self.assertEqual(result.exit_code, 0)
            self.assertIn("chore(deps): update .terraform.lock.hcl", result.output)
