# Cross-SDK Change Specification

> **Version**: 0.9.3 (Python CLI reference)  
> **Date**: 2026-06-05  
> **Status**: Draft — actionable for Go SDK and TypeScript SDK teams  
> **Reference implementation**: `lansenger-cli` (Python) — `src/lansenger_cli/`

This document lists every change introduced in the Python SDK/CLI v0.9.3 that must be synchronized across the Go and TypeScript SDK projects and their respective CLIs. Each change is tagged with a **priority** and **scope** (SDK vs CLI-only) to help teams prioritize.

---

## Priority Labels

| Label | Meaning |
|-------|---------|
| **P0** | Must sync before next release — breaks existing behavior or fixes a bug |
| **P1** | Should sync in next release — new feature that users will expect |
| **P2** | Can defer — enhancement or convenience feature |

---

## 1. CLI Changes

### 1.1 — `--json` global flag works for ALL commands [P0]

**Scope**: CLI-only  
**Affected commands** (previously missing `--json` output):

| Command | What was missing | Fix |
|---------|-----------------|-----|
| `health check` | No JSON output at all | Check `is_json_output()` → output `{"healthy": true/false}` |
| `oauth authorize-url` | Only printed rich-formatted URL | Check `is_json_output()` → output `{"authorize_url": "<url>"}` |
| `oauth parse-callback` | Only printed dict | Check `is_json_output()` → output structured JSON |
| `oauth validate-state` | Only printed bool string | Check `is_json_output()` → output `{"valid": true/false}` |
| `media download` | Only printed rich status | Check `is_json_output()` → output `{"success": bool, "size": int, "error": string}` |
| `media download-to-file` | Only printed rich path | Check `is_json_output()` → output `{"saved_path": string}` |

**Implementation pattern** (copy this in each command handler):

```python
# At the top of every command handler, after getting the result:
if is_json_output():
    rprint(json.dumps({...structured dict...}, ensure_ascii=False))
    return
# Then fall through to existing rich/table output
```

**Reference**: `src/lansenger_cli/commands/health.py:14`, `src/lansenger_cli/commands/oauth.py:18`, `src/lansenger_cli/commands/media.py:43`

---

### 1.2 — `chat messages --split-month` and `--progress` [P1]

**Scope**: CLI-only  
**New CLI parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--split-month` | bool | false | Auto-split query by month when time range exceeds 1 month |
| `--progress` | bool | false | Show pagination progress (pages/messages fetched, month progress) |

**Behavior**:
1. When `--split-month` is false (default), the command works as before — single query with start/end time.
2. When `--split-month` is true:
   - The `_split_months()` helper divides the `[start_time, end_time]` microsecond range into monthly intervals.
   - For each month interval, paginate through all pages (cursor = `last_version`).
   - Collect all messages into a single list.
   - Output the combined result.
3. When `--progress` is true (and not `--json`), print incremental status:
   - Per-page: `Month 1/3 | Page 5 | 420 messages total`
   - Final: `Done: 15 pages, 1260 messages across 3 months`
4. When both `--split-month` and `--json` are set, output the combined message list as a single JSON array.

**`_split_months()` algorithm**:

```
Input: start_us (microseconds), end_us (microseconds)
Output: list of (month_start_us, month_end_us) tuples

Algorithm:
1. Convert start_us/end_us to datetime objects (divide by 1_000_000)
2. If start_us == 0, default to 2020-01-01
3. Iterate year/month from start to end
4. For each month:
   - month_start = 1st day 00:00:00 in microseconds
   - month_end = last day 23:59:59 in microseconds (use calendar.monthrange for last day)
5. Return list of (month_start, month_end) pairs
```

**API note**: The underlying SDK call `fetch_chat_messages()` is unchanged. The CLI orchestrates multiple SDK calls per month. No SDK change required.

**Reference**: `src/lansenger_cli/commands/chat.py:49-112`

---

### 1.3 — `calendar create-schedule`: 3 new parameters [P1]

**Scope**: CLI-only (SDK already supports these fields, CLI was missing the flags)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--rule` | string (JSON) | "" | RFC 5545 repeat rule JSON (for `repeat_type=custom`) |
| `--expire` | string | "" | Expire date type: `yes` or `no` |
| `--attendee-perms` | string | "" | Attendee permissions: `can_modify`, `can_invite`, `can_see`, `none` |

