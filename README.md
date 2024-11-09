[![Release Notes](https://img.shields.io/github/release/iloveitaly/aiautocommit)](https://github.com/iloveitaly/aiautocommit/releases) [![Downloads](https://static.pepy.tech/badge/aiautocommit/month)](https://pepy.tech/project/aiautocommit) [![Python Versions](https://img.shields.io/pypi/pyversions/aiautocommit)](https://pypi.org/project/aiautocommit) ![GitHub CI Status](https://github.com/iloveitaly/aiautocommit/actions/workflows/build_and_publish.yml/badge.svg) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# aiautocommit

Generate intelligent commit messages using AI. aiautocommit analyzes your staged changes and creates conventional commit messages, handling both small tweaks and large changesets effectively.

Yes, there are a lot of these. Main ways this is different:

* Simple codebase
* Ability to easily customize prompts on a per-repo basis

## Installation

```shell
pip install aiautocommit
```

## Features

* Generates conventional commit messages
* Customizable prompts and exclusions
* Pre-commit hook integration
* Supports custom config directories

## Getting Started

Set your OpenAI API key:

```
export OPENAI_API_KEY=<YOUR API KEY>
```

Stage your changes and run aiautocommit:

```
git add .
aiautocommit
```

## Customization

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

* `diff_prompt.txt`: Template for generating diff summaries
* `commit_prompt.txt`: Template for generating commit messages
* `exclusions.txt`: List of files to exclude from processing

### Installing Pre-commit Hook

To automatically generate commit messages during git commits:

```
aiautocommit install-pre-commit
```

### Environment Variables

* `OPENAI_API_KEY`: Your OpenAI API key
* `aiautocommit_MODEL`: AI model to use (default: gpt-4-mini)
* `aiautocommit_CONFIG`: Custom config directory path
* `LOG_LEVEL`: Logging verbosity
* `aiautocommit_LOG_PATH`: Custom log file path

## Privacy Disclaimer

`gpt-commit` uses the [OpenAI API](https://platform.openai.com/docs) to generate commit messages. Both file names and contents from files that contain staged changes will be shared with OpenAI when using `gpt-commit`. OpenAI will process this data according to their [terms of use](https://openai.com/policies/terms-of-use) and [API data usage policies](https://openai.com/policies/api-data-usage-policies). On March 1st 2023 OpenAI pledged that by default, they would not use data submitted by customers via their API to train or improve their models, and that this data will be retained for a maximum of 30 days, after which it will be deleted.

## Special Thanks

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