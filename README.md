[English](README.md) | [简体中文](README.zhHans.md) | [繁体中文](README.zhHant.md) | [繁体中文香港](README.zhHantHK.md) | [Français](README.fr.md)

# Lansenger CLI

Lansenger command-line tool — interact with Lansenger APIs directly from the terminal: send messages, manage groups, query staff/departments, operate calendars, and more.

## Install

```bash
pip install lansenger-cli
```

Or build from source:

```bash
git clone https://github.com/lansenger-pm/lansenger-cli.git
cd lansenger-cli
pip install -e .
```

Requires Python ≥ 3.10.

## Quick Start

### 1. Configure Credentials

Save credentials via `config set` (stored by profile in `~/.lansenger/sdk_state.json`, keys masked, file permissions 0600):

**Required credentials**:

```bash
lansenger config set app_id YOUR_APP_ID
lansenger config set app_secret YOUR_APP_SECRET
lansenger config set api_gateway_url https://your-gateway.example.com
lansenger config set identity_type personal-bot   # optional: credential identity type — personal-bot / org-app / org-bot
```

**OAuth2 user auth (fill in when you need userToken)**:

```bash
lansenger config set passport_url https://your-passport.example.com  # required
lansenger config set redirect_uri http://localhost:8765   # OAuth2 redirect URI
```

**Callback receiver (fill in when you need to parse/verify webhook callbacks)**:

```bash
lansenger config set encoding_key YOUR_ENCODING_KEY
lansenger config set callback_token YOUR_CALLBACK_TOKEN
```

You can also configure via environment variables (CI/CD friendly):

```bash
export LANSENGER_APP_ID=YOUR_APP_ID
export LANSENGER_APP_SECRET=YOUR_APP_SECRET
export LANSENGER_ENCODING_KEY=YOUR_ENCODING_KEY
export LANSENGER_CALLBACK_TOKEN=YOUR_CALLBACK_TOKEN
```

> **External token mode**: `LANSENGER_APP_TOKEN` takes precedence over the app credentials above. An expired external token only produced a vague `invalid APP_TOKEN` error — since `lansenger-sdk` 1.12.2 declare its expiry with `LANSENGER_APP_TOKEN_EXPIRES_AT` (seconds or milliseconds) and the SDK will obtain a fresh appToken from `LANSENGER_APP_ID` / `LANSENGER_APP_SECRET` instead; without app credentials it now fails with an explicit `LANSENGER_APP_TOKEN expired` error.

### 2. View Configuration

```bash
lansenger config show
```

### 3. Health Check

Verify credentials are correct and app token can be obtained:

```bash
lansenger health check
```

## Command Overview

| Group | Description | Subcommands |
|--------|------|--------|
| `config` | Manage credentials | `set`, `show`, `clear`, `delete-profile`, `list-profiles`, `list-users` |
| `message` | Send & manage messages | `send-text`, `send-markdown`, `send-file`, `send-image-url`, `send-link-card`, `send-app-articles`, `send-app-card`, `send-oacard`, `send-bot-message`, `send-group-message`, `send-account-message`, `send-user-message`, `update-dynamic-card`, `revoke`, `query-groups`, `reply`, `send-authorization-request` |
| `group` | Manage groups | `create`, `info`, `members`, `list`, `check`, `update`, `update-members` |
| `staff` | Query staff info | `basic-info`, `detail`, `ancestors`, `id-mapping`, `org-extra-fields`, `search`, `org-info` |
| `department` | Query department info | `detail`, `children`, `staffs` |
| `calendar` | Calendar & schedule | `primary`, `create-schedule`, `fetch-schedule`, `delete-schedule`, `list-schedules`, `attendees`, `add-attendees`, `delete-attendees`, `update-attendees`, `update-schedule`, `attendee-meta` |
| `bot-command` | Bot slash commands | `create`, `query`, `delete` |
| `personal-app` | Personal apps/bots | `create`, `update`, `info`, `delete`, `list` |
| `videoconference` | Videoconference open APIs (视频会议开放能力) | `create`, `modify`, `cancel`, `stop`, `detail`, `list`, `record-list`, `simplerecord`, `fixroom-list`, `status`, `subscribe`, `params`, `history`, `active`, `member-control`, `invite`, `member-list`, `vod-list`, `vod-download`, `org-conf` |
| `oauth` | OAuth2 user auth | `authorize-url`, `device-authorize`, `device-login`, `device-poll`, `exchange-code`, `local-callback`, `refresh-token`, `user-info`, `parse-callback`, `validate-state` |
| `callback` | Callback event parsing | `parse-payload`, `decrypt-payload`, `verify-signature`, `event-types` |
| `media` | Media file operations | `upload`, `upload-app`, `download`, `download-to-file` |
| `streaming` | Streaming messages (AI) | `create`, `fetch` |
| `chat` | Conversations & messages | `list`, `messages` |
| `health` | Connection health check | `check` |