**SDK mapping** (how CLI maps these to SDK method params):

| CLI flag | SDK method parameter |
|----------|---------------------|
| `--rule` | `rule` |
| `--expire` | `expire_date_type` |
| `--attendee-perms` | `attendee_permissions` |

**Reference**: `src/lansenger_cli/commands/calendar.py:35-37` (flags), `:54` (SDK call)

---

### 1.4 — `calendar add-attendees` / `delete-attendees`: `--reminder` parameter [P1]

**Scope**: CLI-only

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--reminder` | string | "" | Reminder type: `yes` or `no` |

Both `add-attendees` and `delete-attendees` commands now accept `--reminder`, passed as `reminder_type` to the SDK.

**Reference**: `src/lansenger_cli/commands/calendar.py:137`, `:156`

---

### 1.5 — `callback` commands: new parameters and new command [P1]

**Scope**: CLI-only (SDK already has the functions; CLI added the flags and a new subcommand)

#### 1.5a — `callback parse-payload` new parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--callback-token` | string | "" | Token for signature verification (falls back to encoding_key) |
| `--known-app-id` | string | "" | Known appId to help split orgId/appId during decryption |

#### 1.5b — NEW command: `callback decrypt-payload`

Separate decryption-only command (parse-payload does both decrypt + parse; this command returns raw decrypted JSON).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `encrypted_data` | argument | yes | Encrypted `dataEncrypt` value |
| `--encoding-key` | option | yes* | Base64-encoded AES key (reads from credential store if empty) |
| `--known-app-id` | option | no | Known appId for orgId/appId splitting |

*required — exits with error if not provided and not found in credential store.

#### 1.5c — `callback verify-signature` new parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--data-encrypt` | string | "" | The encrypted dataEncrypt value (required for correct verification) |
| `--callback-token` | string | "" | Token from dev center callback config (falls back to encoding_key) |

#### 1.5d — Credential store resolution for callback params

All callback commands now resolve `encoding_key` and `callback_token` from `CredentialStore` when CLI flags are empty:

```
_resolve_encoding_key(cli_value, profile):
  1. If cli_value is non-empty → return cli_value
  2. Load credentials from CredentialStore(profile)
  3. Return creds.get("encoding_key", "")
  4. If found, print info message: "Using encoding_key from credential store (profile: X)"

_resolve_callback_token(cli_value, encoding_key, profile):
  1. If cli_value is non-empty → return cli_value
  2. Load credentials from CredentialStore(profile)
  3. Return creds.get("callback_token", "")
  4. If found, print info message
  Note: falls back to encoding_key as the token (SDK behavior)
```

**Reference**: `src/lansenger_cli/commands/callback.py:10-33` (resolvers), `:73-95` (decrypt-payload command)

---

### 1.6 — `config set`: new valid keys [P1]

**Scope**: CLI-only

`encoding_key` and `callback_token` are now accepted by `config set` alongside the existing keys.

**VALID_KEYS** list:

```
app_id, app_secret, api_gateway_url, passport_url, encoding_key, callback_token
```

The `config set` command now also passes `encoding_key` and `callback_token` to `store.save_credentials()`.

**Reference**: `src/lansenger_cli/commands/config.py:10`, `:26-33`

---

## 2. SDK Changes

### 2.1 — `ChatMessageInfo.plain_text()` method [P0]

**Scope**: SDK  
**Languages**: Python ✅, Go ❌, TypeScript ❌

Add a `plain_text()` (or `PlainText()` / `plainText()`) method to the `ChatMessageInfo` model class.

**Behavior**:

```
Extract plain text from the content field. Handles these content formats:

| Content format | Extraction logic | Example |
|----------------|-----------------|---------|
| {"text": "xxx"} | Return text value | "Hello" |
| {"formatText": {"content": "xxx"}} | Return formatText.content value | "Hello" |
| {"text": "", "attachments": [...]} | Return "" (empty) | "" |
| Plain string | Return the string directly | "Hello" |
| None / null | Return "" | "" |

Always returns a string. Never returns None/null.
```

**Python reference implementation**:

```python
def plain_text(self) -> str:
    content = self.content
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        if "text" in content and content["text"]:
            return content["text"]
        if "formatText" in content and isinstance(content["formatText"], dict):
            return content["formatText"].get("content", "")
    return ""
```

