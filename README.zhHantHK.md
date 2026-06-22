[English](README.md) | [简体中文](README.zhHans.md) | [繁体中文](README.zhHant.md) | [繁体中文香港](README.zhHantHK.md) | [Français](README.fr.md)

# Lansenger CLI

Lansenger 命令列工具 — 在終端機直接呼叫藍信開放平台 API，發送訊息、管理群組、查詢人員/部門、操作行事曆與待辦等。

## 安裝

```bash
pip install lansenger-cli
```

或從原始碼安裝：

```bash
git clone https://github.com/lansenger-pm/lansenger-cli.git
cd lansenger-cli
pip install -e .
```

需要 Python ≥ 3.10。

## 快速開始

### 1. 設定憑證

透過 `config set` 命令儲存憑證（按 appID/profile 隔離儲存在 `~/.lansenger/sdk_state.json`，密鑰脫敏顯示，檔案權限 0600）：

**基本憑證（所有使用者必填）**：

```bash
lansenger config set app_id YOUR_APP_ID
lansenger config set app_secret YOUR_APP_SECRET
lansenger config set api_gateway_url https://apigw.lx.qianxin.com/open/apigw
```

**OAuth2 使用者認證（需要取得 userToken 時填寫）**：

```bash
lansenger config set passport_url https://passport.lx.qianxin.com
lansenger config set redirect_uri http://localhost:8765   # OAuth2 回呼地址（預設值）
```

**回呼接收（需要解析/驗簽回呼 Webhook 時填寫）**：

```bash
lansenger config set encoding_key YOUR_ENCODING_KEY
lansenger config set callback_token YOUR_CALLBACK_TOKEN
```

也可以透過環境變數設定（適合 CI/CD 或臨時使用）：

```bash
export LANSENGER_APP_ID=YOUR_APP_ID
export LANSENGER_APP_SECRET=YOUR_APP_SECRET
export LANSENGER_ENCODING_KEY=YOUR_ENCODING_KEY
export LANSENGER_CALLBACK_TOKEN=YOUR_CALLBACK_TOKEN
```

### 2. 檢視設定

```bash
lansenger config show
```

### 3. 健康檢查

驗證憑證是否正確、能否成功取得 app token：

```bash
lansenger health check
```

## 命令總覽

| 命令組 | 說明 | 子命令 |
|--------|------|--------|
| `config` | 管理憑證設定 | `set`, `show`, `clear`, `delete-profile`, `list-profiles`, `list-users` |
| `message` | 發送與管理訊息 | `send-text`, `send-markdown`, `send-file`, `send-image-url`, `send-link-card`, `send-app-articles`, `send-app-card`, `send-oacard`, `send-bot-message`, `send-group-message`, `send-account-message`, `send-user-message`, `update-dynamic-card`, `revoke`, `query-groups` |
| `group` | 管理群組 | `create`, `info`, `members`, `list`, `check`, `update`, `update-members` |
| `staff` | 查詢人員資訊 | `basic-info`, `detail`, `ancestors`, `id-mapping`, `org-extra-fields`, `search`, `org-info` |
| `department` | 查詢部門資訊 | `detail`, `children`, `staffs` |
| `calendar` | 行事曆操作 | `primary`, `create-schedule`, `fetch-schedule`, `delete-schedule`, `list-schedules`, `attendees`, `add-attendees`, `delete-attendees` |
| `todo` | 待辦任務管理 | `create`, `update`, `update-status`, `delete`, `list`, `fetch-by-source`, `fetch-by-id`, `status-counts`, `executor-status`, `add-executors`, `delete-executors`, `executor-list` |
| `oauth` | OAuth2 使用者認證 | `authorize-url`, `exchange-code`, `refresh-token`, `user-info`, `parse-callback`, `validate-state` |
| `callback` | 回呼事件解析 | `parse-payload`, `decrypt-payload`, `verify-signature`, `event-types` |
| `media` | 媒體檔案操作 | `upload`, `upload-app`, `download`, `download-to-file` |
| `streaming` | 串流訊息（AI 場景） | `create`, `fetch` |
| `chat` | 會話與訊息記錄 | `list`, `messages` |
| `health` | 連線健康檢查 | `check` |

