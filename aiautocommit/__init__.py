import logging
import os
import subprocess
import sys
import warnings
from pathlib import Path

import click
from openai import OpenAI

# Config file locations in priority order
CONFIG_PATHS = [
    Path(".aiautocommit"),  # $PWD/.aiautocommit
    Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
    / "aiautocommit",  # XDG config dir
    Path(os.environ.get("AIAUTOCOMMIT_CONFIG", "")),  # Custom config path
]

COMMIT_PROMPT_FILE = "commit_prompt.txt"
EXCLUSIONS_FILE = "exclusions.txt"
COMMIT_SUFFIX_FILE = "commit_suffix.txt"

# https://platform.openai.com/docs/models
# gpt-4o-mini is cheaper, basically free
MODEL_NAME = os.environ.get("AIAUTOCOMMIT_MODEL", "gpt-4o")

COMMIT_PROMPT = """
You are a expert senior software developer.

Generate a commit message from the `git diff` output below using the following rules:

1. **Subject Line**:

   - Use a conventional commit prefix (e.g., `feat`, `fix`, `docs`, `style`, `refactor`, `build`, `deploy`).
     - Use `docs` if **documentation files** (like `.md`, `.rst`, or documentation comments in code) are the **only files changed**, even if they include code examples.
     - Use `docs` if **comments in code** are the **only changes made**.
     - Use `style` for **formatting**, **code style**, **linting**, or related configuration changes within code files.
     - Use `refactor` only for changes that do not alter behavior but improve the code structure.
     - Use `build` when updating **build scripts**, **configuration files**, or **build system setup** (e.g., `Makefile`, `Justfile`, `package.json`).
     - Use `deploy` when updating deployment scripts.
     - Do not use `feat` for changes that users wouldn't notice.
   - Limit the subject line to **50 characters** after the conventional commit prefix.
   - Write the subject in the **imperative mood**, as if completing the sentence "If applied, this commit will...".
   - Analyze **all changes**, including modifications in build scripts and configurations, when determining the commit message.

2. **Extended Commit Message**:

   - **Do not include an extended commit message** if the changes are **documentation-only**, involve **comment updates**, **simple formatting changes**, or are **not complex**.
   - Include an extended commit message **only if the diff is complex and affects functionality or build processes**.
   - Do not nest bullets
   - **Do not** write more than three bullets, choose the most important couple changes to expand on
   - In the extended message:
     - Focus on **what** and **why**, not **how** (the code explains how).
     - Use **markdown bullet points** to describe changes.
     - Explain the **problem** the commit solves and the reasons for the change.
     - Mention any **side effects** or important considerations.
     - **Do not include descriptions of trivial formatting or comment changes** in the extended message.

3. **General Guidelines**:

   - Do **not** wrap the output in a code block.
   - Do **not** include obvious statements easily inferred from the diff.
   - **Simplify** general statements. For example:
     - Replace "update dependency versions in package.json and pnpm.lock" with "update dependencies".
     - Replace "These changes resolve..." with "Resolved...".
   - **Handling Formatting Changes**:
     - If simple formatting updates (like changing quotes, code reformatting) are the **only changes** in code files, use the subject line "style: formatting update".
     - **Do not** treat changes in build scripts or configurations that affect functionality as mere formatting changes. They should be described appropriately.
   - Focus on code changes above comment or documentation updates

4. **File Type Hints**:

   - Recognize that a `Justfile` is like a `Makefile` and is part of the **build system**.
   - Changes to the build system are significant and should be reflected in the commit message.
   - Recognize other build-related files (e.g., `Dockerfile`, `package.json`, `webpack.config.js`) as part of the build or configuration.

5. **Avoid Verbose Details**:

   - Do not mention specific variables or excessive details.
   - Keep the commit message concise and focused on the overall changes.

6. **Focus on Functionality Over Documentation**:

   - If both documentation and functionality are modified, **emphasize the functional changes**.

7. **Insufficient Information**:

   - If there isn't enough information to generate a summary, **return an empty string**.

8. **Scopes**:

   - A scope is not required. Do not include one unless you are confident about your choice.
   - Scopes should formatted as `category(scope):` (e.g., `feat(api):`).
   - Use `migrations` if the change involves database migrations.

## Example 1

```
diff --git c/.tmux-shell.sh i/.tmux-shell.sh
index a34433f..01d2e9f 100755
--- c/.tmux-shell.sh
+++ i/.tmux-shell.sh
@@ -14,8 +14,8 @@ while [[ $counter -lt 20 ]]; do
   session="${session_uid}-${counter}"
 
   # if the session doesn't exist, create it
-  if ! tmux has-session -t "$session" 2>/dev/null; then
-    tmux new -ADs "$session"
+  if ! /opt/homebrew/bin/tmux has-session -t "$session" 2>/dev/null; then
+    /opt/homebrew/bin/tmux new -ADs "$session"
     break
   fi
```

This diff is short and should have no extended commit message.

Example commit message:

fix: use full path to tmux in .tmux-shell.sh

## Example 2

```
diff --git a/.git-functions b/.git-functions
index ba4be51..2bbb33b 100644
--- a/.git-functions
+++ b/.git-functions
@@ -108,7 +108,7 @@ github_reopen_pr() {
   gh pr create --web --repo "$REPO" --title "$TITLE" --body "$BODY" --head "$HEAD_REPO_OWNER:$HEAD_REF" --base "$BASE_BRANCH"
 }
 
-# add a license to an existing project/repo
+# add a license to an existing project/repo, both as a license file and license metadata
 add_mit_license() {
   # Check if the current folder is tied to a GitHub repository
   if ! gh repo view >/dev/null 2>&1; then
@@ -148,7 +148,8 @@ add_mit_license() {
   echo "MIT License added to the repository."
 }
 
-# render readme content on clipboard and replace username and password
+# render readme content on clipboard and replace username and repo
+# useful for custom templates I have in my notes
 render-git-template() {
   local GH_USERNAME=$(gh repo view --json owner --jq '.owner.login' | tr -d '[:space:]')
   local GH_REPO=$(gh repo view --json name --jq '.name' | tr -d '[:space:]')
@@ -158,3 +159,22 @@ render-git-template() {
   TEMPLATE=${TEMPLATE//REPO/$GH_REPO}
   echo $TEMPLATE | tr -ds '\n' ' '
 }
+
+# extracts all file(s) in a git repo path into PWD. Helpful for lifting source from an existing open source project.
+# usage: git-extract https://github.com/vantezzen/shadcn-registry-template/blob/main/scripts/
+git-extract() {
+  local url=$1
+  # Extract owner/repo/branch/path from GitHub URL
+  local parts=(${(s:/:)${url/https:\/\/github.com\//}})
+  local owner=$parts[1]
+  local repo=$parts[2] 
+  local branch=$parts[4]
+  local filepath=${(j:/:)parts[5,-1]}
+  
+  # Build tarball URL and folder name
+  local tarball="https://github.com/$owner/$repo/archive/refs/heads/$branch.tar.gz"
+  local foldername="$repo-$branch"
+  
+  # Extract just the specified path
+  curl -L $tarball | tar xz --strip=1 "$foldername/$filepath"
+}
\ No newline at end of file
```

This diff is short and should have no extended commit message. The updated comments of `render-git-template` and 
`update-mit-license` should be ignored when writing the commit message.

Example commit message:

feat: git-extract function to download a folder or file from a git repo

## Example 3

```
8083521 (17 seconds ago) feat: enhance SAS token generation and add new upload endpoints <Michael Bianco>
- Introduced `UploadType` enum to support multiple upload scenarios.
- Updated SAS token generation to handle different upload types.
- Added new API endpoints for generating signed URLs and handling uploads for example notes and intakes.
- Updated existing visit audio file upload process to align with new structure.
- Included doctor information in upload processes to store metadata and queue processing jobs.
- Modified settings route to fetch and return notes schema for the current doctor.

Generated-by: aiautocommit


diff --git a/app/commands/uploads/sas.py b/app/commands/uploads/sas.py
index cdfde5c..d9d55ab 100644
--- a/app/commands/uploads/sas.py
+++ b/app/commands/uploads/sas.py
@@ -1,4 +1,5 @@
-from datetime import datetime, timedelta
+from datetime import datetime, timedelta, timezone
+from enum import Enum
 
 from azure.storage.blob import (
     AccountSasPermissions,
@@ -12,10 +13,17 @@ from app.configuration.azure import (
     AZURE_UPLOADS_ACCOUNT_NAME,
     AZURE_UPLOADS_ACCOUNT_URL,
     AZURE_UPLOADS_CONTAINER_NAME,
+    AZURE_UPLOADS_EXAMPLE_NOTES_CONTAINER_NAME,
 )
 
 
-def perform() -> str:
+class UploadType(Enum):
+    VISIT = AZURE_UPLOADS_CONTAINER_NAME
+    EXAMPLE_NOTE = AZURE_UPLOADS_EXAMPLE_NOTES_CONTAINER_NAME
+    EXAMPLE_INTAKE = "to_implement"
+
+
+def perform(upload_type: UploadType) -> str:
     \"\"\"
     Generate a SAS token for uploading files, like audio, to a azure storage blob.
 
@@ -28,11 +36,12 @@ def perform() -> str:
         account_key=AZURE_UPLOADS_ACCOUNT_KEY,
         resource_types=ResourceTypes(object=True),
         permission=AccountSasPermissions(write=True),
-        expiry=datetime.utcnow() + timedelta(hours=1),
+        # 1hr is arbitrary
+        expiry=datetime.now(timezone.utc) + timedelta(hours=1),
     )
 
     container_client = ContainerClient(
-        container_name=AZURE_UPLOADS_CONTAINER_NAME,
+        container_name=upload_type.value,
         account_url=AZURE_UPLOADS_ACCOUNT_URL,
         credential=sas_token,
     )
diff --git a/app/routes/internal.py b/app/routes/internal.py
index 60104db..2dc05b4 100644
--- a/app/routes/internal.py
+++ b/app/routes/internal.py
@@ -1,10 +1,13 @@
 from typing import Annotated
 
 from fastapi import APIRouter, Depends, Path, Request
+from openai.types import Upload
 from pydantic import BaseModel, computed_field
 
 import app.commands.uploads.sas
 import app.commands.uploads.upload_visit_audio_file
+import app.jobs.extract
+from app.commands.uploads.sas import UploadType
 
 from activemodel.session_manager import aglobal_session
 from activemodel.types import TypeIDType
@@ -12,6 +15,8 @@ from app.models.ai_visit_note import AIVisitNote
 from app.models.ai_visit_transcript import AIVisitTranscript
 from app.models.appointment import Appointment
 from app.models.doctor import Doctor
+from app.models.doctor_note_file import DoctorNoteFile
+from app.models.doctor_note_schema import DoctorNoteSchema
 from app.models.patient import Patient
 
 from ..configuration.clerk import CLERK_PRIVATE_KEY
@@ -113,22 +118,66 @@ def note_detail(
     return note_detail
 
 
+# unique endpoints are used to generate the signed URLs, this is mostly an arbitrary choice. It probably adds an extra
+# added level of security and ability to evolve the upload flow in the future without modifying the frontend.
 @internal_api_app.post("/visit-audio-file/get-signed-url", response_model=str)
-def generate_signed_upload_url():
-    return app.commands.uploads.sas.perform()
+def generate_signed_visit_recording_upload_url():
+    return app.commands.uploads.sas.perform(UploadType.VISIT)
 
 
 @internal_api_app.post("/visit-audio-file/upload-complete")
 def upload_visit_audio_file(request: Request, file_name: str) -> None:
+    doctor: Doctor = request.state.doctor
+
     return app.commands.uploads.upload_visit_audio_file.perform(
-        user=request.state.user, blob_name=file_name
+        doctor=doctor,
+        blob_name=file_name,
+        # TODO add to upload process
+        patient_name="hi",
+        appointment_date="01-01-20101",
+        date_of_birth="01-01-20101",
     )
 
 
+@internal_api_app.post("/notes/get-signed-url", response_model=str)
+def generate_signed_example_note_upload_url():
+    return app.commands.uploads.sas.perform(UploadType.EXAMPLE_NOTE)
+
+
+@internal_api_app.post("/notes/upload-example")
+def upload_example_note(request: Request, file_name: str, note_type: str) -> None:
+    # TODO maybe accept ID as well?
+    doctor: Doctor = request.state.doctor
+
+    doctor_note_file = DoctorNoteFile(
+        doctor_id=doctor.id, azure_file_name=file_name, note_type=note_type
+    ).save()
+
+    app.jobs.extract.queue(doctor_note_file.id)
+
+
+@internal_api_app.post("/intake/get-signed-url", response_model=str)
+def generate_signed_example_intake_upload_url():
+    return app.commands.uploads.sas.perform(UploadType.EXAMPLE_INTAKE)
+
+
+@internal_api_app.post("/intake/upload-example")
+def upload_example_intake(request: Request, file_name: str) -> None:
+    doctor: Doctor = request.state.doctor
+    raise NotImplementedError()
+
+
 class SettingsData(BaseModel, extra="forbid"):
-    settings: dict
+    notes_schema: list[DoctorNoteSchema]
+    # TODO add intake schema
 
 
 @internal_api_app.get("/settings")
-def settings_data() -> SettingsData:
-    return SettingsData(settings={})
+def settings_data(request: Request) -> SettingsData:
+    doctor: Doctor = request.state.doctor
+
+    notes_schema = (
+        DoctorNoteSchema.select().where(DoctorNoteSchema.doctor_id == doctor.id).all()
+    )
+
+    return SettingsData(notes_schema=list(notes_schema))
diff --git a/web/app/components/VisitNoteViewer.tsx b/web/app/components/VisitNoteViewer.tsx
index a31db12..d487410 100644
--- a/web/app/components/VisitNoteViewer.tsx
+++ b/web/app/components/VisitNoteViewer.tsx
@@ -12,8 +12,6 @@ import {
 import { CopyButton } from "~/components/shared/CopyButton"
 import { AIVisitNote } from "~/configuration/client"
 
-import ReactDOMServer from "react-dom/server"
-
 export default function VisitNoteViewer({
   note,
   defaultOpen = false,
```

This diff is medium sized and should have no extended commit message.

Example commit message:

feat: sas for multiple storage containers, upload endpoints and expanded settings endpoint
"""