**Go implementation notes**:
- Add `PlainText() string` method on `ChatMessageInfo` struct
- Handle `map[string]interface{}` or typed nested structs for content
- Return empty string for nil/empty cases

**TypeScript implementation notes**:
- Add `plainText(): string` method on `ChatMessageInfo` class
- Content field is `Record<string, any> | string | null`
- Return empty string for null/undefined cases

---

### 2.2 — `exchange_code` bug fix: persist `expires_in` [P0]

**Scope**: SDK  
**Languages**: Python ✅, Go ❌, TypeScript ❌

**Bug**: When `exchange_code()` saves the `user_token` to `CredentialStore`, it does NOT pass `expires_in` to `save_user_token()`. This means `user_token_expiry` stays `0` in the store, which prevents any auto-refresh expiry checks from working.

**Fix**: After calling the exchange API, pass `expires_in` to the credential persistence method:

```python
# BEFORE (broken):
store.save_user_token(user_token=result.user_token, refresh_token=result.refresh_token)

# AFTER (fixed):
store.save_user_token(
    user_token=result.user_token,
    refresh_token=result.refresh_token,
    expires_in=result.expires_in,         # <-- ADD THIS
    refresh_expires_in=result.refresh_expires_in,  # <-- ADD THIS TOO
)
```

**Go implementation notes**:
- In `ExchangeCode()`, ensure `ExpiresIn` and `RefreshExpiresIn` are passed to the token store's `SaveUserToken()` method
- Check that `SaveUserToken()` accepts and persists these fields

**TypeScript implementation notes**:
- In `exchangeCode()`, ensure `expiresIn` and `refreshExpiresIn` are passed to `saveUserToken()`
- Check that the store schema includes `user_token_expiry` and `refresh_token_expiry` fields

---

### 2.3 — `UserTokenManager` for auto-refresh (future feature) [P2]

**Scope**: SDK  
**Status**: Not yet implemented — specification only  
**Languages**: All three (design first, implement later)

This is a planned feature. Do NOT implement yet, but ensure the SDK architecture can accommodate it.

**Design**:

```
UserTokenManager (similar to TokenManager for appToken):
1. Before every API call that requires a user_token, check expiry:
   - If user_token_expiry > now + 60s → token is valid, use it
   - If user_token_expiry <= now + 60s → attempt refresh
2. Refresh flow:
   - Call refresh_user_token() with stored refresh_token
   - Persist new user_token + new refresh_token + new expires_in
   - IMPORTANT: refresh_token rotation — old refresh_token is invalidated after use
   - If refresh fails → return error, do NOT retry with old token
3. Integration point:
   - LansengerSyncClient / LansengerClient should have a method like
     ensure_valid_user_token(profile) that does the check+refresh
   - CLI commands that accept --user-token should optionally use this
     when --user-token is empty and a stored token exists
```

**Token lifecycle** (document for all teams):

| Token | Lifetime | Notes |
|-------|----------|-------|
| `user_token` | 2 hours | Used for user-scoped API calls |
| `refresh_token` | 30 days | Used to get a new user_token; **rotates** on each use |
| `app_token` | 2 hours | Obtained from app_id+app_secret; auto-refreshed by TokenManager |

**Key constraints**:
- `refresh_token` rotation: each refresh API call returns a **new** `refresh_token`. The old one is immediately invalidated. The store must update both tokens atomically.
- Concurrent refresh: if two processes try to refresh simultaneously, one will fail. Implement a lock or accept the race condition with retry logic.

---

## 3. CredentialStore Schema Changes

### 3.1 — New credential fields [P1]

**Scope**: SDK (CredentialStore)  
**Languages**: Python ✅, Go ❌, TypeScript ❌

The `CredentialStore` now persists 6 fields per profile:

| Field | Type | Description |
|-------|------|-------------|
| `app_id` | string | Application ID |
| `app_secret` | string | Application secret |
| `api_gateway_url` | string | API gateway base URL |
| `passport_url` | string | Passport/auth base URL |
| `encoding_key` | string | Base64-encoded AES key for callback decryption |
| `callback_token` | string | Token for callback signature verification |

