[![Release Notes](https://img.shields.io/github/release/iloveitaly/autocommit)](https://github.com/iloveitaly/autocommit/releases) [![Downloads](https://static.pepy.tech/badge/autocommit/month)](https://pepy.tech/project/autocommit) [![Python Versions](https://img.shields.io/pypi/pyversions/autocommit)](https://pypi.org/project/autocommit) ![GitHub CI Status](https://github.com/iloveitaly/autocommit/actions/workflows/build_and_publish.yml/badge.svg) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)%

# autocommit

Generate intelligent commit messages using AI. Autocommit analyzes your staged changes and creates conventional commit messages, handling both small tweaks and large changesets effectively.

Yes, there are a lot of these. Main ways this is different:

* Simple codebase
* Ability to easily customize prompts on a per-repo basis

## Installation

```shell
pip install autocommit
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

Stage your changes and run autocommit:

```
git add .
autocommit
```

## Customization

### Using Config Directory

Autocommit looks for configuration files in these locations (in priority order):

* .autocommit/ in current directory
* $XDG_CONFIG_HOME/autocommit/ (defaults to ~/.config/autocommit/)
* Custom path via AUTOCOMMIT_CONFIG environment variable

To get started with customization:

```shell
autocommit dump-prompts
```

This creates a `.autocommit/` directory with:

* `diff_prompt.txt`: Template for generating diff summaries
* `commit_prompt.txt`: Template for generating commit messages
* `exclusions.txt`: List of files to exclude from processing

### Installing Pre-commit Hook

To automatically generate commit messages during git commits:

```
autocommit install-pre-commit
```

### Environment Variables

* `OPENAI_API_KEY`: Your OpenAI API key
* `AUTOCOMMIT_MODEL`: AI model to use (default: gpt-4-mini)
* `AUTOCOMMIT_CONFIG`: Custom config directory path
* `LOG_LEVEL`: Logging verbosity
* `AUTOCOMMIT_LOG_PATH`: Custom log file path

## Privacy Disclaimer

`gpt-commit` uses the [OpenAI API](https://platform.openai.com/docs) to generate commit messages. Both file names and contents from files that contain staged changes will be shared with OpenAI when using `gpt-commit`. OpenAI will process this data according to their [terms of use](https://openai.com/policies/terms-of-use) and [API data usage policies](https://openai.com/policies/api-data-usage-policies). On March 1st 2023 OpenAI pledged that by default, they would not use data submitted by customers via their API to train or improve their models, and that this data will be retained for a maximum of 30 days, after which it will be deleted.

## Special Thanks

[This project](https://github.com/markuswt/gpt-commit) inspired this project. It had a very simple codebase. I've taken the idea and expanded it to include a lot more features, specifically per-project prompt customization.

## Related Projects

I looked at a bunch of projects before building this one.

- https://github.com/abi/autocommit - python, inactive. Many files, not simple.
- https://github.com/Sett17/turboCommit - rust, inactive.
- https://github.com/Nutlope/aicommits - typescript. Node is so slow and I hate working with it.
- https://github.com/Elhameed/aicommits - python
- https://github.com/zurawiki/gptcommit - active, rust. Too complicated and no prompt customization.
- https://github.com/ywkim/gpt-commit - lisp, inactive.
- https://github.com/markuswt/gpt-commit - single file, python based. No commits > 1yr. Very simple codebase.
- https://github.com/josenerydev/gpt-commit - also python
- https://github.com/di-sukharev/opencommit - has conventional commit structure