## Common Examples

### Messaging

```bash
# Send plain text
lansenger message send-text chat123 "Hello World"

# Send markdown
lansenger message send-markdown chat123 "**Bold** text"

# Send file
lansenger message send-file chat123 /path/to/file.pdf

# Send image from URL
lansenger message send-image-url chat123 https://example.com/photo.jpg

# Send link card
lansenger message send-link-card chat123 "Announcement" https://example.com --desc "Click for details"

# Send app card
lansenger message send-app-card chat123 "Card Title" --content "Body text" --card-link https://example.com

# Send app articles
lansenger message send-app-articles chat123 '{"title":"Article 1","url":"https://a.com"}' '{"title":"Article 2","url":"https://b.com"}'

# Send OA approval card
lansenger message send-oacard chat123 "Approval Title" --head "Notification" --field '{"key":"Applicant","value":"John"}'

# Send in group with @all
lansenger message send-text group123 "Announcement" --group --mention-all

# @mention specific people in group
lansenger message send-text group123 "Please check" --group --mention staff001 --mention staff002

# @mention specific bots in group
lansenger message send-text group123 "Bot check" --group --mention-bot bot001 --mention-bot bot002

# Reply to a message (message reference)
lansenger message send-text group123 "Got it" --group --ref-msg-id 524288-xxx

# Bot channel broadcast
lansenger message send-bot-message text '{"content":"Notice"}' --chat-id user001 --chat-id user002

# Bot channel reply (message reference)
lansenger message send-bot-message text '{"content":"Reply"}' --chat-id user001 --ref-msg-id 524288-xxx

# Group message channel (user_token optional, shows as bot without it)
lansenger message send-group-message group123 text '{"content":"Group message"}'

# Send as human user (requires user_token)
lansenger message send-group-message group123 text '{"content":"Group message"}' --user-token YOUR_USER_TOKEN --sender-id staff001

# Reply with group message
lansenger message send-group-message group123 text '{"content":"reply"}' --ref-msg-id 524288-xxx

# Public account channel
lansenger message send-account-message text '{"content":"Account message"}' --chat-id user001 --account-id acct001

# User channel (requires user_token)
lansenger message send-user-message user001 text '{"content":"Private message"}' --user-token YOUR_USER_TOKEN

# Revoke messages
lansenger message revoke msg001 msg002

# Reply to a message with an emoji
lansenger message reply msg001 --emoji TYPE_OK

# Cancel that emoji reply
lansenger message reply msg001 --cancel

# Send an authorization request (authorizationType=1 = location permission)
lansenger message send-authorization-request --chat-id user001

# Query group ID list
lansenger message query-groups --page 0 --size 100
```

### Group Management

```bash
# Create group
lansenger group create "Project Group" org001 --staff staff001 --staff staff002

# View group info
lansenger group info group123

# View group members
lansenger group members group123

# View group list (bot can list groups it belongs to)
lansenger group list

# View group list as user (requires user_token)
lansenger group list --user-token YOUR_USER_TOKEN

# Check if user is in group
lansenger group check group123 --staff-id staff001

# Update group info
lansenger group update group123 --name "New Name" --desc "New Description"

# Add/remove members
lansenger group update-members group123 --add staff003 --remove staff001
```

### Staff Query

```bash
# Basic staff info
lansenger staff basic-info staff001

# Detailed staff info
lansenger staff detail staff001

# Search staff
lansenger staff search ZhangSan

# ID mapping (phone/email → staffId)
lansenger staff id-mapping org001 phone 13800138000

# Organization info
lansenger staff org-info org001
```

### Department Query

```bash
# Department detail
lansenger department detail dept001

# Department children
lansenger department children dept001

# Department staff
lansenger department staffs dept001
```

### Conversations & Messages

