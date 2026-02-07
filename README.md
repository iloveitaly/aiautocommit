[![Release Notes](https://img.shields.io/github/release/iloveitaly/aiautocommit)](https://github.com/iloveitaly/aiautocommit/releases)
[![Downloads](https://static.pepy.tech/badge/aiautocommit/month)](https://pepy.tech/project/aiautocommit)
![GitHub CI Status](https://github.com/iloveitaly/aiautocommit/actions/workflows/build_and_publish.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Generate Commit Messages With AI

`aiautocommit` analyzes your staged changes and creates conventional commit messages, handling both small tweaks and large changesets effectively.

Yes, there are a lot of these. Main ways this is different:


* Ability to easily customize prompts on a per-repo basis

## Installation

```
uvx aiautocommit
```

> **Note**: OpenAI, Anthropic, and Gemini (Google) are supported by default. To install all providers supported by Pydantic AI, use `pip install "aiautocommit[all-providers]"`.

## Features

* Generates conventional commit messages
* Customizable prompts and exclusions
* Pre-commit hook integration
* Supports custom config directories
* CLI flag for version checking (`--version`)
* Does not generate a commit during a merge or reversion (when an existing autogen'd msg exists)
* **Automatic lock file handling**: recognizable lock files (e.g., `uv.lock`, `package-lock.json`) generate specific conventional messages (e.g., `chore(deps): update uv.lock`) even when they are excluded from the AI prompt.
* **Optional difftastic integration** for syntax-aware semantic diffs

## Getting Started

Set your API key (works for any provider, Google Gemini is the default):

```shell
export AIAUTOCOMMIT_AI_KEY=<YOUR API KEY>
```

Stage your changes and run aiautocommit:

```shell
git add .

# this will generate a commit message and commit the changes
aiautocommit commit

# or, just to see what it will do
aiautocommit commit --print-message
```

Using the CLI directly is the best way to debug and tinker with the project as well.

## Difftastic Integration (Optional)

aiautocommit can optionally use [difftastic](https://github.com/Wilfred/difftastic) for syntax-aware diffs that understand code structure rather than just line-by-line changes. This helps the AI distinguish between refactoring (variable renames, code movement) and actual functional changes, leading to more accurate commit messages. Install with `brew install difftastic` (macOS) or `cargo install difftastic` (Linux/Windows), then enable with:

```shell
aiautocommit commit --difftastic
```

## Automatic Lock File Handling

Lock files (like `uv.lock`, `package-lock.json`, `Gemfile.lock`, etc.) are frequently updated but don't provide much context for an AI-generated message. By default, these are excluded from the AI prompt to save tokens and improve quality.

However, if you stage *only* lock files, aiautocommit will detect them and automatically generate a conventional commit message:

- `uv.lock` -> `chore(deps): update uv.lock`
- `package-lock.json` -> `chore(deps): update package-lock.json`
- `.terraform.lock.hcl` -> `chore(deps): update .terraform.lock.hcl`
- Mixed lock files -> `chore(deps): update lock files`

If any non-lock files are staged alongside them, the AI will ignore the lock files (based on your exclusions) and focus on the meaningful code changes.

## Customization

### Logging

First, you'll want to enable logging so you can extract the diff and prompt and iterate on it in ChatGPT:

```shell
export AIAUTOCOMMIT_LOG_LEVEL=DEBUG
export AIAUTOCOMMIT_LOG_PATH=aiautocommit.log
```

Now, you'll have a nice log you can tail and fiddle with from there.

### Using Config Directory

aiautocommit looks for configuration files in these locations (in priority order):

* .aiautocommit/ in current directory
* $XDG_CONFIG_HOME/aiautocommit/ (defaults to ~/.config/aiautocommit/)
* Custom path via aiautocommit_CONFIG environment variable

To get started with customization:

```shell
aiautocommit dump-prompts
```

This creates a `.aiautocommit/` directory with:

* `commit_prompt.txt`: Template for generating commit messages
* `excluded_files.txt`: List of files to exclude from processing
* `commit_suffix.txt`: Static suffix to append to commit messages. Useful for trailers.

### Installing Pre-commit Hook

To automatically generate commit messages during git commits:

```
aiautocommit install-pre-commit
```

[Learn more about git hooks here.](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)

### Customize Scopes

First, dump the prompts into your project:

```shell
aiautocommit dump-prompts
```

Then add your scope specification to the commit prompt:

```
#### 4. **Scopes**

Optional scopes (e.g., `feat(api):`):
- `api`: API endpoints, controllers, services.
- `frontend`: React components, styles, state management.
- `migration`: Database schema changes.
- `jobs`: Background jobs, scheduled tasks.
- `infra`: Infrastructure, networking, deployment, containerization.
- `prompt`: Updates to LLM or AI prompts.
```

#### Lefthook Configuration

[Lefthook](https://lefthook.dev) is an excellent tool for managing git hooks. To use aiautocommit with lefthook, add the following to your `.lefthook.yml`:

```yaml
prepare-commit-msg:
  commands:
    aiautocommit:
      run: aiautocommit commit --output-file "{1}"
      interactive: true
      env:
        # without this, lefthook will run in an infinite loop
        LEFTHOOK: 0
        # ensures that LOG_LEVEL config of the current project does not interfere with aiautocommit
        AIAUTOCOMMIT_LOG_LEVEL: info
      skip:
        merge:
        rebase:
        # only run this if the tool exists
        run: ! which aiautocommit > /dev/null
```

### Environment Variables

All environment variables used by `aiautocommit` or its providers can be prefixed with `AIAUTOCOMMIT_` to take precedence over the standard variable.

* `AIAUTOCOMMIT_AI_KEY`: **Universal API key.** `aiautocommit` internally maps this to the correct provider-specific variable (e.g., `GOOGLE_API_KEY`, `OPENAI_API_KEY`) based on your active model.
* `AIAUTOCOMMIT_MODEL`: AI model to use, in `provider:model` format (default: `gemini:gemini-3-flash-preview`). Examples: `anthropic:claude-3-5-sonnet-latest`, `openai:gpt-4o`.
* `AIAUTOCOMMIT_CONFIG`: Custom config directory path
* `AIAUTOCOMMIT_DIFFTASTIC`: Enable difftastic for syntax-aware diffs (set to "1", "true", or "yes")
* `AIAUTOCOMMIT_LOG_LEVEL`: Logging verbosity
* `AIAUTOCOMMIT_LOG_PATH`: Custom log file path

Ensure you have the corresponding API key set in `AIAUTOCOMMIT_AI_KEY`.

### Model Configuration

`aiautocommit` uses [pydantic-ai](https://ai.pydantic.dev/) under the hood, supporting a wide range of providers including OpenAI, Anthropic, and Gemini (via VertexAI or Generative AI) by default. You can specify the model using the `provider:model` syntax in the `AIAUTOCOMMIT_MODEL` environment variable.

Google Gemini models use "thinking" (Chain of Thought) with a minimal budget to improve accuracy.

Common examples:

* `gemini:gemini-3-flash-preview` (default)
* `openai:gpt-4o`
* `anthropic:claude-3-5-sonnet-latest`
* `gemini:gemini-1.5-pro`
* `ollama:llama3` (for local models)

Ensure you have the corresponding API key set in your environment (e.g., `ANTHROPIC_API_KEY` for Anthropic models).

## Writing Good Commit Messages

Some guides to writing good commit messages:

* https://cbea.ms/git-commit/
* https://groups.google.com/g/golang-dev/c/6M4dmZWpFaI
* https://github.com/RomuloOliveira/commit-messages-guide

## Credits

[This project](https://github.com/markuswt/gpt-commit) inspired this project. It had a very simple codebase. I've taken the idea and expanded it to include a lot more features, specifically per-project prompt customization.

## Related Projects

I looked at a bunch of projects before building this one.

- https://github.com/abi/aiautocommit - python, inactive. Many files, not simple.
- https://github.com/Sett17/turboCommit - rust, inactive.
- https://github.com/Nutlope/aicommits - typescript. Node is so slow and I hate working with it.
- https://github.com/Elhameed/aicommits - python
- https://github.com/zurawiki/gptcommit - active, rust. Too complicated and no prompt customization.
- https://github.com/ywkim/gpt-commit - lisp, inactive.
- https://github.com/markuswt/gpt-commit - single file, python based. No commits > 1yr. Very simple codebase.
- https://github.com/josenerydev/gpt-commit - also python
- https://github.com/di-sukharev/opencommit - has conventional commit structure

---

*This project was created from [iloveitaly/python-package-template](https://github.com/iloveitaly/python-package-template)*