**Changes needed in Go/TS**:
1. `CredentialStore.Save()` / `Load()` must handle `encoding_key` and `callback_token`
2. `config set` CLI command must accept these as valid keys
3. `save_credentials()` must accept and persist these fields
4. `load_credentials()` must return these fields

---

### 3.2 — User token persistence fields [P0]

**Scope**: SDK (CredentialStore)  
**Languages**: All three

The `save_user_token()` method must persist these fields:

| Field | Type | Description |
|-------|------|-------------|
| `user_token` | string | Current user access token |
| `user_token_expiry` | int64 | Expiry timestamp (unix seconds, = now + expires_in) |
| `refresh_token` | string | Current refresh token (rotates on each use) |
| `refresh_token_expiry` | int64 | Refresh token expiry timestamp |

**Bug**: Currently `user_token_expiry` is not computed/persisted because `expires_in` was not passed. This is the P0 fix in §2.2.

---

## 4. Skills Documentation Changes

These changes affect the `.agents/skills/` SKILL.md files that are shared across all SDK projects (they are installed into the opencode agent environment, not per-language).

### 4.1 — `lansenger-chat` SKILL.md [P1]

Add these sections:

#### Batch Operations & Limitations (批量操作与限制说明)

| Topic | Detail |
|-------|--------|
| 1-month limit | API does not support queries spanning > 1 month per request |
| `--split-month` | CLI auto-splits into monthly intervals; SDK users must implement their own splitting |
| `--progress` | Shows page/message count during pagination (CLI only) |
| Resume (断点续传) | Use `last_version` as `base_version` cursor to resume from where you stopped |
| Rate limiting |建议每页之间加 100-200ms 延迟, 避免触发限流 |

#### Command parameter updates

Add to parameter table:

| Parameter | Command | Description |
|-----------|---------|-------------|
| `--split-month` | chat messages | Auto-split by month |
| `--progress` | chat messages | Show progress during pagination |

#### Field clarifications

- `sender` field in ChatMessageInfo: this is the **display name**, not a staffId. For identity, use `sender_id`.
- `staff_infos` in chat list response: limited info. Use `staff detail` command for full profile.
- `content` field format table (see §2.1 above for the 5 formats).

---

### 4.2 — `lansenger-oauth` SKILL.md [P1]

Add token lifecycle management section:

#### Token Lifecycle

| Token | Lifetime | Rotation | Storage key |
|-------|----------|----------|-------------|
| `user_token` | 2 hours | Refreshed via refresh_token | `user_token` |
| `refresh_token` | 30 days | **Rotates** on each refresh call | `refresh_token` |
| `app_token` | 2 hours | Auto-refreshed from app_id+app_secret | (internal) |

#### Auto-refresh best practices

1. Always persist `expires_in` when saving tokens (§2.2 bug fix)
2. Check expiry before making API calls (`user_token_expiry > now + buffer`)
3. After refresh, atomically update both `user_token` AND `refresh_token` (rotation)
4. Never reuse an old `refresh_token` after a successful refresh

#### `exchange_code` now persists `expires_in`

Document that `exchange_code` now saves `expires_in` and `refresh_expires_in`, enabling future auto-refresh.

---

### 4.3 — `lansenger-shared` SKILL.md [✅ done]

Already updated with 6-field credential table. No further changes needed.

---

### 4.4 — `lansenger-callback` SKILL.md [✅ done]

Already updated with `decrypt-payload` command and new parameters. No further changes needed.

---

## 5. Implementation Checklist

Use this checklist to track cross-SDK synchronization progress.

### Go SDK / Go CLI

| # | Change | Priority | Status |
|---|--------|----------|--------|
| 1 | `--json` flag for health, oauth, media commands | P0 | ✅ |
| 2 | `chat messages --split-month --progress` | P1 | ✅ |
| 3 | `calendar create-schedule --rule --expire --attendee-perms` | P1 | ✅ |
| 4 | `calendar add/delete-attendees --reminder` | P1 | ✅ |
| 5 | `callback parse-payload --callback-token --known-app-id` | P1 | ✅ |
| 6 | NEW: `callback decrypt-payload` command | P1 | ✅ |
| 7 | `callback verify-signature --data-encrypt --callback-token` | P1 | ✅ |
| 8 | Credential store resolution for encoding_key/callback_token | P1 | ✅ |
| 9 | `config set` accepts encoding_key, callback_token | P1 | ✅ |
| 10 | `ChatMessageInfo.PlainText()` method | P0 | ✅ |
| 11 | `ExchangeCode()` persists expires_in + refresh_expires_in | P0 | ✅ |
| 12 | CredentialStore 6-field schema | P1 | ✅ |
| 13 | CredentialStore user_token_expiry field | P0 | ✅ |
| 14 | UserTokenManager (auto-refresh) + getUserToken/setUserTokens | P0 | ❌ |

