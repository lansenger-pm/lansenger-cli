[English](README.md) | [简体中文](README.zhHans.md) | [繁体中文](README.zhHant.md) | [繁体中文香港](README.zhHantHK.md) | [Français](README.fr.md)

# Lansenger CLI

Lansenger command-line tool — interact with Lansenger APIs directly from the terminal: send messages, manage groups, query staff/departments, operate calendars and todos, and more.

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
lansenger config set api_gateway_url https://apigw.lx.qianxin.com/open/apigw
```

**OAuth2 user auth (fill in when you need userToken)**:

```bash
lansenger config set passport_url https://passport.lx.qianxin.com
lansenger config set redirect_uri http://localhost:8765   # OAuth2 redirect URI (default)
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
| `config` | Manage credentials | `set`, `show`, `clear`, `delete-profile`, `list-profiles` |
| `message` | Send & manage messages | `send-text`, `send-markdown`, `send-file`, `send-image-url`, `send-link-card`, `send-app-articles`, `send-app-card`, `send-oacard`, `send-bot-message`, `send-group-message`, `send-account-message`, `send-user-message`, `update-dynamic-card`, `revoke`, `query-groups` |
| `group` | Manage groups | `create`, `info`, `members`, `list`, `check`, `update`, `update-members` |
| `staff` | Query staff info | `basic-info`, `detail`, `ancestors`, `id-mapping`, `org-extra-fields`, `search`, `org-info` |
| `department` | Query department info | `detail`, `children`, `staffs` |
| `calendar` | Calendar & schedule | `primary`, `create-schedule`, `fetch-schedule`, `delete-schedule`, `list-schedules`, `attendees`, `add-attendees`, `delete-attendees` |
| `todo` | Todo task management | `create`, `update`, `update-status`, `delete`, `list`, `fetch-by-source`, `fetch-by-id`, `status-counts`, `executor-status`, `add-executors`, `delete-executors`, `executor-list` |
| `oauth` | OAuth2 user auth | `authorize-url`, `exchange-code`, `refresh-token`, `user-info`, `parse-callback`, `validate-state` |
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

# Bot channel broadcast
lansenger message send-bot-message text '{"content":"Notice"}' --chat-id user001 --chat-id user002

# Group message channel (user_token optional, shows as bot without it)
lansenger message send-group-message group123 text '{"content":"Group message"}'

# Send as human user (requires user_token)
lansenger message send-group-message group123 text '{"content":"Group message"}' --user-token YOUR_USER_TOKEN --sender-id staff001

# Public account channel
lansenger message send-account-message text '{"content":"Account message"}' --chat-id user001 --account-id acct001

# User channel (requires user_token)
lansenger message send-user-message user001 text '{"content":"Private message"}' --user-token YOUR_USER_TOKEN

# Revoke messages
lansenger message revoke msg001 msg002
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

### Todo Tasks

```bash
# Create todo
lansenger todo create "Approve Document" https://app.com/doc https://app.com/doc \
  "staff001,staff002" org001 --desc "Please review" --type 2

# Update todo status (11=unread, 12=read, 21=pending, 22=done)
lansenger todo update-status task001 22 org001

# List todos
lansenger todo list org001 --status 21,22

# Delete todo
lansenger todo delete task001 org001
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

### Streaming Messages

```bash
# Create streaming message (for AI agent progressive output)
lansenger streaming create user123 single stream-session-001

# Get streaming message status
lansenger streaming fetch MSG_ID
```

## Global Options

| Option | Description |
|------|------|
| `--json` / `-j` | Output raw JSON instead of formatted tables |

```bash
# JSON output (useful for scripting)
lansenger -j staff basic-info staff001
```

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