# trailers are a native git feature that can be used to add metadata to a commit
# https://git-scm.com/docs/git-interpret-trailers
# let's indicate that this message was generated by aiautocommit
COMMIT_SUFFIX = """

Generated-by: aiautocommit
"""

# TODO should we ignore files without an extension? can we detect binary files?
EXCLUDED_FILES = [
    "Gemfile.lock",
    "uv.lock",
    "poetry.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "pnpm-lock.yaml",
    "composer.lock",
    "cargo.lock",
    "mix.lock",
    "Pipfile.lock",
    "pdm.lock",
    "flake.lock",
    "bun.lockb",
    ".terraform.lock.hcl",
]

# characters, not tokens
PROMPT_CUTOFF = 10_000

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    **(
        {"filename": os.environ.get("AIAUTOCOMMIT_LOG_PATH")}
        if os.environ.get("AIAUTOCOMMIT_LOG_PATH")
        else {"stream": sys.stderr}
    ),
)

# this is called within py dev environments. Unless it looks like we are explicitly debugging aiautocommit, we force a
# more silent operation. Checking for AIAUTOCOMMIT_LOG_PATH is not a perfect heuristic, but it works for now.
if not os.environ.get("AIAUTOCOMMIT_LOG_PATH"):
    # Suppress ResourceWarnings
    warnings.filterwarnings("ignore", category=ResourceWarning)

    # Optional: Disable httpx logging if desired
    logging.getLogger("httpx").setLevel(logging.WARNING)

