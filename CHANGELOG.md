# Changelog

All notable changes to the Lansenger CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.15.1] - 2026-10-13

### Fixed

- `oauth device-login` 轮询阶段失败时缺少回退指引：authorize 阶段判 `deviceflow_unsupported` 会提示 `authorize-url` / `local-callback`，而 authorize 通过、轮询阶段才判不支持时只打印错误就退出 1。现两个阶段提示对称（`--json` 输出契约不变，`error_type` 一直在结果文档里）。

## [0.15.0] - 2026-10-13

### Added

- OAuth2 设备码授权（deviceflow，新版开平）三个命令：`oauth device-authorize` / `oauth device-poll`（可 `--wait`）/ `oauth device-login`（一条式：申请设备码 → 浏览器授权 → 轮询 → 兑换 → 自动落库，无头/远程环境无需本地回调服务器）。旧版开平自动降级：`error_type="deviceflow_unsupported"` + 回退指引（authorize-url / local-callback），退出码契约 0/1/10 不变。
- `oauth device-authorize` / `oauth device-login` 新增 `--from`（AutoClaw/CLI/OpenClaw/MCP，默认 CLI）。

### Changed

- **dep**: `lansenger-sdk` 下限提到 `>=1.12.0`（deviceflow 协议层在 SDK；**发布顺序：先发 SDK 1.12.0 到 PyPI，再合入本版**，否则 CI 解析依赖失败）。
- README 命令总览表补上此前遗漏的 `local-callback`（历史漂移修正）。

### Fixed

- `oauth device-poll --wait` 轮询期间按 Ctrl-C 之前以信号码 130 退出（未捕获 `KeyboardInterrupt`）；现捕获并统一为退出码 1，与 `oauth device-login` 同形状，遵守 C1 0/1/10 退出码契约。

## [0.14.0] - 2026-10-09

### Changed

- **dep**: `lansenger-sdk` 下限提到 `>=1.11.0`。

### Removed

- 移除 7 个应用域：qingjia（请假 V2）、jiaban（加班 V2）、questionnaire（问卷）、notice（通知）、todo（应用待办）、boardroom（会议室预定 V2）、personalTodo（个人待办）。这些应用与蓝信标准接口不同、且会按交付定制，不属于「交付给谁都不变」的标准版，故从 CLI 中剥离。对应 `src/lansenger_cli/commands/*.py` 命令模块、`main.py` 注册与单元测试已移除，5 个语言版本的 README 同步删去相应章节、命令总览表行与身份能力矩阵行。

### Fixed

- **视频会议 `--member` 参数校验**：`videoconference create` / `modify` 的 `--member` 传入非 JSON 对象（例如 `'["u1"]'`）时立即报错并以状态码 2 退出，错误信息给出正确写法，不再把非法成员下发到接口。
- **列表命令表格渲染**：`videoconference history` / `active` / `fixroom-list` 等分页列表此前把接口返回的全部列（最多 34 列）铺开，终端里挤成一团；现在按关键字段（`id` / `mid` / `meetingNumber` / `subject` / `name` / `staffId` 等）自动挑选最多 6 列，单元格截断到 40 字符，并过滤 `password` / `secret` 类字段。
- **`media download-to-file` 失败提示**：下载失败（媒体不存在、身份无权限等）时输出 `Error: Download failed: … (errCode=…)` 并以退出码 1 结束，不再抛出 Python traceback。

---

## [0.13.2] - 2026-09-23

### Added

- **personal-todo**: `resource upload` 成功后额外打印一行可直接粘进 `--resources` 的条目片段（非 JSON 输出时才提示，不污染 JSON 消费方）。条目已做过 `mimeType`/`size` → `fileType`/`fileSize` 映射，避免直接照抄上传响应被后端 errCode 500 打回。

### Fixed

- **videoconference**: `modify` 新增 `--user-stop-time`（自动结束时间，epoch 毫秒），与 `create` 对齐——此前该参数只在创建时可传，修改时无法设置。
- **videoconference**: 会控 `member-control` 移除 `op-code` 白名单客户端校验，改为原样透传（服务端才是权威）。此前客户端会拦掉服务端实际接受的取值（例如 `mute`）。
- **dep**: `lansenger-sdk` 下限提到 `>=1.9.1`——挂附件片段用到 `to_resource_entry()`，会控透传也依赖该版本的 SDK 行为。