## 常用範例

### 訊息發送

```bash
# 發送純文字訊息
lansenger message send-text chat123 "Hello World"

# 發送 Markdown 訊息
lansenger message send-markdown chat123 "**粗體** 文字"

# 發送檔案
lansenger message send-file chat123 /path/to/file.pdf

# 發送網路圖片
lansenger message send-image-url chat123 https://example.com/photo.jpg

# 發送連結卡片
lansenger message send-link-card chat123 "公告標題" https://example.com --desc "點擊檢視詳情"

# 發送應用卡片
lansenger message send-app-card chat123 "卡片標題" --content "正文內容" --card-link https://example.com

# 發送多條圖文（appArticles）
lansenger message send-app-articles chat123 '{"title":"文章1","url":"https://a.com"}' '{"title":"文章2","url":"https://b.com"}'

# 發送 OA 審批卡片
lansenger message send-oacard chat123 "審批標題" --head "審批通知" --field '{"key":"申請人","value":"張三"}'

# 群組內發送並 @all
lansenger message send-text group123 "全員通知" --group --mention-all

# 群組內 @指定人
lansenger message send-text group123 "請檢視" --group --mention staff001

# @提及群組中的特定機器人
lansenger message send-text group123 "Bot check" --group --mention-bot bot001 --mention-bot bot002

# 回覆訊息（訊息引用）
lansenger message send-text group123 "Got it" --group --ref-msg-id 524288-xxx

# 機械人通道發送訊息
lansenger message send-bot-message text '{"content":"通知內容"}' --chat-id user001 --chat-id user002

# 機械人通道回覆（訊息引用）
lansenger message send-bot-message text '{"content":"Reply"}' --chat-id user001 --ref-msg-id 524288-xxx

# 群組訊息通道發送（user_token 可選，無則顯示為 bot）
lansenger message send-group-message group123 text '{"content":"群組訊息"}'

# 以人類使用者身份發送（需要 user_token）
lansenger message send-group-message group123 text '{"content":"群組訊息"}' --user-token YOUR_USER_TOKEN --sender-id staff001

# 回覆群組訊息
lansenger message send-group-message group123 text '{"content":"reply"}' --ref-msg-id 524288-xxx

# 應用帳號通道發送
lansenger message send-account-message text '{"content":"帳號訊息"}' --chat-id user001 --account-id acct001

# 使用者通道發送（需要 user_token）
lansenger message send-user-message user001 text '{"content":"私聊訊息"}' --user-token YOUR_USER_TOKEN

# 撤回訊息
lansenger message revoke msg001 msg002

# 查詢群組 ID 列表
lansenger message query-groups --page 0 --size 100
```

### 群組管理

```bash
# 建立群組
lansenger group create "專案群" org001 --staff staff001 --staff staff002

# 檢視群組資訊
lansenger group info group123

# 檢視群組成員
lansenger group members group123

# 檢視群組列表（bot 可檢視所在的群組，傳 user_token 可檢視使用者所在的群組）
lansenger group list

# 檢視使用者所在的群組列表（需要 user_token）
lansenger group list --user-token YOUR_USER_TOKEN

# 檢查使用者是否在群組內
lansenger group check group123 --staff-id staff001

# 更新群組資訊
lansenger group update group123 --name "新名稱" --desc "新描述"

# 新增/移除成員
lansenger group update-members group123 --add staff003 --remove staff001
```

### 人員查詢

```bash
# 檢視人員基本資訊
lansenger staff basic-info staff001

# 檢視人員詳細資訊
lansenger staff detail staff001

# 搜尋人員
lansenger staff search 張三

# ID 對映（手機號/電子郵件 → staffId）
lansenger staff id-mapping org001 phone 13800138000

# 檢視組織資訊
lansenger staff org-info org001
```