### TypeScript SDK / TS CLI

| # | Change | Priority | Status |
|---|--------|----------|--------|
| 1 | `--json` flag for health, oauth, media commands | P0 | ✅ |
| 2 | `chat messages --split-month --progress` | P1 | ✅ |
| 3 | `calendar create-schedule --rule --expire --attendee-perms` | P1 | ✅ |
| 4 | `calendar add/delete-attendees --reminder` | P1 | ✅ |
| 5 | `callback parse-payload --callback-token --known-app-id` | P1 | ✅ |
| 6 | NEW: `callback decrypt-payload` command | P1 | ✅ |
| 7 | `callback verify-signature --data-encrypt --callback-token` | P1 | ✅ |
| 8 | Credential store resolution for encoding_key/callback_token | P1 | ✅ |
| 9 | `config set` accepts encoding_key, callback_token | P1 | ✅ |
| 10 | `ChatMessageInfo.plainText()` method | P0 | ✅ (SDK) |
| 11 | `exchangeCode()` persists expiresIn + refreshExpiresIn | P0 | ✅ |
| 12 | CredentialStore 6-field schema | P1 | ✅ |
| 13 | CredentialStore user_token_expiry field | P0 | ✅ |
| 14 | UserTokenManager (auto-refresh) + getUserToken/setUserTokens | P0 | ✅ |
| 15 | `oauth local-callback` CLI subcommand | P1 | ✅ |

---

## 6. API Compatibility Notes

### No server-side API changes

All changes in this spec are **client-side only**. The Lansenger server APIs are unchanged. The changes fall into two categories:

1. **SDK bug fixes / feature additions** — making existing SDK capabilities actually work correctly (e.g., §2.2 expires_in bug)
2. **CLI orchestration** — combining multiple SDK calls in new ways (e.g., §1.2 split-month pagination)

### `--split-month` is CLI-only, not SDK

The SDK does NOT need a `split_month` parameter on `fetch_chat_messages()`. The CLI orchestrates multiple calls. However, SDK docs should mention the 1-month query limit and recommend that SDK users implement their own month-splitting when querying long ranges.

### `plain_text()` is SDK-only, not a server API

The server returns `content` as a polymorphic field (string, dict, or null). The `plain_text()` / `PlainText()` / `plainText()` method is a client-side convenience extractor. The server API is not changing.

---

## 7. Test Cases for Validation

Each SDK/CLI team should validate these scenarios:

### §2.2 — exchange_code persists expires_in

```
1. Call exchange_code() with a valid auth code
2. Inspect CredentialStore for the profile
3. Verify: user_token_expiry > 0 (should be ~now + 7200)
4. Verify: refresh_token_expiry > 0 (should be ~now + 2592000)
```

### §2.1 — plain_text() method

```
Test cases for ChatMessageInfo.plain_text():

| Input content | Expected output |
|---------------|-----------------|
| {"text": "Hello world"} | "Hello world" |
| {"formatText": {"content": "<b>Hello</b>"}} | "<b>Hello</b>" |
| {"text": "", "attachments": [{"name": "file.pdf"}]} | "" |
| "Hello world" | "Hello world" |
| None / null | "" |
| {} (empty dict) | "" |
| {"formatText": {"content": ""}} | "" |
```

### §1.1 — --json flag coverage

```
For each affected command:
1. Run command WITHOUT --json → expect rich/table output
2. Run same command WITH --json/-j → expect valid JSON output
3. Verify JSON is parseable (jq . or equivalent)
```

### §1.2 — split-month pagination

```
1. Run: chat messages --staff-id X --start 1700000000000000 --end 1710000000000000 --split-month --progress
   (range spans multiple months)
2. Verify: progress messages appear per month
3. Verify: final output contains all messages across months
4. Run same with --json → expect single JSON array of all messages
```