# allow a unique API key to be set for OpenAI, for tracking/costing
if os.environ.get("AIAUTOCOMMIT_OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.environ["AIAUTOCOMMIT_OPENAI_API_KEY"]


def configure_prompts(config_dir=None):
    global DIFF_PROMPT, COMMIT_MSG_PROMPT, EXCLUDED_FILES, CONFIG_PATHS

    if config_dir:
        CONFIG_PATHS.insert(0, Path(config_dir))

    # Find first existing config dir
    config_dir = next((path for path in CONFIG_PATHS if path and path.exists()), None)

    if not config_dir:
        logging.debug("No config directory found")
        return

    logging.debug(f"Found config directory at {config_dir}")

    # Load commit prompt
    commit_file = config_dir / COMMIT_PROMPT_FILE
    if commit_file.exists():
        logging.debug("Loading custom commit prompt from commit.txt")
        COMMIT_MSG_PROMPT = commit_file.read_text().strip()

    # Load exclusions
    exclusions_file = config_dir / EXCLUSIONS_FILE
    if exclusions_file.exists():
        logging.debug("Loading custom exclusions from exclusions.txt")
        EXCLUDED_FILES = [
            line.strip()
            for line in exclusions_file.read_text().splitlines()
            if line.strip()
        ]

    # Load commit suffix
    commit_suffix_file = config_dir / COMMIT_SUFFIX_FILE
    if commit_suffix_file.exists():
        logging.debug("Loading custom commit suffix from commit_suffix.txt")
        global COMMIT_SUFFIX
        COMMIT_SUFFIX = commit_suffix_file.read_text().strip()


def get_diff(ignore_whitespace=True):
    arguments = [
        "git",
        "--no-pager",
        "diff",
        "--staged",
    ]
    if ignore_whitespace:
        arguments += [
            "--ignore-space-change",
            "--ignore-blank-lines",
        ]

    for file in EXCLUDED_FILES:
        arguments += [f":(exclude){file}"]

    diff_process = subprocess.run(arguments, capture_output=True, text=True)
    diff_process.check_returncode()
    normalized_diff = diff_process.stdout.strip()

    logging.debug(f"Discovered Diff:\n{normalized_diff}")

    return normalized_diff


def complete(prompt, diff):
    if len(diff) > PROMPT_CUTOFF:
        logging.warning(
            f"Prompt length ({len(diff)}) exceeds the maximum allowed length, truncating."
        )

    client = OpenAI()
    completion_resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": diff[:PROMPT_CUTOFF]},
        ],
        # TODO this seems awfully small?
        # max_completion_tokens=128,
    )

    completion = completion_resp.choices[0].message.content.strip()
    return completion


