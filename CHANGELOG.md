# [0.14.0](https://github.com/iloveitaly/aiautocommit/compare/v0.13.1...v0.14.0) (2025-11-08)


### Features

* difftastic integration ([de5d360](https://github.com/iloveitaly/aiautocommit/commit/de5d360fe0e3f20944316de8f031cc555c75bf7e))



## [0.18.0](https://github.com/iloveitaly/aiautocommit/compare/v0.17.0...v0.18.0) (2026-03-24)


### Features

* allow local .aiautocommit file to append to system prompt ([8356557](https://github.com/iloveitaly/aiautocommit/commit/8356557d7a1b8ba5a10de95812a70af6f2b861e2))
* **cli:** append .dev suffix to local version ([9466480](https://github.com/iloveitaly/aiautocommit/commit/9466480457b6e8635f39f5faf37406b26243f9e4))
* **cli:** make message optional for debug-prompt command ([54130ca](https://github.com/iloveitaly/aiautocommit/commit/54130ca78f53d616328c3beb5c5a2578b393e387))
* enhance SAS token generation and add new upload endpoints ([85ae0f8](https://github.com/iloveitaly/aiautocommit/commit/85ae0f82bb30e52b24d796ca2f32cc9b49306694))


### Bug Fixes

* **cli:** provide fallback comment when AI model is unavailable ([9bf2a55](https://github.com/iloveitaly/aiautocommit/commit/9bf2a552de547d340a85528ff14d279c055e3472))
* detect whitespace-only changes correctly ([f323228](https://github.com/iloveitaly/aiautocommit/commit/f323228c15c55c0b9f616a00ce33234313740df8))
* improve error handling and CLI output for model failures ([7d4c29d](https://github.com/iloveitaly/aiautocommit/commit/7d4c29d06ebd9dd24cd681b078516f781de961ce))
* improve git hook installation and commit trigger ([0f0770c](https://github.com/iloveitaly/aiautocommit/commit/0f0770cf7c1b6c8c65150284e7d5910431f06261))


### Documentation

* clarify configuration file usage in README ([845913d](https://github.com/iloveitaly/aiautocommit/commit/845913de161e2a32b5bfdccf410bac0bf9300053))
* document debug-prompt command in README ([220af15](https://github.com/iloveitaly/aiautocommit/commit/220af1552280ead405577924285971925a66e18c))
* improve readme clarity and tone ([24dbc90](https://github.com/iloveitaly/aiautocommit/commit/24dbc9044a74e90c973efb8f0507de95b438b890))
* more comments ([252796d](https://github.com/iloveitaly/aiautocommit/commit/252796d7d219d5bed4777687844da81fcc70331a))
* update debug_prompt command description ([8b2a625](https://github.com/iloveitaly/aiautocommit/commit/8b2a625213c20275215df9430fee591f63c9eef9))

## [0.17.0](https://github.com/iloveitaly/aiautocommit/compare/v0.16.1...v0.17.0) (2026-03-18)


### Features

* add support for glob patterns in file exclusions ([e75aa8e](https://github.com/iloveitaly/aiautocommit/commit/e75aa8e0d12357c6981197df1acec49ea6aafcc0))

## [0.16.1](https://github.com/iloveitaly/aiautocommit/compare/v0.16.0...v0.16.1) (2026-03-17)


### Bug Fixes

* docs update to trigger a build ([899a9a8](https://github.com/iloveitaly/aiautocommit/commit/899a9a84e2073454928c58ee3c3bce4753b916c7))

## [0.16.0](https://github.com/iloveitaly/aiautocommit/compare/v0.15.0...v0.16.0) (2026-03-10)


### Features

* add execution timing with time_it context manager ([2a9fcf9](https://github.com/iloveitaly/aiautocommit/commit/2a9fcf93e84aec673459d66388b6ec1889ab9e79))

## [0.15.0](https://github.com/iloveitaly/aiautocommit/compare/v0.14.1...v0.15.0) (2026-02-07)


### Features

* map universal ai key to provider env vars and update docs ([99f4a02](https://github.com/iloveitaly/aiautocommit/commit/99f4a027ed760ecd3f17e50564c1f1b9cb3b40fd))
* update default model to gemini-3-flash and enable thinking ([c4faf71](https://github.com/iloveitaly/aiautocommit/commit/c4faf71d77b1f9bf9e82f9ae69bc035c1917b358))


### Documentation

* remove LOC count from README ([0cf8099](https://github.com/iloveitaly/aiautocommit/commit/0cf80997e0e4178c7c4f32581d7f469151fd5993))
* Remove obsolete MCP Server Configuration section ([a904ef1](https://github.com/iloveitaly/aiautocommit/commit/a904ef100211359d6cbb167f05f39dbcb371cda5))

## [0.14.1](https://github.com/iloveitaly/aiautocommit/compare/v0.14.0...v0.14.1) (2026-02-05)


### Bug Fixes

* handle pure whitespace commits with default message ([81d8888](https://github.com/iloveitaly/aiautocommit/commit/81d8888dbcd26b10b65681936ee92d39a376ab21))


### Documentation

* add git-log-search/message.py link to TODO list ([c51723a](https://github.com/iloveitaly/aiautocommit/commit/c51723a09a29947907d826b1ed55b80d9b0cc167))
* add rules for writing or updating README in commands files ([8c9fb45](https://github.com/iloveitaly/aiautocommit/commit/8c9fb4577e9adb59dd037b9d9d1e43ac3706df36))
* document and implement static lock file commit messages ([baa879d](https://github.com/iloveitaly/aiautocommit/commit/baa879d3308ccd40b006b60e9feefbcdfc38d066))
* update env var to AIAUTOCOMMIT_LOG_PATH in README ([f1de046](https://github.com/iloveitaly/aiautocommit/commit/f1de04616054d2258f34155cb8e349a5f92d6f9d))
* update privacy section and CLI name references ([dca5725](https://github.com/iloveitaly/aiautocommit/commit/dca57254d398da2f3c7d36bdaedd980b68d62ab5))
* update readme title and clarify usage section ([d9e5aac](https://github.com/iloveitaly/aiautocommit/commit/d9e5aac9ad48f7ab6a0f919ecbc85cc1f82cee3f))
* update storage file names in README for config files ([95492f1](https://github.com/iloveitaly/aiautocommit/commit/95492f17e101d044b8a11c81f63b98d03137fa0e))

## [0.13.1](https://github.com/iloveitaly/aiautocommit/compare/v0.13.0...v0.13.1) (2025-08-18)


### Bug Fixes

* don't exit early if commit message file exists ([80e57eb](https://github.com/iloveitaly/aiautocommit/commit/80e57ebbe2867c4bb7b8c6493c170b7c1f1a8284))
* revised iteration on AI commit prompts ([4649f28](https://github.com/iloveitaly/aiautocommit/commit/4649f288b129b6bfce6fa5cd8f73e0d12f24ca7d))



# [0.13.0](https://github.com/iloveitaly/aiautocommit/compare/v0.12.1...v0.13.0) (2025-05-12)


### Features

* add utility to wait for internet connection ([0d859a8](https://github.com/iloveitaly/aiautocommit/commit/0d859a8eb4e821cd598b732080f6f60bb6cf08b4))
* sort git diff by change size and add Azure OpenAI support ([6962f47](https://github.com/iloveitaly/aiautocommit/commit/6962f47d838d73d74005e1d75e66b7a93802c594))



## [0.12.1](https://github.com/iloveitaly/aiautocommit/compare/v0.12.0...v0.12.1) (2025-04-19)


### Bug Fixes

* update default model to gpt-4.1 and clarify prompt instructions ([bfe0c5a](https://github.com/iloveitaly/aiautocommit/commit/bfe0c5af796ba60facea872215aac810ca578451))



# [0.12.0](https://github.com/iloveitaly/aiautocommit/compare/v0.11.0...v0.12.0) (2025-03-04)


### Features

* add debug info command for commit prompts ([9f8a1b4](https://github.com/iloveitaly/aiautocommit/commit/9f8a1b47ee37e8871bb343e2a6d8f27ccd0c9b51))