### 部門查詢

```bash
# 檢視部門詳情
lansenger department detail dept001

# 檢視子部門
lansenger department children dept001

# 檢視部門內人員
lansenger department staffs dept001
```

### 會話與訊息記錄

```bash
# 取得會話列表（需要 user_token）
lansenger chat list --user-token YOUR_USER_TOKEN

# 只看群組聊天
lansenger chat list --type 2 --user-token YOUR_USER_TOKEN

# 搜尋會話（關鍵詞）
lansenger chat list --type 1 --keyword 張三 --user-token YOUR_USER_TOKEN

# 取得私聊訊息記錄
lansenger chat messages --staff-id staff001 --user-token YOUR_USER_TOKEN

# 取得群組聊天訊息記錄（bot 可直接取得所在群組的訊息）
lansenger chat messages --group-id group123

# 取得群組聊天訊息記錄（以使用者身份，需要 user_token）
lansenger chat messages --group-id group123 --user-token YOUR_USER_TOKEN
```

### 行事曆操作

```bash
# 取得主行事曆
lansenger calendar primary --user-token YOUR_USER_TOKEN

# 建立排程（start/end 為秒級時間戳）
lansenger calendar create-schedule cal001 "週會" 1747539600 1747543200 \
  '[{"staffId":"staff001","attendeeFlag":"yes"}]' \
  --desc "每週例會" --user-token YOUR_USER_TOKEN

# 檢視排程列表（start/end 為秒級時間戳）
lansenger calendar list-schedules cal001 1747539600 1747603200 --user-token YOUR_TOKEN

# 檢視排程詳情
lansenger calendar fetch-schedule cal001 schedule001 --user-token YOUR_TOKEN

# 刪除排程
lansenger calendar delete-schedule cal001 schedule001 --user-token YOUR_TOKEN
```

### 待辦任務

```bash
# 建立待辦
lansenger todo create "審批檔案" https://app.com/doc https://app.com/doc \
  "staff001,staff002" org001 --desc "請審批" --type 2

# 更新待辦狀態（11=待閱, 12=已閱, 21=待辦, 22=已辦）
lansenger todo update-status task001 22 org001

# 檢視待辦列表
lansenger todo list org001 --status 21,22

# 刪除待辦
lansenger todo delete task001 org001
```

### OAuth2 使用者認證

```bash
# 產生授權 URL
lansenger oauth authorize-url https://yourapp.com/callback --scope basic_userinfor

# 交換 code 取得 user token
lansenger oauth exchange-code AUTH_CODE --redirect-uri https://yourapp.com/callback

# 刷新 user token
lansenger oauth refresh-token YOUR_REFRESH_TOKEN

# 取得使用者資訊
lansenger oauth user-info YOUR_USER_TOKEN
```

### 回呼事件

```bash
# 檢視所有回呼事件類型
lansenger callback event-types

# 解析回呼資料
lansenger callback parse-payload ENCRYPTED_DATA --encoding-key YOUR_KEY

# 解密回呼資料（檢視 orgId/appId/events）
lansenger callback decrypt-payload ENCRYPTED_DATA --encoding-key YOUR_KEY

# 驗證簽章
lansenger callback verify-signature TIMESTAMP NONCE SIGNATURE ENCODING_KEY --data-encrypt ENCRYPTED_DATA
```

### 媒體檔案

```bash
# 上載核心平台檔案
lansenger media upload /path/to/file.pdf --media-type 3

# 上載應用/機械人媒體檔案（用於 send-text / send-file 等）
lansenger media upload-app /path/to/file.pdf --media-type file

# 下載媒體檔案到本地
lansenger media download-to-file MEDIA_ID --output /path/to/save.pdf
```

### 串流訊息

```bash
# 建立串流訊息（用於 AI agent 漸進式輸出）
lansenger streaming create user123 single stream-session-001

# 取得串流訊息狀態
lansenger streaming fetch MSG_ID
```

