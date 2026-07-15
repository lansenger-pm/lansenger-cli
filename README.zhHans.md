[English](README.md) | [简体中文](README.zhHans.md) | [繁体中文](README.zhHant.md) | [繁体中文香港](README.zhHantHK.md) | [Français](README.fr.md)

# Lansenger CLI

蓝信（Lansenger）命令行工具 — 在终端直接调用蓝信开放平台 API，发送消息、管理群组、查询人员/部门、操作日程与待办等。

## 安装

```bash
pip install lansenger-cli
```

或从源码安装：

```bash
git clone https://github.com/lansenger-pm/lansenger-cli.git
cd lansenger-cli
pip install -e .
```

需要 Python ≥ 3.10。

## 快速开始

### 1. 配置凭证

通过 `config set` 命令保存凭证（按 appID/profile 隔离存储在 `~/.lansenger/sdk_state.json`，密钥脱敏显示，文件权限 0600）：

**基本凭证（所有用户必填）**：

```bash
lansenger config set app_id YOUR_APP_ID
lansenger config set app_secret YOUR_APP_SECRET
lansenger config set api_gateway_url https://your-gateway.example.com
```

**OAuth2 用户认证（需要获取 userToken 时填写）**：

```bash
lansenger config set passport_url https://your-passport.example.com   # 必须配置
lansenger config set redirect_uri http://localhost:8765             # OAuth2 回调地址（默认值）
```

**回调接收（需要解析/验签回调 Webhook 时填写）**：

```bash
lansenger config set encoding_key YOUR_ENCODING_KEY        # 回调数据 AES 解密密钥（Base64 编码）
lansenger config set callback_token YOUR_CALLBACK_TOKEN    # 回调签名验证 token（未填时回退到 encoding_key）
```

也可以通过环境变量配置（适合 CI/CD 或临时使用）：

```bash
export LANSENGER_APP_ID=YOUR_APP_ID
export LANSENGER_APP_SECRET=YOUR_APP_SECRET
export LANSENGER_ENCODING_KEY=YOUR_ENCODING_KEY
export LANSENGER_CALLBACK_TOKEN=YOUR_CALLBACK_TOKEN
```

### 2. 查看配置

```bash
lansenger config show
```

### 3. 健康检查

验证凭证是否正确、能否成功获取 app token：

```bash
lansenger health check
```

## 命令总览

| 命令组 | 说明 | 子命令 |
|--------|------|--------|
| `config` | 管理凭证配置 | `set`, `show`, `clear`, `delete-profile`, `list-profiles`, `list-users` |
| `message` | 发送与管理消息 | `send-text`, `send-markdown`, `send-file`, `send-image-url`, `send-link-card`, `send-app-articles`, `send-app-card`, `send-oacard`, `send-bot-message`, `send-group-message`, `send-account-message`, `send-user-message`, `update-dynamic-card`, `revoke`, `query-groups` |
| `group` | 管理群组 | `create`, `info`, `members`, `list`, `check`, `update`, `update-members` |
| `staff` | 查询人员信息 | `basic-info`, `detail`, `ancestors`, `id-mapping`, `org-extra-fields`, `search`, `org-info` |
| `department` | 查询部门信息 | `detail`, `children`, `staffs` |
| `calendar` | 日程操作 | `primary`, `create-schedule`, `fetch-schedule`, `delete-schedule`, `list-schedules`, `attendees`, `add-attendees`, `delete-attendees`, `update-attendees`, `update-schedule`, `attendee-meta` |
| `todo` | 待办任务管理 | `create`, `update`, `update-status`, `delete`, `list`, `fetch-by-source`, `fetch-by-id`, `status-counts`, `executor-status`, `add-executors`, `delete-executors`, `executor-list` |
| `bot-command` | 机器人命令 | `create`, `query`, `delete` |
| `personal-app` | 个人应用 | `create`, `update`, `info`, `delete`, `list` |
| `oauth` | OAuth2 用户认证 | `authorize-url`, `exchange-code`, `refresh-token`, `user-info`, `parse-callback`, `validate-state` |
| `callback` | 回调事件解析 | `parse-payload`, `decrypt-payload`, `verify-signature`, `event-types` |
| `media` | 媒体文件操作 | `upload`, `upload-app`, `download`, `download-to-file` |
| `streaming` | 流式消息（AI 场景） | `create`, `fetch` |
| `chat` | 会话与消息记录 | `list`, `messages` |
| `health` | 连接健康检查 | `check` |

## 常用示例

### 发送消息

