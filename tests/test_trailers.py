import subprocess
from unittest.mock import patch

from aiautocommit import (
    apply_commit_suffix,
    generate_commit_message,
    is_git_trailer,
    split_trailing_trailers,
)


def git_parse_trailers(message: str) -> list[str]:
    parsed = subprocess.check_output(
        ["git", "interpret-trailers", "--parse"],
        input=message,
        text=True,
    )
    return [line for line in parsed.splitlines() if line]


def test_is_git_trailer():
    assert is_git_trailer("Generated-by: aiautocommit")
    assert is_git_trailer("Dev-Note: LLM instructions have been updated")
    assert is_git_trailer("Co-authored-by: Name <a@b.c>")
    assert is_git_trailer("Signed-off-by: Me <me@x.com>")
    assert not is_git_trailer("- did a thing")
    assert not is_git_trailer("feat something")
    assert not is_git_trailer("custom suffix")


def test_apply_suffix_to_subject_only():
    result = apply_commit_suffix(
        "docs: update coding instructions", "Generated-by: aiautocommit"
    )
    assert result == ("docs: update coding instructions\n\nGenerated-by: aiautocommit")
    assert git_parse_trailers(result) == ["Generated-by: aiautocommit"]


def test_stack_llm_trailer_above_generated_by():
    message = (
        "docs: update coding instructions and guidelines\n"
        "\n"
        "Dev-Note: LLM instructions have been updated"
    )
    result = apply_commit_suffix(message, "Generated-by: aiautocommit")

    assert result == (
        "docs: update coding instructions and guidelines\n"
        "\n"
        "Dev-Note: LLM instructions have been updated\n"
        "Generated-by: aiautocommit"
    )
    assert git_parse_trailers(result) == [
        "Dev-Note: LLM instructions have been updated",
        "Generated-by: aiautocommit",
    ]


def test_blank_line_between_trailers_is_collapsed():
    message = (
        "docs: update coding instructions and guidelines\n"
        "\n"
        "Dev-Note: LLM instructions have been updated\n"
        "\n"
    )
    result = apply_commit_suffix(message, "Generated-by: aiautocommit")

    assert "Dev-Note: LLM instructions have been updated\nGenerated-by" in result
    assert "\n\nGenerated-by" not in result
    assert git_parse_trailers(result) == [
        "Dev-Note: LLM instructions have been updated",
        "Generated-by: aiautocommit",
    ]


def test_glued_trailer_after_conventional_subject():
    message = (
        "docs: update coding instructions and guidelines\n"
        "Dev-Note: LLM instructions have been updated"
    )
    result = apply_commit_suffix(message, "Generated-by: aiautocommit")

    assert result == (
        "docs: update coding instructions and guidelines\n"
        "\n"
        "Dev-Note: LLM instructions have been updated\n"
        "Generated-by: aiautocommit"
    )
    assert git_parse_trailers(result) == [
        "Dev-Note: LLM instructions have been updated",
        "Generated-by: aiautocommit",
    ]


def test_body_then_multiple_trailers():
    message = (
        "feat: add retry to webhook delivery\n"
        "\n"
        "- partner API is flaky on timeouts\n"
        "\n"
        "Dev-Note: retries are required by the partner SLA\n"
        "\n"
        "Signed-off-by: Dev <dev@example.com>"
    )
    result = apply_commit_suffix(message, "Generated-by: aiautocommit")

    assert result == (
        "feat: add retry to webhook delivery\n"
        "\n"
        "- partner API is flaky on timeouts\n"
        "\n"
        "Dev-Note: retries are required by the partner SLA\n"
        "Signed-off-by: Dev <dev@example.com>\n"
        "Generated-by: aiautocommit"
    )
    assert git_parse_trailers(result) == [
        "Dev-Note: retries are required by the partner SLA",
        "Signed-off-by: Dev <dev@example.com>",
        "Generated-by: aiautocommit",
    ]


def test_does_not_duplicate_existing_generated_by():
    message = "docs: tweak comments\n\nGenerated-by: aiautocommit"
    result = apply_commit_suffix(message, "Generated-by: aiautocommit")
    assert result.count("Generated-by: aiautocommit") == 1


def test_multiline_suffix_trailers_are_stacked():
    suffix = "Co-authored-by: Bot <bot@example.com>\nGenerated-by: aiautocommit"
    result = apply_commit_suffix("fix: handle empty payload", suffix)
    assert result == (
        "fix: handle empty payload\n"
        "\n"
        "Co-authored-by: Bot <bot@example.com>\n"
        "Generated-by: aiautocommit"
    )


def test_non_trailer_suffix_is_appended_as_a_block():
    result = apply_commit_suffix("feat: test", "custom suffix")
    assert result == "feat: test\n\n\ncustom suffix"


def test_split_does_not_treat_subject_as_trailer():
    body, trailers = split_trailing_trailers("feat: add login")
    assert body == "feat: add login"
    assert trailers == []


def test_generate_commit_message_stacks_trailers():
    llm = (
        "docs: update coding instructions and guidelines\n"
        "\n"
        "Dev-Note: LLM instructions have been updated"
    )
    with patch("aiautocommit.complete", return_value=llm):
        with patch("aiautocommit.COMMIT_SUFFIX", "Generated-by: aiautocommit"):
            result = generate_commit_message("some diff")

    assert result.endswith(
        "Dev-Note: LLM instructions have been updated\nGenerated-by: aiautocommit"
    )
    assert git_parse_trailers(result) == [
        "Dev-Note: LLM instructions have been updated",
        "Generated-by: aiautocommit",
    ]
