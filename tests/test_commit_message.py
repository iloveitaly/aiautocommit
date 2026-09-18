from unittest.mock import patch

from aiautocommit import generate_commit_message


def test_generate_commit_message_empty_diff():
    assert generate_commit_message("") == ""


def test_generate_commit_message_empty_completion():
    with patch("aiautocommit.complete", return_value=""):
        assert generate_commit_message("some diff") == ""


def test_generate_commit_message_quoted_empty():
    with patch("aiautocommit.complete", return_value='""'):
        assert generate_commit_message("some diff") == ""


def test_generate_commit_message_with_suffix():
    with patch("aiautocommit.complete", return_value="feat: test"):
        with patch("aiautocommit.COMMIT_SUFFIX", " [suffix]"):
            assert generate_commit_message("some diff") == "feat: test [suffix]"


def test_generate_commit_message_injects_xml_repo_information():
    captured = {}

    def fake_complete(prompt, diff):
        captured["prompt"] = prompt
        captured["diff"] = diff
        return "feat: test"

    with (
        patch("aiautocommit.complete", side_effect=fake_complete),
        patch("aiautocommit.get_current_branch", return_value="feature/xml-tags"),
        patch("aiautocommit.get_pull_request_context", return_value=None),
        patch(
            "aiautocommit.COMMIT_PROMPT",
            "base prompt\n\n<examples>\nexample\n</examples>",
        ),
        patch("aiautocommit.COMMIT_SUFFIX", ""),
    ):
        generate_commit_message("some diff")

    prompt = captured["prompt"]
    assert captured["diff"] == "some diff"
    assert prompt.startswith("base prompt")
    assert "<examples>" in prompt
    assert prompt.index("</examples>") < prompt.index("<repo_information>")
    assert "<branch>feature/xml-tags</branch>" in prompt
    assert "## Repo Information" not in prompt


def test_generate_commit_message_appends_repo_information_without_examples():
    captured = {}

    def fake_complete(prompt, diff):
        captured["prompt"] = prompt
        captured["diff"] = diff
        return "feat: test"

    with (
        patch("aiautocommit.complete", side_effect=fake_complete),
        patch("aiautocommit.get_current_branch", return_value="main"),
        patch(
            "aiautocommit.get_pull_request_context",
            return_value="<pull_request_title>PR #1: title</pull_request_title>\n",
        ),
        patch("aiautocommit.COMMIT_PROMPT", "base prompt only"),
        patch("aiautocommit.COMMIT_SUFFIX", ""),
    ):
        generate_commit_message("some diff")

    prompt = captured["prompt"]
    assert captured["diff"] == "some diff"
    assert prompt.startswith("base prompt only")
    assert "<branch>main</branch>" in prompt
    assert "<pull_request_title>PR #1: title</pull_request_title>" in prompt
    assert prompt.index("</repo_information>") > prompt.index(
        "<pull_request_title>PR #1: title</pull_request_title>"
    )
    assert "## Repo Information" not in prompt