```bash
# 发送文本消息
lansenger message send-text chat123 "Hello World"

# 发送 Markdown 消息
lansenger message send-markdown chat123 "**Bold** text"

# 发送文件
lansenger message send-file chat123 /path/to/file.pdf

# 发送带图片 URL 的消息
lansenger message send-image-url chat123 https://example.com/photo.jpg

# 发送链接卡片
lansenger message send-link-card chat123 "公告标题" https://example.com --desc "点击查看详情"

# 发送应用卡片
lansenger message send-app-card chat123 "卡片标题" --content "正文内容" --card-link https://example.com

# 发送多条图文（appArticles）
lansenger message send-app-articles chat123 '{"title":"文章1","url":"https://a.com"}' '{"title":"文章2","url":"https://b.com"}'

# 发送 OA 审批卡片
lansenger message send-oacard chat123 "审批标题" --head "审批通知" --field '{"key":"申请人","value":"张三"}' --link https://app.com/approve

# 群内发送并 @all
lansenger message send-text group123 "全员通知" --group --mention-all

# 群内 @指定人
lansenger message send-text group123 "请查看" --group --mention staff001 --mention staff002

# @提及群中的特定机器人
lansenger message send-text group123 "Bot check" --group --mention-bot bot001 --mention-bot bot002

# 回复消息（消息引用）
lansenger message send-text group123 "Got it" --group --ref-msg-id 524288-xxx

# 机器人通道发送消息
lansenger message send-bot-message text '{"content":"通知内容"}' --chat-id user001 --chat-id user002

# 机器人通道回复（消息引用）
lansenger message send-bot-message text '{"content":"Reply"}' --chat-id user001 --ref-msg-id 524288-xxx

# 群消息通道发送（user_token 可选，无则显示为 bot）
lansenger message send-group-message group123 text '{"content":"群消息"}'

# 以人类用户身份发送（需要 user_token）
lansenger message send-group-message group123 text '{"content":"群消息"}' --user-token YOUR_USER_TOKEN --sender-id staff001

# 回复群消息
lansenger message send-group-message group123 text '{"content":"reply"}' --ref-msg-id 524288-xxx

# 应用账号通道发送
lansenger message send-account-message text '{"content":"账号消息"}' --chat-id user001 --account-id acct001

# 用户通道发送（需要 user_token）
lansenger message send-user-message user001 text '{"content":"私聊消息"}' --user-token YOUR_USER_TOKEN

# 撤回消息
lansenger message revoke msg001 msg002

# 查询群 ID 列表
lansenger message query-groups --page 0 --size 100
```

### 群组管理

```bash
# 创建群组
lansenger group create "项目群" org001 --staff staff001 --staff staff002

# 查看群信息
lansenger group info group123

# 查看群成员
lansenger group members group123

# 查看群列表（bot 可查看所在的群，传 user_token 可查看用户所在的群）
lansenger group list

# 查看用户所在的群列表（需要 user_token）
lansenger group list --user-token YOUR_USER_TOKEN

# 检查用户是否在群内
lansenger group check group123 --staff-id staff001

# 更新群信息
lansenger group update group123 --name "新名称" --desc "新描述"

# 添加/移除成员
lansenger group update-members group123 --add staff003 --remove staff001
```

### 人员查询

```bash
# 查看人员基本信息
lansenger staff basic-info staff001

# 查看人员详细信息
lansenger staff detail staff001

# 搜索人员
lansenger staff search 张三

# 手机号/邮箱映射 staff ID
lansenger staff id-mapping org001 phone 13800138000

# 查看组织信息
lansenger staff org-info org001
```

### 部门查询

```bash
# 查看部门详情
lansenger department detail dept001

# 查看子部门
lansenger department children dept001

# 查看部门内人员
lansenger department staffs dept001
```

### 会话与消息记录

```bash
# 获取会话列表（需要 user_token）
lansenger chat list --user-token YOUR_USER_TOKEN

# 只看群聊
lansenger chat list --type 2 --user-token YOUR_USER_TOKEN

# 搜索会话（关键词）
lansenger chat list --type 1 --keyword 张三 --user-token YOUR_USER_TOKEN

# 获取私聊消息记录
lansenger chat messages --staff-id staff001 --user-token YOUR_USER_TOKEN

# 获取群聊消息记录（bot 可直接获取所在群的消息）
lansenger chat messages --group-id group123

# 获取群聊消息记录（以用户身份，需要 user_token）
lansenger chat messages --group-id group123 --user-token YOUR_USER_TOKEN
```

### 日程操作

```bash
# 获取主日历
lansenger calendar primary --user-token YOUR_USER_TOKEN

# 创建日程（start/end 为秒级时间戳）
lansenger calendar create-schedule cal001 "周会" 1747539600 1747543200 \
  '[{"staffId":"staff001","attendeeFlag":"yes"}]' \
  --desc "每周例会" --user-token YOUR_USER_TOKEN

# 查看日程列表（start/end 为秒级时间戳）
lansenger calendar list-schedules cal001 1747539600 1747603200 --user-token YOUR_TOKEN

# 查看日程详情
lansenger calendar fetch-schedule cal001 schedule001 --user-token YOUR_TOKEN

# 删除日程
lansenger calendar delete-schedule cal001 schedule001 --user-token YOUR_TOKEN
```