def generate_commit_message(diff):
    if not diff:
        logging.debug("No commit message generated")
        return ""

    return (complete(COMMIT_PROMPT, diff)) + COMMIT_SUFFIX


def git_commit(message):
    # will ignore message if diff is empty
    return subprocess.run(["git", "commit", "--message", message, "--edit"]).returncode


def is_reversion():
    # Check if we're in the middle of a git revert
    if (Path(".git") / "REVERT_HEAD").exists():
        return True

    if (Path(".git") / "MERGE_MSG").exists():
        return True

    return False


@click.group(invoke_without_command=True)
def main():
    """
    Generate a commit message for staged files and commit them.
    Git will prompt you to edit the generated commit message.
    """
    ctx = click.get_current_context()
    if ctx.invoked_subcommand is None:
        ctx.invoke(commit)


@main.command()
@click.option(
    "-p",
    "--print-message",
    is_flag=True,
    default=False,
    help="print commit msg to stdout instead of performing commit",
)
@click.option(
    "-o",
    "--output-file",
    type=click.Path(writable=True),
    help="write commit message to specified file",
)
@click.option(
    "--config-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="specify custom config directory",
)
def commit(print_message, output_file, config_dir):
    """
    Generate commit message from git diff.
    """

    if is_reversion():
        return 0

    configure_prompts(config_dir)

    try:
        if not get_diff(ignore_whitespace=False):
            click.echo(
                "No changes staged. Use `git add` to stage files before invoking gpt-commit.",
                err=True,
            )
            return 1

        commit_message = generate_commit_message(get_diff())
    except UnicodeDecodeError:
        click.echo("aiautocommit does not support binary files", err=True)

        commit_message = (
            # TODO use heredoc
            "# gpt-commit does not support binary files. "
            "Please enter a commit message manually or unstage any binary files."
        )

    if output_file:
        if commit_message:
            Path(output_file).write_text(commit_message)
            return 0
        return 1
    elif print_message:
        click.echo(commit_message)
        return 0
    else:
        return git_commit(commit_message)