## 全域選項

| 選項 | 說明 |
|------|------|
| `--json` / `-j` | 輸出原始 JSON 格式而非表格 |
| `--as <staff_id>` | 從憑證儲存中自動載入並自動刷新指定 staff_id 的 user token |

```bash
# JSON 格式輸出（便於指令稿處理）
lansenger -j staff basic-info staff001

# 以指定使用者身份執行命令（自動從憑證儲存載入 user token）
lansenger --as staff001 chat messages --group-id group123
```

## Shell 自動補全

typer 內建補全支援：

```bash
# 安裝補全
lansenger --install-completion

# 檢視補全指令稿
lansenger --show-completion
```

支援 bash、zsh、fish 等主流 shell。

## 多應用/多機械人設定（Profile）

CLI 支援多 profile，每個 profile 對應一個 appID（一個應用或一個機械人），憑證互相隔離：

```bash
# 設定第一個應用（個人機械人）
lansenger config set app_id xxx1 --profile my-bot
lansenger config set app_secret xxx1 --profile my-bot

# 設定第二個應用（藍信應用）
lansenger config set app_id xxx2 --profile my-app
lansenger config set app_secret xxx2 --profile my-app
lansenger config set encoding_key yyy2 --profile my-app        # 此應用需要接收回呼
lansenger config set callback_token zzz2 --profile my-app

# 切換應用執行命令
lansenger message send-text staff123 "Hello" --profile my-bot
lansenger callback parse-payload DATA --profile my-app

# 檢視所有已設定 profile
lansenger config list-profiles

# 刪除指定 profile（如為當前 active 則自動切換到 default）
lansenger config delete-profile my-bot

# 檢視某個 profile 詳情
lansenger config show --profile my-app
```

## 憑證安全

- 憑證按 profile 隔離儲存在 `~/.lansenger/sdk_state.json`，檔案權限 0600
- `config show` 對所有密鑰類欄位脫敏顯示（`***`），僅 `api_gateway_url` 和 `passport_url` 明文展示
- 支援環境變數 `LANSENGER_APP_ID` / `LANSENGER_APP_SECRET` / `LANSENGER_ENCODING_KEY` / `LANSENGER_CALLBACK_TOKEN`，適合 CI/CD 場景

## 身份與權限

### 身份能力矩陣

藍信平台有三種身份類型，各自擁有不同的 API 存取權限：

| 命令域 | 個人機械人 | 組織應用（自建） | 組織應用 + 機械人 | 說明 |
|--------|:---:|:---:|:---:|------|
| `message send-text/markdown/file/...`（機械人私聊） | **Y** | N | **Y** | 只有機械人可以傳送機械人私聊 |
| `message send-text --group`（群聊） | N* | N | **Y** | 個人機械人 API 支援，但尚無入群功能 |
| `message send-group-message` | N* | N | **Y** | 同上 |
| `message send-account-message`（公眾號） | N | **Y** | **Y** | 需要公眾號能力 |
| `message send-user-message`（使用者對使用者） | N | **Y** | **Y** | 需要 userToken + OAuth2 |
| `message revoke` | **Y** | **Y** | **Y** | 撤回自己傳送的訊息 |
| `staff *`（通訊錄唯讀） | N | **Y** | **Y** | `search` 額外需要 userToken |
| `department *` | N | **Y** | **Y** | 僅組織級應用 |
| `calendar *` | N | **Y** | **Y** | 有 userToken = 使用者身份；無 = 機械人身份 |
| `todo *` | N | **Y** | **Y** | 僅組織級應用 |
| `chat list/messages` | N | **Y** | **Y** | 僅組織級應用 |
| `group *`（群組管理 V2） | N | N | **Y** | 需要機械人已在群內 |
| `media upload` | **Y** | **Y** | **Y** | 通用上載 |
| `media upload-app` | **Y** | **Y** | **Y** | 僅自建應用（非 ISV） |
| `media download/path` | **Y** | **Y** | **Y** | 通用下載 |
| `oauth *` | N | **Y** | **Y** | 僅組織級應用 |
| `streaming *` | N | **Y** | **Y** | 僅組織級應用 |
| `callback *`（事件解析） | N/A | N/A | N/A | 純資料操作，無需身份 |