---

## [0.13.0] - 2026-09-21

### Added

- **videoconference**: 新增 20 个子命令，覆盖视频会议开放能力全部端点——创建/修改/取消/结束会议、会议详情与列表、操作记录、成员进出记录、云会议室、批量状态、事件订阅、会议参数、历史/进行中会议、会控（opCode）、邀请入会、成员列表、录像列表与下载链接、组织会议配置。
- **videoconference**: 客户端校验——创建/修改要求成员列表恰好一名 `role="admin"` 主持人；会控 `op-code` 白名单（22 个合法值）；录像下载链接每次最多 3 个；`--fetch-range person` 必须带 `--staff-id`；`--mids` 不得为空。
- **videoconference**: `cancel` / `stop` 接入高风险门禁（`--yes` / `--dry-run`，缺省退出码 10）。

### Notes

- **deps**: `lansenger-sdk>=1.8.0`（视频会议域方法与模型随 SDK 1.8.0 提供）。
- 取消仅对未开始的会议有效（已开始请用 `stop`）；错误码 105100/105106 表示组织未启用视频会议。

---

## [0.12.4] - 2026-09-20

### Added

- **notice**: 新增 `send` / `accounts`，支持完整投放、提醒、附件参数和官方账号查询。
- **questionnaire**: 新增 22 个子命令，删除类命令接入高风险门禁。
- **boardroom**: 新增 11 个子命令，覆盖查询、预订、修改、取消、扫码确认；取消接入高风险门禁。
- **personal-todo**: 新增 6 个子命令及本地文件 Base64 上传。

### Fixed

- 修复通知 `--as` 自动补 `createUserId`，显式 `--user-token` 不替代创建人字段。
- 补齐会议室 `gradings --user-id/--org-id`、预订可选参数和个人待办 `finishTime` / 更新身份字段。
- 问卷参与与答卷类命令补齐 `--user-id`。

### Notes

- **deps**: `lansenger-sdk>=1.7.5`。
- 个人待办与应用身份 `todo` 完全分离，`--org-id` 必须显式传入。

---

## [0.12.3] - 2026-08-28

### Added

- **config**: `config set identity_type` — persist the credential identity type (`personal-bot` / `org-app` / `org-bot`); displayed in `config show` and `config list-profiles` (`type=...`). Lets agents distinguish personal-bot vs org-app credentials.

### Fixed

- **cli**: `LANSENGER_APP_TOKEN` / `LANSENGER_USER_TOKEN` env-var mode now works — the env fallback previously only accepted `app_id`/`app_secret` and threw a traceback when no credentials were configured; the no-credentials error message now includes env var guidance.

## [0.11.0] - 2026-07-29

### Added

- **media**: `upload-app-v2` command — 4.5.5 V2 app media upload with required `--user-token`.
- **media**: `download-share` command — 4.5.6 download media by share ID with optional `--output` and `--user-token`.

## [0.10.24] - 2026-07-29

### Added

- **cli**: `parse_field_or_json()` utility — parses `--field`/`--link`/`--fields` values as JSON with automatic `name=value` fallback, fixing PowerShell quoting issues.
- **cli**: `__main__.py` entry point — supports `python -m lansenger_cli` invocation.

### Fixed

- **cli**: `send-app-card`, `update-dynamic-card`, `send-oacard`, `approve-card` now accept `name=value` format for field/link parameters in addition to JSON.

## [0.10.23] - 2026-07-17

### Added

- **cli**: `_ExternalUserTokenProxy` for external mode — auto-injects global `--user-token` into method calls where `user_token=""` is passed.
- **cli**: External mode support in `get_client()` — when `--app-token` + `--user-token` are provided, returns an `_ExternalUserTokenProxy`.

## [0.10.22] - 2026-07-16

### Added

- **linting**: `ruff` linter config in `pyproject.toml` (F/E/W/B rules).
- **tests**: CLI command-level tests for `config` (4 tests) and `health` (2 tests) using Typer CliRunner.

### Fixed

- **lint**: Renamed ambiguous variable `l` to `link` in `message.py`.

## [0.10.21] - 2026-07-16

### Added

- **cli**: `--as` mode now auto-injects `user_id` from staff_id (alongside existing `user_token` auto-fill), enabling calendar `create-schedule` without explicit `--user-id`.

