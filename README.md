# Lansenger CLI

蓝信（Lansenger）命令行工具 — 在终端直接调用蓝信开放平台 API，发送消息、管理群组、查询人员/部门、操作日程与待办等。

## 安装

```bash
pip install lansenger-cli
```

或从源码安装：

```bash
pip install -e .
```

需要 Python ≥ 3.10。

## 快速开始

### 1. 配置凭证

通过 `config set` 命令保存 app 凭证（存储在 `~/.lansenger/sdk_state.json`，密钥脱敏显示）：

```bash
lansenger config set app_id YOUR_APP_ID
lansenger config set app_secret YOUR_APP_SECRET
```

也可以通过环境变量配置（适合 CI/CD 或临时使用）：

```bash
export LANSENGER_APP_ID=YOUR_APP_ID
export LANSENGER_APP_SECRET=YOUR_APP_SECRET
```

可选：设置私有部署网关地址和 OAuth2 passport 地址：

```bash
lansenger config set api_gateway_url https://your-gateway.example.com/open/apigw
lansenger config set passport_url https://your-passport.example.com
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
| `config` | 管理凭证配置 | `set`, `show`, `clear` |
| `message` | 发送与管理消息 | `send-text`, `send-markdown`, `send-file`, `send-image-url`, `send-link-card`, `send-app-articles`, `send-app-card`, `update-dynamic-card`, `revoke`, `query-groups` |
| `group` | 管理群组 | `create`, `info`, `members`, `list`, `check`, `update`, `update-members` |
| `staff` | 查询人员信息 | `basic-info`, `detail`, `ancestors`, `id-mapping`, `org-extra-fields`, `search`, `org-info` |
| `department` | 查询部门信息 | `detail`, `children`, `staffs` |
| `calendar` | 日程操作 | `primary`, `create-schedule`, `fetch-schedule`, `delete-schedule`, `list-schedules`, `attendees`, `add-attendees`, `delete-attendees` |
| `todo` | 待办任务管理 | `create`, `update`, `update-status`, `delete`, `list`, `fetch-by-source`, `fetch-by-id`, `status-counts`, `executor-status`, `add-executors`, `delete-executors`, `executor-list` |
| `oauth` | OAuth2 用户认证 | `authorize-url`, `exchange-code`, `refresh-token`, `user-info`, `parse-callback`, `validate-state` |
| `callback` | 回调事件解析 | `parse-payload`, `verify-signature`, `event-types` |
| `media` | 媒体文件操作 | `upload`, `download`, `download-to-file` |
| `streaming` | 流式消息（AI 场景） | `create`, `fetch` |
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

# 群内发送并 @all
lansenger message send-text group123 "全员通知" --group --mention-all

# 群内 @指定人
lansenger message send-text group123 "请查看" --group --mention staff001 --mention staff002

# 撤回消息
lansenger message revoke msg001 msg002
```

### 群组管理

```bash
# 创建群组
lansenger group create "项目群" org001 --staff staff001 --staff staff002

# 查看群信息
lansenger group info group123

# 查看群成员
lansenger group members group123

# 查看群列表
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

### 日程操作

```bash
# 获取主日历
lansenger calendar primary --user-token YOUR_USER_TOKEN

# 创建日程
lansenger calendar create-schedule cal001 "周会" \
  '{"dateTime":"2026-01-01T09:00:00","timeZone":"Asia/Shanghai"}' \
  '{"dateTime":"2026-01-01T10:00:00","timeZone":"Asia/Shanghai"}' \
  '[{"staffId":"staff001"}]' \
  --desc "每周例会"

# 查看日程列表
lansenger calendar list-schedules cal001 1735689600 1735776000 --user-token YOUR_TOKEN
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

# 验证签名
lansenger callback verify-signature TIMESTAMP NONCE SIGNATURE ENCODING_KEY
```

### 媒体文件

```bash
# 上传文件
lansenger media upload /path/to/file.pdf --media-type 3

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

```bash
# JSON 格式输出（便于脚本处理）
lansenger -j staff basic-info staff001
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

## 凭证安全

- 凭证存储在 `~/.lansenger/sdk_state.json`，文件权限 0600
- `config show` 命令对 `app_id` 和 `app_secret` 脱敏显示（`***`）
- 也支持环境变量 `LANSENGER_APP_ID` / `LANSENGER_APP_SECRET`，适合 CI/CD 场景

## 与 SDK 的关系

本 CLI 基于 [lansenger-sdk](https://github.com/lansenger-pm/lansenger-skills-official) 的 `LansengerSyncClient` 实现，覆盖 SDK 全部同步 API，不修改 SDK 代码。

## 许可证

MIT License