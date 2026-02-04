import os
import unittest
import pytest
from unittest.mock import patch
from click.testing import CliRunner
from aiautocommit import main
from tests.utils import GitTestMixin


@pytest.mark.integration
class TestIntegration(unittest.TestCase, GitTestMixin):
    def setUp(self):
        self.runner = CliRunner()
        self.model_name = os.environ.get("AIAUTOCOMMIT_MODEL", "gemini:gemini-flash-latest")

        # Verify we have an API key for integration tests
        if os.environ.get("OPENAI_API_KEY"):
            pass
        elif os.environ.get("GEMINI_API_KEY"):
            pass
        elif os.environ.get("AZURE_OPENAI_API_KEY") and os.environ.get(
            "AZURE_OPENAI_ENDPOINT"
        ):
            # Configure for Azure if available
            # If AIAUTOCOMMIT_MODEL is not set to an azure model, we can't guess the deployment
            if not self.model_name.startswith("azure:"):
                self.skipTest(
                    "Azure keys present but AIAUTOCOMMIT_MODEL not set to 'azure:<deployment>'. Skipping integration test."
                )
        else:
            self.skipTest(
                "No valid API key (OPENAI_API_KEY, GEMINI_API_KEY, or AZURE_OPENAI_*) set, skipping integration test"
            )

    def test_full_generation_cycle(self):
        """
        Test the full cycle with a real LLM call.
        This verifies that pydantic-ai is correctly configured and can talk to the configured AI provider.
        """
        # Patch the MODEL_NAME in the module to ensure our test model selection is used
        with patch("aiautocommit.MODEL_NAME", self.model_name):
            with self.runner.isolated_filesystem():
                self.init_repo()

                # Create initial file
                self.create_file("main.py", "print('hello world')\n")
                self.git_add("main.py")
                self.git_commit("initial commit")

                # Make a meaningful change that should generate a clear commit message
                self.create_file("main.py", "print('hello universe')\n")
                self.git_add("main.py")

                # Run command with --print-message to avoid opening editor
                # Enable debug logging to diagnose issues
                result = self.runner.invoke(
                    main,
                    ["commit", "--print-message"],
                    env={"LOG_LEVEL": "DEBUG", **os.environ},
                )

                # Assertions
                if result.exit_code != 0:
                    print(f"Command failed with exit code {result.exit_code}")
                    print(f"Output: {result.output}")
                    if result.exception:
                        print(f"Exception: {result.exception}")
                self.assertEqual(result.exit_code, 0)

                # The message should be non-empty and not the fallback "style: whitespace change"
                message = result.output.strip()
                if not message:
                    print(
                        f"DEBUG: Output was empty. Full result output:\n{result.output}"
                    )
                    print(f"DEBUG: Using model: {self.model_name}")

                self.assertTrue(message)
                self.assertNotEqual(message, "style: whitespace change")

                # It should look like a commit message (basic check)
                print(f"\nGenerated message: {message}")