### 待办任务

```bash
# 创建待办
lansenger todo create "审批文档" https://app.com/doc https://app.com/doc \
  "staff001,staff002" org001 --desc "请审批" --type 2

# 更新待办状态（11=待阅, 12=已阅, 21=待办, 22=已办）
lansenger todo update-status task001 22 org001

# 查看待办列表
lansenger todo list org001 --status 21,22

# 删除待办
lansenger todo delete task001 org001
```

### OAuth2 用户认证

```bash
# 生成授权 URL
lansenger oauth authorize-url https://yourapp.com/callback --scope basic_userinfor

# 交换 code 获取 user token
lansenger oauth exchange-code AUTH_CODE --redirect-uri https://yourapp.com/callback

# 刷新 user token
lansenger oauth refresh-token YOUR_REFRESH_TOKEN

# 获取用户信息
lansenger oauth user-info YOUR_USER_TOKEN
```

### 回调事件

```bash
# 查看所有回调事件类型
lansenger callback event-types

# 解析回调数据
lansenger callback parse-payload ENCRYPTED_DATA --encoding-key YOUR_KEY

# 解密回调数据（查看 orgId/appId/events）
lansenger callback decrypt-payload ENCRYPTED_DATA --encoding-key YOUR_KEY

# 验证签名
lansenger callback verify-signature TIMESTAMP NONCE SIGNATURE ENCODING_KEY --data-encrypt ENCRYPTED_DATA
```

### 媒体文件

```bash
# 上传核心平台文件
lansenger media upload /path/to/file.pdf --media-type 3

# 上传应用/机器人媒体文件（用于 send-text / send-file 等）
lansenger media upload-app /path/to/file.pdf --media-type file

# 下载媒体文件到本地
lansenger media download-to-file MEDIA_ID --output /path/to/save.pdf
```

### 流式消息

```bash
# 创建流式消息（用于 AI agent 渐进式输出）
lansenger streaming create user123 single stream-session-001

# 获取流式消息状态
lansenger streaming fetch MSG_ID
```

## 全局选项

| 选项 | 说明 |
|------|------|
| `--json` / `-j` | 输出原始 JSON 格式而非 rich 表格 |
| `--as <staff_id>` | 从凭证存储中自动加载并自动刷新指定 staff_id 的 user token |

```bash
# JSON 格式输出（便于脚本处理）
lansenger -j staff basic-info staff001

# 以指定用户身份执行命令（自动从凭证存储加载 user token）
lansenger --as staff001 chat messages --group-id group123
```

## Shell 自动补全

typer 内置补全支持：

```bash
# 安装补全
lansenger --install-completion

# 查看补全脚本
lansenger --show-completion
```

支持 bash、zsh、fish 等主流 shell。

## 多应用/多机器人配置（Profile）

CLI 支持多 profile，每个 profile 对应一个 appID（一个应用或一个机器人），凭证互相隔离：

```bash
# 配置第一个应用（个人机器人）
lansenger config set app_id xxx1 --profile my-bot
lansenger config set app_secret xxx1 --profile my-bot

# 配置第二个应用（蓝信应用）
lansenger config set app_id xxx2 --profile my-app
lansenger config set app_secret xxx2 --profile my-app
lansenger config set encoding_key yyy2 --profile my-app        # 此应用需要接收回调
lansenger config set callback_token zzz2 --profile my-app

# 切换应用执行命令
lansenger message send-text staff123 "Hello" --profile my-bot
lansenger callback parse-payload DATA --profile my-app

# 查看所有已配置 profile
lansenger config list-profiles

# 删除指定 profile（如为当前 active 则自动切换到 default）
lansenger config delete-profile my-bot

# 查看某个 profile 详情
lansenger config show --profile my-app
```

## 凭证安全

- 凭证按 profile 隔离存储在 `~/.lansenger/sdk_state.json`，文件权限 0600
- `config show` 对所有密钥类字段脱敏显示（`***`），仅 `api_gateway_url` 和 `passport_url` 明文展示
- 支持环境变量 `LANSENGER_APP_ID` / `LANSENGER_APP_SECRET` / `LANSENGER_ENCODING_KEY` / `LANSENGER_CALLBACK_TOKEN`，适合 CI/CD 场景

## 身份与权限

### 身份能力矩阵

蓝信平台有三种身份类型，各自拥有不同的 API 访问权限：