## [0.10.20] - 2026-07-16

### Added

- **cli**: `--verbose` global flag to enable debug logging in `lansenger_sdk`. Logs to stderr with timestamp prefix.

### Changed

- **docs**: All READMEs updated — real URLs replaced with `your-gateway.example.com` / `your-passport.example.com` placeholders. `api_gateway_url` and `passport_url` now clearly marked as required.

## [0.10.19] - 2026-07-15

### Changed

- **docs**: `passport_url` marked as required in all language READMEs. Removed references to "public cloud default" for `api_gateway_url`.

## [0.10.18] - 2026-07-01

### Added

- **bot-command**: New command group (create/query/delete) for managing bot slash commands (4.37).
- **personal-app**: New command group (create/update/info/delete/list) for managing personal apps/bots (4.38).
- **calendar**: `update-attendees` command for batch add/delete schedule attendees (4.23.19).

## [0.10.17] - 2026-06-17

### Added

- **message**: `send-text`, `send-markdown`, `send-group-message` commands now support `--mention-bot` and `--ref-msg-id` options.

### Fixed

- **message**: `query-groups` command default page offset changed from 1 to 0 to match V2 API specification.

## [0.10.16] - 2026-06-17

### Fixed

- **config**: `list-users --show-tokens` showed 0 for both expiry times due to wrong key names (`expires_in` → `user_token_expiry`, `refresh_expires_in` → `refresh_token_expiry`).

## [0.10.15] - 2026-06-16

### Added

- **config**: `list-users` command to list all users with stored user tokens in the current profile.
- **config**: `list-users --show-tokens` flag to display complete token information (user_token, refresh_token, expires_in, refresh_expires_in) for each stored user.
- **cli**: `--as <staff_id>` global flag (short for "act as") that auto-loads and auto-refreshes user tokens from the CredentialStore. Works transparently via proxy — no command files were modified.

## [0.10.14] - 2026-06-16

### Fixed

- **calendar**: `list-schedules` — use `s.get("scheduleId")` instead of `getattr(s, "schedule_id")` for dict items.
- **group**: `members` — use `m.get("staffId")` instead of `getattr(m, "staff_id")`.
- **department**: `children` — fix `Parent ID` (`ancestorDepartments[0].id`), `Has Children` (`hasChildren`).
- **department**: `staffs` — fix `Staff ID` (`id` not `staffId`), replace nonexistent `Gender` with `Org Name` (`orgName`).

## [0.10.13] - 2026-06-15

### Added

- **config**: `delete-profile` command to permanently remove a credential profile and all its data. If the deleted profile is the active one, automatically switches to `"default"`.

### Changed

- **deps**: Bump minimum `lansenger-sdk` requirement to >=1.6.12 for `delete_profile_by_name()` support.

## [0.10.12] - 2026-06-12

### Changed

- **help docs**: All 81 subcommands across 13 modules now have descriptive docstrings, making `--help` output informative for both humans and AI agents.
- **staff search**: `--user-token` and `--user-id` help text now correctly states "one of the two is required" (previously both were shown as required).

### Fixed

- **help rendering**: Command-level help strings migrated from `@app.command(help=...)` to function docstrings for better compatibility with Typer.

---

## [0.10.11] - 2026-06-10

### Changed

- **send-text / send-file**: `--media-type` option now accepts string values (`file`/`video`/`image`/`audio`) instead of integers (1/2/3), matching SDK v1.6.7 upload changes.

## [0.10.10] — migrated to src layout

### Fixed

- **utils**: Error message now properly displays profile name (missing `f`-string prefix).
- **oauth `refresh-token`**: `save_user_token` parameter order fixed — `margin` and `refresh_expires_in` were swapped (caused incorrect expiry calculation).
- **config `show --json`**: Sensitive fields (`app_secret`, `encoding_key`, `callback_token`) now masked in JSON output.
- **chat `messages`**: Added validation — at least one of `--staff-id` or `--group-id` is now required.
- **calendar `list-schedules`**: Help text corrected from `microseconds` to `seconds` (matches OpenAPI 4.23.14).
- **media `upload`**: Help text corrected from `3=file` to `3=audio`; default type changed from 3 to 2.

### Added

