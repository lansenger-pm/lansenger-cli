# Changelog

All notable changes to the Lansenger CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