```bash
# Get chat list (requires user_token)
lansenger chat list --user-token YOUR_USER_TOKEN

# Group chats only
lansenger chat list --type 2 --user-token YOUR_USER_TOKEN

# Search chats by keyword
lansenger chat list --type 1 --keyword ZhangSan --user-token YOUR_USER_TOKEN

# Get private chat messages
lansenger chat messages --staff-id staff001 --user-token YOUR_USER_TOKEN

# Get group chat messages (bot can fetch messages of groups it's in)
lansenger chat messages --group-id group123

# Get group chat messages as user (requires user_token)
lansenger chat messages --group-id group123 --user-token YOUR_USER_TOKEN
```

### Calendar

```bash
# Get primary calendar
lansenger calendar primary --user-token YOUR_USER_TOKEN

# Create schedule (start/end are Unix timestamps in seconds)
lansenger calendar create-schedule cal001 "Weekly Meeting" 1747539600 1747543200 \
  '[{"staffId":"staff001","attendeeFlag":"yes"}]' \
  --desc "Weekly standup" --user-token YOUR_USER_TOKEN

# List schedules (start/end are Unix timestamps in seconds)
lansenger calendar list-schedules cal001 1747539600 1747603200 --user-token YOUR_TOKEN

# View schedule detail
lansenger calendar fetch-schedule cal001 schedule001 --user-token YOUR_TOKEN

# Delete schedule
lansenger calendar delete-schedule cal001 schedule001 --user-token YOUR_TOKEN
```

### OAuth2 User Auth

```bash
# Build authorize URL
lansenger oauth authorize-url https://yourapp.com/callback --scope basic_userinfor

# Exchange code for user token
lansenger oauth exchange-code AUTH_CODE --redirect-uri https://yourapp.com/callback

# Refresh user token
lansenger oauth refresh-token YOUR_REFRESH_TOKEN

# Fetch user info
lansenger oauth user-info YOUR_USER_TOKEN

# Device code login — headless/remote friendly (no localhost callback server);
# requires the new open platform, legacy servers print a fallback hint.
# A scannable QR is drawn in the terminal (--qr auto|utf8|ascii|none); --qr-png
# Terminal QR is painted with colour half-blocks (falls back to plain block characters when colour is off)
# also saves it as a PNG, --qr-data-uri emits the same PNG as a base64 data:
# URI for chats and web panels that cannot read a file or terminal text.
# Approval is the user's own act on the Lanxin mobile app (scan the QR / open
# the link); the CLI never opens a browser unless you pass --open-browser
lansenger oauth device-login

# Low-level steps for scripts / agents
lansenger oauth device-authorize
# --qr-ecc L|M picks the error-correction level (default M, smaller panels)
lansenger oauth device-authorize --qr none --qr-png /tmp/device-qr.png
lansenger oauth device-authorize --qr none --qr-data-uri   # data: URI for chats/panels
lansenger oauth device-poll DEVICE_CODE --wait
```

### Callback Events

```bash
# List all callback event types
lansenger callback event-types

# Parse callback payload
lansenger callback parse-payload ENCRYPTED_DATA --encoding-key YOUR_KEY

# Decrypt callback payload (view orgId/appId/events)
lansenger callback decrypt-payload ENCRYPTED_DATA --encoding-key YOUR_KEY

# Verify signature
lansenger callback verify-signature TIMESTAMP NONCE SIGNATURE ENCODING_KEY --data-encrypt ENCRYPTED_DATA
```

### Media Files

```bash
# Upload core platform file
lansenger media upload /path/to/file.pdf --media-type 3

# Upload app/bot media file (used for send-text / send-file etc.)
lansenger media upload-app /path/to/file.pdf --media-type file

# Download media to local file
lansenger media download-to-file MEDIA_ID --output /path/to/save.pdf
```

> **Note**: `media upload` (4.5.1) needs the 「上传素材」(media upload) permission in the developer console, otherwise the platform rejects the upload.

### Streaming Messages

```bash
# Create streaming message (for AI agent progressive output)
lansenger streaming create user123 single stream-session-001

# Get streaming message status
lansenger streaming fetch MSG_ID
```

### Videoconference (视频会议开放能力)