> \* **N\*** = API 能力存在，但入群功能尚未就緒。

> **個人機械人**只能收發訊息和上載/下載檔案。不能存取通訊錄、群組、行事曆或 OAuth2。
>
> **組織應用 vs 組織應用 + 機械人**：使用相同的 appID/appSecret。唯一區別在於訊息通道——只有機械人可以傳送機械人私聊和群訊息（因為只有機械人可以加入群組）。所有其他 API（通訊錄、行事曆、待辦、會話、OAuth2、串流訊息）兩者完全一致。目前僅自建應用支援機械人能力。

### 開發者中心權限

除了身份類型外，具體 API 呼叫還依賴藍信開發者中心中的權限開關。組織可能限制開發者存取，需要管理員協助。

**基礎權限（預設開啟）：**

| 權限 | 說明 |
|------|------|
| 取得使用者基本資訊 | 取得人員基本資訊，用於系統/應用登入 |
| 傳送通知訊息 | 取得組織訊息通道，向人員/群組傳送訊息 |

**進階權限（預設關閉，需手動開啟）：**

| 權限 | 說明 | 涉及的 Skill |
|------|------|-------------|
| 通訊錄唯讀 | 通訊錄讀取權限 | `lansenger-staff`、`lansenger-department` |
| 通訊錄編輯 | 通訊錄編輯權限 | `lansenger-staff`（建立/更新/刪除） |
| 敏感資訊 - 手機號 | 取得使用者手機號 | `lansenger-staff`（詳情、ID 對映） |
| 敏感資訊 - 電子郵件 | 取得使用者電子郵件 | `lansenger-staff`（詳情、ID 對映） |
| 敏感資訊 - 身份證號 | 取得使用者身份證號 | `lansenger-staff` |
| 敏感資訊 - 工號 | 取得使用者工號 | `lansenger-staff` |
| 唯一屬性對映 staff ID | 將手機號/電子郵件/工號對映為 staff ID | `lansenger-staff`（ID 對映） |
| 應用編輯 | 建立和更新應用 | 開發者中心管理 |
| 群組唯讀 | 群組讀取權限 | `lansenger-group`（查詢資訊/成員） |
| 群組編輯 | 群組編輯權限 | `lansenger-group`（建立/更新/解散/成員） |
| 行事曆唯讀 | 行事曆和排程讀取權限 | `lansenger-calendar`（查詢） |
| 行事曆編輯 | 行事曆和排程編輯權限 | `lansenger-calendar`（建立/更新/刪除） |
| 上載媒體 | 上載媒體檔案權限 | `lansenger-media`（upload、upload-app） |
| 工作台模板讀取 | 工作台模板讀取權限 | — |
| 工作台模板寫入 | 工作台模板寫入權限 | — |

遇到權限錯誤時，請先確認身份類型是否支援該操作，再提示使用者在開發者中心開啟對應的進階權限（如無法存取請聯繫組織管理員）。

## CLI 相容性

本 CLI 與 TypeScript 版、Go 版命令語法完全一致：

```bash
# Python CLI
pip install lansenger-cli

# Go CLI
go install github.com/lansenger-pm/lansenger-sdk-go/cmd/lansenger@latest

# TypeScript CLI
npm install -g lansenger-cli
```

## 與 SDK 的關係

本 CLI 基於 [lansenger-sdk-python](https://github.com/lansenger-pm/lansenger-sdk-python) 的 `LansengerSyncClient` 實作，覆蓋 SDK 全部同步 API，不修改 SDK 程式碼。

## 授權條款

MIT License