- **Short options**: 19 missing short options added across commands:
  - `group create`: `-S/--staff`, `-D/--dept`
  - `group update-members`: `-A/--add`, `-X/--remove`, `-D/--add-dept`
  - `staff search`: `-R/--recursive`, `-S/--sector`
  - `message send-*`: `-m/--mention`, `-F/--field`, `-L/--link`, `-C/--chat-id`, `-D/--dept`
  - `oauth local-callback`: `-E/--exchange`

## [0.10.6] — Skipped (published as 0.10.7)

## [0.10.5] - 2026-06-09

### Fixed

- **oauth `local-callback`**: Port reuse via `_ReuseAddrHTTPServer` subclass (fixes "Address already in use" error on restart).

## [0.10.4] - 2026-06-09

### Fixed

- **staff**: `id_type` parameter values aligned with SDK/API docs (`employ_id`, `mobile`, `mail`, `login`, `external_id`).

## [0.10.3] - 2026-06-08

### Fixed

- **chat/oauth**: JSON output now uses `print()` instead of `rprint()` for proper machine-readable output.
- **oauth `refresh-token`**: Now persists to `CredentialStore` on refresh.

## [0.10.2] - 2026-06-07

### Changed

- Removed static `lxlogin.js` (no longer used).
- OAuth `local-callback` improvements.

## [0.10.1] - 2026-06-06

### Changed

- SDK dependency updated to `>=1.6.0`.

## [0.10.0] - 2026-06-05

### Added

- `oauth local-callback` command: starts a local HTTP server to receive OAuth2 callback, auto-exchanges code for userToken.
- SDK dependency `>=1.5.0`.

## [0.9.3] - 2026-06-01

### Added

- `--json` flag for all commands (machine-readable JSON output).
- `--split-month` and `--progress` flags for `chat messages` (auto-split long date ranges by month with progress feedback).

## [0.9.2] - 2026-05-28

### Added

- `create-schedule`: `--rule`, `--expire`, `--attendee-perms` options.
- `add/delete-attendees`: `--reminder` option.

## [0.9.1] - 2026-05-25

### Changed

- Documentation updates for multi-profile config and credential fields.

## [0.9.0] - 2026-05-22

### Changed

- `send-file` and `send-image-url`: `--caption` renamed to `--content` for consistency.

## [0.8.1] - 2026-05-18

### Fixed

- Minor bug fixes and improvements.

## [0.8.0] - 2026-05-15

### Added

- 6 new CLI commands.
- `upload-app` command (separate from `upload` — uses 4.5.4 app bot endpoint).

## [0.7.1] - 2026-05-12

### Fixed

- Callback commands now resolve `encoding_key` and `callback_token` from `CredentialStore` when flags are empty.

## [0.7.0] - 2026-05-10

### Added

- `encoding_key` and `callback_token` support in `config set`.

## [0.6.0] - 2026-05-08

### Added

- `callback decrypt-payload` command.
- Support for `callback_token`, `known_app_id`, and `data_encrypt` params for callback decryption (requires SDK >=1.3.0).

## [0.5.0] - 2026-05-01

### Added

- `--profile/-P` global option with multi-profile config commands.
- `config list-profiles`, `config use`, and profile switching support.

## [0.4.0] - 2026-04-28

### Added

- `chat` subcommands: `list` and `messages` (OpenAPI 4.24 MCP endpoints).
- `send-bot-message` and `send-group-message` commands.
- `is_group` and `send_group_message` reminder params.

## [0.3.0] - 2026-04-25

### Added

- `calendar create-schedule` now accepts timestamp format.
- `send-oacard`, `send-account-message`, `send-user-message` commands.
- `pad_link` and `pad_card_link` support in `send-link-card` and `send-app-card`.

## [0.2.0] - 2026-04-20

### Added

- `is_group`, `user_token`, `sender_id` to all send commands.
- `head_status_info`, `fields`, `links` to `send-app-card`.
- Expanded `revoke` chat_type support.

### Removed

- `pad_card_link` (merged into `send-app-card`).

## [0.1.0] - 2026-04-15

### Added

- Initial release.
- Commands: `config`, `staff`, `department`, `group`, `message`, `media`, `oauth`, `calendar`, `todo`, `callback`.
- Support for sending text, markdown, files, images, cards via bot and user channels.
- `CredentialStore` integration for persistent credentials.
- Multi-language command support.
