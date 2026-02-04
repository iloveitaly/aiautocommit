import unittest
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
