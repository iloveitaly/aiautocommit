# [0.14.0](https://github.com/iloveitaly/aiautocommit/compare/v0.13.1...v0.14.0) (2025-11-08)


### Features

* difftastic integration ([de5d360](https://github.com/iloveitaly/aiautocommit/commit/de5d360fe0e3f20944316de8f031cc555c75bf7e))



## [0.24.0](https://github.com/iloveitaly/aiautocommit/compare/v0.23.0...v0.24.0) (2026-08-14)


### Features

* update default model to google:gemini-3.7-flash ([#81](https://github.com/iloveitaly/aiautocommit/issues/81)) ([287aa58](https://github.com/iloveitaly/aiautocommit/commit/287aa587f27a4691053f0190a6668ecbe35a4187))

## [0.23.0](https://github.com/iloveitaly/aiautocommit/compare/v0.22.0...v0.23.0) (2026-08-14)


### Features

* add install_editable recipe for global CLI development ([c993811](https://github.com/iloveitaly/aiautocommit/commit/c99381122974d193bd9ca9e0a8556aa0628f6ddc))
* **cli:** add --skip-edit option to install command ([8fd1102](https://github.com/iloveitaly/aiautocommit/commit/8fd1102502b64fcb641126cffd3d7a82ee557a51))


### Bug Fixes

* **ci:** unblock dependabot PRs and bump stalled deps ([#79](https://github.com/iloveitaly/aiautocommit/issues/79)) ([40f702b](https://github.com/iloveitaly/aiautocommit/commit/40f702bb75bdf8889331542cf71b1bf768979060))
* **cli:** handle pydantic_ai UserError cleanly without tracebacks ([19b32e1](https://github.com/iloveitaly/aiautocommit/commit/19b32e19310397631c2401cb045cd54a018dfa67))
* use low thinking effort for Google Gemini models ([#78](https://github.com/iloveitaly/aiautocommit/issues/78)) ([cbe82ab](https://github.com/iloveitaly/aiautocommit/commit/cbe82abe44ca26fe2f43c61c7bd87fb402c55be1))

## [0.22.0](https://github.com/iloveitaly/aiautocommit/compare/v0.21.0...v0.22.0) (2026-07-28)


### Features

* update default model to google:gemini-3.5-flash-lite ([956d608](https://github.com/iloveitaly/aiautocommit/commit/956d6087df9df752ef0b23f7b4dc06243395d267))
* update default model to google:gemini-3.5-flash-lite ([#67](https://github.com/iloveitaly/aiautocommit/issues/67)) ([4a8454a](https://github.com/iloveitaly/aiautocommit/commit/4a8454a7e5beb9820667ad0b7c8e2e682a849ced))


### Bug Fixes

* preserve Ruff rule baseline ([3fb4bee](https://github.com/iloveitaly/aiautocommit/commit/3fb4bee9841cb7722d204644184b2a0e4e672ec4))
* **timing:** type message parameter correctly in log decorators ([#69](https://github.com/iloveitaly/aiautocommit/issues/69)) ([13619c1](https://github.com/iloveitaly/aiautocommit/commit/13619c15f94eeee4fdfed597b0a402217907731f))
* type timing log messages ([13619c1](https://github.com/iloveitaly/aiautocommit/commit/13619c15f94eeee4fdfed597b0a402217907731f))
* update default Google Gemini model ([4a8454a](https://github.com/iloveitaly/aiautocommit/commit/4a8454a7e5beb9820667ad0b7c8e2e682a849ced))

## [0.21.0](https://github.com/iloveitaly/aiautocommit/compare/v0.20.0...v0.21.0) (2026-07-28)


### Features

* add support for including pull request context in commits ([e95e03c](https://github.com/iloveitaly/aiautocommit/commit/e95e03c7f210aff7bc2e20540a96f30e51029ef2))
* add uninstall command for pre-commit hook ([924e382](https://github.com/iloveitaly/aiautocommit/commit/924e38232d502a0c6f53b63a31f280f762e18d0f))
* detect default branch for smarter repo context ([920741f](https://github.com/iloveitaly/aiautocommit/commit/920741fef644ef773b772f4ffae19b2baf201f85))
* include pull request context in commit generation prompt ([154c060](https://github.com/iloveitaly/aiautocommit/commit/154c0602e8777562e4fdaee5562a32c874e009c4))


### Bug Fixes

* improve example schema to improve prompt performance ([ee9af60](https://github.com/iloveitaly/aiautocommit/commit/ee9af609bd91e613ebd6f426f034dfbbc1371444))


### Documentation

* add documentation for PR context feature ([104fe42](https://github.com/iloveitaly/aiautocommit/commit/104fe4226dd6b107b6490bd9cf5f518f5ed7e3bc))
* Add link to commit message guidelines gist ([a074269](https://github.com/iloveitaly/aiautocommit/commit/a074269804b5ea6d97cb16df1c642fa00ac7d8b2))

## [0.20.0](https://github.com/iloveitaly/aiautocommit/compare/v0.19.0...v0.20.0) (2026-04-02)


### Features

* include current git branch in commit generation prompt ([3153520](https://github.com/iloveitaly/aiautocommit/commit/3153520d0569c2fd8a67716eb6cb4238167c50e1))


### Bug Fixes

* improve output file handling to preserve existing content ([5c44db0](https://github.com/iloveitaly/aiautocommit/commit/5c44db0137e020c0d01abe58e923bd9f25fa897a))


### Documentation

* add git branch inclusion to feature list ([b235aa1](https://github.com/iloveitaly/aiautocommit/commit/b235aa1a71143224769956fbaaa2357ea7e7803a))

## [0.19.0](https://github.com/iloveitaly/aiautocommit/compare/v0.18.0...v0.19.0) (2026-03-29)


### Features

* add header to examples in commit prompt ([5e4d5ad](https://github.com/iloveitaly/aiautocommit/commit/5e4d5adf324a81fd81f0cdca078e4ae3bb3857ec))


### Bug Fixes

* ensure consistent git output by disabling custom user configs ([a7a417b](https://github.com/iloveitaly/aiautocommit/commit/a7a417b991932c9a5385215b50aa4db0ae3a5648))


### Documentation

* update example format and documentation in README ([9fff2be](https://github.com/iloveitaly/aiautocommit/commit/9fff2bea8782c29169708da839002533782340d8))
* update feature descriptions and lock file handling in readme ([d13795a](https://github.com/iloveitaly/aiautocommit/commit/d13795addacfccca7b139a17e5422bad0b69a57e))

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