| 命令域 | 个人机器人 | 组织应用（自建） | 组织应用 + 机器人 | 说明 |
|--------|:---:|:---:|:---:|------|
| `message send-text/markdown/file/...`（机器人私聊） | **Y** | N | **Y** | 只有机器人可以发送机器人私聊 |
| `message send-text --group`（群聊） | **Y** | N | **Y** | 个人机器人现已支持群聊 |
| `message send-group-message` | **Y** | N | **Y** | 同上 |
| `message send-account-message`（公众号） | N | **Y** | **Y** | 需要公众号能力 |
| `message send-user-message`（用户对用户） | N | **Y** | **Y** | 需要 userToken + OAuth2 |
| `message revoke` | **Y** | **Y** | **Y** | 撤回自己发送的消息 |
| `staff *`（通讯录只读） | N | **Y** | **Y** | `search` 额外需要 userToken |
| `department *` | N | **Y** | **Y** | 仅组织级应用 |
| `calendar *` | N | **Y** | **Y** | 有 userToken = 用户身份；无 = 机器人身份 |
| `todo *` | N | **Y** | **Y** | 仅组织级应用 |
| `chat list/messages` | N | **Y** | **Y** | 仅组织级应用 |
| `group *`（群组管理 V2） | N | N | **Y** | 需要机器人已在群内 |
| `media upload` | **Y** | **Y** | **Y** | 通用上传 |
| `media upload-app` | **Y** | **Y** | **Y** | 仅自建应用（非 ISV） |
| `media download/path` | **Y** | **Y** | **Y** | 通用下载 |
| `oauth *` | N | **Y** | **Y** | 仅组织级应用 |
| `streaming *` | N | **Y** | **Y** | 仅组织级应用 |
| `callback *`（事件解析） | N/A | N/A | N/A | 纯数据操作，无需身份 |

> \* **N\*** = API 能力存在。

> **个人机器人**只能收发消息和上传/下载文件。不能访问通讯录、日历或 OAuth2。
>
> **组织应用 vs 组织应用 + 机器人**：使用相同的 appID/appSecret。唯一区别在于消息通道——只有机器人可以发送机器人私聊和群消息（因为只有机器人可以加入群组）。所有其他 API（通讯录、日历、待办、会话、OAuth2、流式消息）两者完全一致。目前仅自建应用支持机器人能力。

### 开发者中心权限

除了身份类型外，具体 API 调用还依赖蓝信开发者中心中的权限开关。组织可能限制开发者访问，需要管理员协助。

**基础权限（默认开启）：**

| 权限 | 说明 |
|------|------|
| 获取用户基本信息 | 获取人员基本信息，用于系统/应用登录 |
| 发送通知消息 | 获取组织消息通道，向人员/群组发送消息 |

**高级权限（默认关闭，需手动开启）：**

| 权限 | 说明 | 涉及的 Skill |
|------|------|-------------|
| 通讯录只读 | 通讯录读取权限 | `lansenger-staff`、`lansenger-department` |
| 通讯录编辑 | 通讯录编辑权限 | `lansenger-staff`（创建/更新/删除） |
| 敏感信息 - 手机号 | 获取用户手机号 | `lansenger-staff`（详情、ID 映射） |
| 敏感信息 - 邮箱 | 获取用户邮箱 | `lansenger-staff`（详情、ID 映射） |
| 敏感信息 - 身份证号 | 获取用户身份证号 | `lansenger-staff` |
| 敏感信息 - 工号 | 获取用户工号 | `lansenger-staff` |
| 唯一属性映射 staff ID | 将手机号/邮箱/工号映射为 staff ID | `lansenger-staff`（ID 映射） |
| 应用编辑 | 创建和更新应用 | 开发者中心管理 |
| 群组只读 | 群组读取权限 | `lansenger-group`（查询信息/成员） |
| 群组编辑 | 群组编辑权限 | `lansenger-group`（创建/更新/解散/成员） |
| 日程只读 | 日历和日程读取权限 | `lansenger-calendar`（查询） |
| 日程编辑 | 日历和日程编辑权限 | `lansenger-calendar`（创建/更新/删除） |
| 上传媒体 | 上传媒体文件权限 | `lansenger-media`（upload、upload-app） |
| 工作台模板读取 | 工作台模板读取权限 | — |
| 工作台模板写入 | 工作台模板写入权限 | — |

遇到权限错误时，请先确认身份类型是否支持该操作，再提示用户在开发者中心开启对应的高级权限（如无法访问请联系组织管理员）。

## CLI 兼容性

本 CLI 与 TypeScript 版、Go 版命令语法完全一致：

```bash
# Python CLI
pip install lansenger-cli

# Go CLI
go install github.com/lansenger-pm/lansenger-sdk-go/cmd/lansenger@latest

# TypeScript CLI
npm install -g lansenger-cli
```

## 与 SDK 的关系

本 CLI 基于 [lansenger-sdk-python](https://github.com/lansenger-pm/lansenger-sdk-python) 的 `LansengerSyncClient` 实现，覆盖 SDK 全部同步 API，不修改 SDK 代码。

## 许可证

MIT License