```bash
# Create a meeting — member list must carry exactly one role="admin" host
lansenger videoconference create "项目周会" org1 \
  --start-time 1729500000000 --type 1 \
  --member '[{"staffId":"u1","employeeName":"Host","role":"admin"},{"staffId":"u2","employeeName":"B","role":"participant"}]'

# Query meetings / status / detail
lansenger videoconference list org1 --start-time 1729400000000 --end-time 1729600000000 --fetch-range all
lansenger videoconference status org1 --mids "123,456"
lansenger videoconference detail 123 org1 staff001

# Host controls a member (opCode is passed through to the server)
lansenger videoconference member-control 123 u2 muteall org1 staff001

# Cancel (gated) / stop (gated)
lansenger videoconference cancel 123 org1 staff001 --dry-run
lansenger videoconference stop 123 org1 staff001 --yes

# Recordings — download URLs allow max 3 vods per call
lansenger videoconference vod-list 123 org1 staff001
lansenger videoconference vod-download org1 staff001 --vods '[{"vodId":"v1"}]'

# Org config (PRS >=3.8)
lansenger videoconference org-conf org1
```

## Global Options

| Option | Description |
|------|------|
| `--json` / `-j` | Output raw JSON instead of formatted tables |
| `--as <staff_id>` | Auto-load & auto-refresh user token for the given staff_id from credential store |
| `--app-token <token>` | Use external mode: provide app token directly, bypassing credential store |
| `--user-token <token>` | Provide user token directly in external mode (auto-injected into commands) |

```bash
# JSON output (useful for scripting)
lansenger -j staff basic-info staff001

# Run a command as a specific user (auto-loads user token from credential store)
lansenger --as staff001 chat messages --group-id group123

# External mode — provide tokens directly, no credential file needed
lansenger --app-token YOUR_APP_TOKEN --user-token YOUR_USER_TOKEN message send-text chat123 "Hello"

# External mode with API gateway URL
LANSENGER_API_GATEWAY_URL=https://your-gateway.example.com lansenger --app-token YOUR_APP_TOKEN --user-token YOUR_USER_TOKEN staff basic-info staff001
```

### External Mode

External mode allows you to provide `app_token` and `user_token` directly via command line flags, bypassing the credential store and OAuth2 flow entirely. This is useful for:

- CI/CD pipelines where tokens are managed externally
- Integration with your own authentication system
- Short-lived tokens that you refresh yourself
- Testing with temporary tokens

When using external mode:
- `--app-token` is required to enter external mode
- `--user-token` is optional but recommended for APIs that require user identity
- The provided `user_token` is automatically injected into all commands that accept it
- Credential store operations (`config` commands) are not available
- Token refresh is not performed — you are responsible for keeping tokens valid

## Shell Completion

Built-in typer completion support:

```bash
# Install completion
lansenger --install-completion

# Show completion script
lansenger --show-completion
```

Supports bash, zsh, fish, and other major shells.

## Multi-app / Multi-bot Profiles

CLI supports multiple profiles, each corresponding to one appID, with isolated credentials:

```bash
# Configure first app (personal bot)
lansenger config set app_id xxx1 --profile my-bot
lansenger config set app_secret xxx1 --profile my-bot

# Configure second app (Lansenger app)
lansenger config set app_id xxx2 --profile my-app
lansenger config set app_secret xxx2 --profile my-app
lansenger config set encoding_key yyy2 --profile my-app        # This app needs callbacks
lansenger config set callback_token zzz2 --profile my-app

# Run commands with specific profile
lansenger message send-text staff123 "Hello" --profile my-bot
lansenger callback parse-payload DATA --profile my-app

# List all configured profiles
lansenger config list-profiles

# Delete a profile (auto-switches to default if active)
lansenger config delete-profile my-bot

# View a profile's details
lansenger config show --profile my-app
```

## Security

- Credentials stored per profile in `~/.lansenger/sdk_state.json` with `0600` permissions
- `config show` masks all secret fields (`***`), only `api_gateway_url` and `passport_url` shown in plaintext
- Environment variables `LANSENGER_APP_ID` / `LANSENGER_APP_SECRET` / `LANSENGER_ENCODING_KEY` / `LANSENGER_CALLBACK_TOKEN` supported for CI/CD

## Identity & Permissions

### Identity Capability Matrix

The Lansenger platform has three identity types with different API access:

| Command Domain | Personal Bot | Org App (Self-built) | Org App + Bot | Notes |
|--------|:---:|:---:|:---:|------|
| `message send-text/markdown/file/...` (bot DM) | **Y** | N | **Y** | Only bots can send bot DMs |
| `message send-text --group` (group chat) | **Y** | N | **Y** | Personal bot now supports group messaging |
| `message send-group-message` | **Y** | N | **Y** | Same as above |
| `message send-account-message` (public account) | N | **Y** | **Y** | Requires public account capability |
| `message send-user-message` (user-to-user) | N | **Y** | **Y** | Requires userToken + OAuth2 |
| `message revoke` | **Y** | **Y** | **Y** | Revoke own messages |
| `message reply` | **Y** | **Y** | **Y** | Emoji reply / cancel on a message (reversible, so no `--yes` gate) |
| `message send-authorization-request` | N | **Y** | **Y** | authorizationReq sent over the public account channel; `--type 1` = location permission |
| `staff *` (contacts read-only) | N | **Y** | **Y** | `search` additionally requires userToken |
| `department *` | N | **Y** | **Y** | Org-level apps only |
| `calendar *` | N | **Y** | **Y** | With userToken = user identity; without = bot identity |
| `chat list/messages` | N | **Y** | **Y** | Org-level apps only |
| `group *` (group management V2) | N | N | **Y** | Requires bot to be in group |
| `media upload` | **Y** | **Y** | **Y** | General upload |
| `media upload-app` | **Y** | **Y** | **Y** | Self-built apps only (not ISV) |
| `media download/path` | **Y** | **Y** | **Y** | General download |
| `oauth *` | N | **Y** | **Y** | Org-level apps only |
| `streaming *` | N | **Y** | **Y** | Org-level apps only |
| `callback *` (event parsing) | N/A | N/A | N/A | Pure data operation, no identity required |


> **Personal Bot** can only send/receive messages and upload/download files. Cannot access contacts, groups, calendars, or OAuth2.
>
> **Org App vs Org App + Bot**: Same appID/appSecret. The only difference is messaging channels — only bots can send bot DMs and group messages (because only bots can join groups). All other APIs (contacts, calendar, chat, OAuth2, streaming) work identically for both. Currently only self-built apps support bot capability.

### Developer Center Permissions

Beyond identity type, specific API calls also depend on permission toggles in the Lansenger Developer Center. The organization may restrict developer access, requiring admin assistance.

**Basic Permissions (enabled by default):**

| Permission | Description |
|------|------|
| Get basic user info | Get personnel basic info for system/app login |
| Send notification messages | Get org message channels to send messages to people/groups |

**Advanced Permissions (disabled by default, must be manually enabled):**

| Permission | Description | Impacted Skill |
|------|------|-------------|
| Contacts read-only | Read access to contacts | `lansenger-staff`, `lansenger-department` |
| Contacts edit | Edit access to contacts | `lansenger-staff` (create/update/delete) |
| Sensitive info - Phone | Access user phone numbers | `lansenger-staff` (detail, id-mapping) |
| Sensitive info - Email | Access user emails | `lansenger-staff` (detail, id-mapping) |
| Sensitive info - ID number | Access user ID numbers | `lansenger-staff` |
| Sensitive info - Employee ID | Access user employee IDs | `lansenger-staff` |
| Map unique attribute to staff ID | Map phone/email/employee ID to staff ID | `lansenger-staff` (id-mapping) |
| App edit | Create and update apps | Developer Center management |
| Groups read-only | Read access to groups | `lansenger-group` (query info/members) |
| Groups edit | Edit access to groups | `lansenger-group` (create/update/dismiss/members) |
| Calendar read-only | Read access to calendar & schedules | `lansenger-calendar` (query) |
| Calendar edit | Edit access to calendar & schedules | `lansenger-calendar` (create/update/delete) |
| Upload media | Upload media file permission | `lansenger-media` (upload, upload-app) |
| Workbench template read | Read access to workbench templates | — |
| Workbench template write | Write access to workbench templates | — |

When encountering permission errors, first verify the identity type supports the operation, then prompt the user to enable the corresponding advanced permission in the Developer Center (contact org admin if unable to access).

## CLI Compatibility

This CLI shares the same command syntax as the TypeScript and Go versions:

```bash
# Python CLI
pip install lansenger-cli

# Go CLI
go install github.com/lansenger-pm/lansenger-sdk-go/cmd/lansenger@latest

# TypeScript CLI
npm install -g lansenger-cli
```

## Relationship with SDK

This CLI is built on [lansenger-sdk-python](https://github.com/lansenger-pm/lansenger-sdk-python)'s `LansengerSyncClient`, covering all sync SDK APIs without modifying the SDK.

## License

MIT License