@main.command()
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing pre-commit hook if it exists",
)
def install_pre_commit(overwrite):
    """Install pre-commit script into git hooks directory"""
    git_result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
    )
    git_result.check_returncode()

    git_dir = git_result.stdout.strip()

    target_hooks_dir = Path(git_dir) / "hooks"
    target_hooks_dir.mkdir(exist_ok=True)

    commit_msg_git_hook_name = "prepare-commit-msg"
    pre_commit = target_hooks_dir / commit_msg_git_hook_name
    pre_commit_script = Path(__file__).parent / commit_msg_git_hook_name

    if not pre_commit.exists() or overwrite:
        pre_commit.write_text(pre_commit_script.read_text())
        pre_commit.chmod(0o755)
        click.echo("Installed pre-commit hook")
    else:
        click.echo(
            "pre-commit hook already exists. Here's the contents we would have written:"
        )
        click.echo(pre_commit_script.read_text())


@main.command()
def dump_prompts():
    """Dump default prompts into .aiautocommit directory for easy customization"""
    config_dir = Path(".aiautocommit")
    config_dir.mkdir(exist_ok=True)

    commit_prompt = config_dir / COMMIT_PROMPT_FILE
    exclusions = config_dir / EXCLUSIONS_FILE
    commit_suffix = config_dir / COMMIT_SUFFIX_FILE

    if not commit_prompt.exists():
        commit_prompt.write_text(COMMIT_MSG_PROMPT)
    if not exclusions.exists():
        exclusions.write_text("\n".join(EXCLUDED_FILES))
    if not commit_suffix.exists():
        commit_suffix.write_text(COMMIT_SUFFIX)

    click.echo(
        f"""Dumped default prompts to .aiautocommit directory:

- {COMMIT_PROMPT_FILE}: Template for generating commit messages
- {EXCLUSIONS_FILE}: List of file patterns to exclude from processing
- {COMMIT_SUFFIX}: Text appended to the end of every commit message
"""
    )
