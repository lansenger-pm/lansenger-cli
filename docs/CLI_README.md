# Lansenger CLI

Lansenger CLI 是蓝信开放平台的命令行工具，让开发者在终端直接调用蓝信常用 API，无需写代码。支持消息发送、通讯录查询、群组管理、日历日程、待办任务等核心功能。

提供 **Python 版** 和 **Go 版** 两个版本，命令和参数完全一致，凭证配置共享同一文件，选择任一即可。

## 两个版本

| | Python 版 | Go 版 |
|---|---|---|
| **安装** | `pip install lansenger-cli` | `go install github.com/lansenger-pm/lansenger-sdk-go/cmd/lansenger@latest` |
| **运行依赖** | Python 3.10+ | 无（单 binary 9.4MB） |
| **适用场景** | 已有 Python 环境、与 Python SDK 配合 | CI/CD、容器、不想装 Python |
| **分发渠道** | PyPI | GitHub |
| **表格输出** | Rich 格式化表格 | 纯文本表格 |
| **凭证文件** | `~/.lansenger/sdk_state.json` | 同一文件，共享 |

> 两个版本共享 `~/.lansenger/sdk_state.json`，配置一次两个 CLI 都能用。

## 特性

- **68 个子命令** — 覆盖蓝信开放平台大部分常用 API
- **多 Profile 支持** — `-P` 参数一键切换凭证环境
- **JSON 输出** — `-j` 输出标准 JSON，方便脚本和 AI Agent 解析
- **格式化表格** — 默认输出结构化表格
- **凭证持久化** — 配置一次，永久生效，无需每次输入密钥

## 安装

### Python 版

```bash
pip install lansenger-cli
```

当前版本：0.5.0，支持 Python 3.10+。

### Go 版

```bash
go install github.com/lansenger-pm/lansenger-sdk-go/cmd/lansenger@latest
```

零依赖，编译为单 binary，无需任何运行时环境。也可从 GitHub Releases 下载预编译 binary。

安装后即可使用 `lansenger` 命令。

## 首次配置

```bash
# 设置应用凭证（首次使用必须）
lansenger config set app_id 你的应用ID
lansenger config set app_secret 你的应用密钥

# 私有部署需要额外设置网关地址
lansenger config set api_gateway_url https://your-gateway.example.com
lansenger config set passport_url https://passport.example.com

# 查看当前配置
lansenger config show

# 验证连接
lansenger health check
```

> **注意**：私有部署的 `api_gateway_url` 只填写网关域名，不要追加 `/open/apigw`。

## 多环境配置

CLI 支持多 Profile，每个 Profile 独立保存一套凭证：

```bash
# 创建生产环境 Profile
lansenger -P prod config set app_id prod-app-id
lansenger -P prod config set app_secret prod-secret
lansenger -P prod config set api_gateway_url https://prod-gateway.example.com

# 创建测试环境 Profile
lansenger -P staging config set app_id staging-app-id
lansenger -P staging config set app_secret staging-secret

# 查看所有 Profile
lansenger config list-profiles

# 使用指定 Profile 执行命令
lansenger -P prod message send-text 用户openId "生产环境消息"
```

## 全局选项

所有命令都支持以下全局选项：

| 选项 | 简写 | 说明 |
|------|------|------|
| `--json` | `-j` | 输出标准 JSON（双引号、缩进），适合脚本解析 |
| `--profile` | `-P` | 指定凭证 Profile，默认 `default` |

建议 `-P` 放在命令前面，符合主流 CLI 工具习惯：

```bash
lansenger -P prod -j staff basic-info openId
```

## 命令总览

| 命令组 | 子命令数 | 功能 |
|--------|---------|------|
| `config` | 4 | 凭证配置管理 |
| `message` | 13 | 消息发送与管理 |
| `staff` | 7 | 通讯录查询 |
| `department` | 3 | 部门信息查询 |
| `group` | 7 | 群组管理 |
| `calendar` | 7 | 日历与日程 |
| `todo` | 10 | 待办任务管理 |
| `oauth` | 6 | OAuth2 用户认证 |
| `callback` | 3 | 回调事件解析 |
| `media` | 3 | 文件上传下载 |
| `streaming` | 2 | 流式消息（AI Agent） |
| `chat` | 2 | 聊天记录查询 |
| `health` | 1 | 连接健康检查 |

## 消息发送

### 纯文本

```bash
lansenger message send-text 用户openId "你好！"
```

### Markdown

```bash
lansenger message send-markdown 用户openId "# 标题\n正文内容"
```

### 带附件

```bash
lansenger message send-text 用户openId "请查看附件" --file /path/to/file.pdf
```

### 发送图片

```bash
# 本地图片
lansenger message send-file 用户openId /path/to/image.jpg --media-type 2

# 图片 URL（内网可用）
lansenger message send-image-url 用户openId https://example.com/image.jpg --caption "图片说明"
```

### 链接卡片

```bash
lansenger message send-link-card 用户openId "文档标题" https://example.com --desc "点击查看"
```

### 图文消息

```bash
lansenger message send-app-articles 用户openId '{"title":"文章1","url":"https://example.com/1"}' '{"title":"文章2","url":"https://example.com/2"}'
```

### 应用卡片

```bash
lansenger message send-app-card 用户openId "审批通知" \
  --head-title "OA审批" \
  --content "<font color='red'>紧急</font> 请尽快处理" \
  --field '{"key":"申请人","value":"张三"}' \
  --field '{"key":"日期","value":"2026-01-15"}' \
  --link '{"title":"点击审批","url":"https://example.com/approve"}' \
  --dynamic  # 启用动态更新
```

### OA审批卡片

```bash
lansenger message send-oacard 用户openId "出差申请" \
  --field '{"key":"目的地","value":"上海"}' \
  --field '{"key":"天数","value":"3天"}' \
  --link https://example.com/oa
```

### 群组消息

所有 send 命令加 `--group/-g` 即可发送到群：

```bash
# 群文本 + @所有人
lansenger message send-text 群openId "群通知" -g --mention-all

# 群 Markdown + @指定人
lansenger message send-markdown 群openId "@张三 请处理" -g --mention staffId1 --mention staffId2
```

### 动态卡片更新

```bash
# 先发送动态卡片（加 --dynamic），获取完整 msgId
lansenger -j message send-app-card 用户openId "审批中" --dynamic --status-desc "待审批" --status-colour "#FFB116"

# 更新卡片状态为已批准
lansenger message update-dynamic-card msgId --status-desc "已批准" --status-colour "#00B578" --last
```

> **重要**：动态卡片更新需要完整 msgId，建议用 `-j` 获取 JSON 输出，避免终端表格截断长 ID。

### 消息撤回

```bash
lansenger message revoke msgId1 msgId2 --chat-type bot
```

## 四种消息通道

| 命令 | 通道 | 说明 |
|------|------|------|
| `send-text/markdown/file/link-card/app-card/oacard` | 智能机器人 | 最常用，支持 `-g` 切换私聊/群聊 |
| `send-bot-message` | Bot广播 | 批量推送（多用户/部门） |
| `send-account-message` | 公号消息 | 以应用公号身份发送 |
| `send-user-message` | 用户私聊 | 需 userToken，代用户发消息 |

```bash
# Bot 广播
lansenger message send-bot-message text '{"content":"通知"}' --chat-id openId1 --chat-id openId2

# 公号消息
lansenger message send-account-message text '{"content":"公告"}' --chat-id openId1 --account-id accountId

# 用户私聊（需 userToken）
lansenger message send-user-message receiverId text '{"content":"私聊"}' --user-token userToken
```

## 通讯录

```bash
# 人员基本信息
lansenger staff basic-info openId

# 人员详细信息
lansenger staff detail openId

# 部门祖先链
lansenger staff ancestors openId

# ID 映射（手机号→openId）
lansenger staff id-mapping orgId phone 13800138000

# 人员搜索
lansenger staff search "张三"

# 组织信息
lansenger staff org-info orgId

# 组织自定义字段
lansenger staff org-extra-fields orgId
```

## 部门

```bash
# 部门详情
lansenger department detail 部门openId

# 子部门列表
lansenger department children 部门openId

# 部门人员列表
lansenger department staffs 部门openId -p 1 -s 100
```

## 群组管理

```bash
# 创建群组
lansenger group create "项目讨论群" orgId --owner 群主openId --staff member1 --staff member2

# 群信息
lansenger group info 群openId

# 群成员
lansenger group members 群openId

# 群列表
lansenger group list

# 检查人员是否在群
lansenger group check 群openId --staff-id openId

# 更新群设置
lansenger group update 群openId --name "新群名"

# 添加/移除成员
lansenger group update-members 群openId --add staffId1 --add staffId2 --remove staffId3
```

## 日历与日程

```bash
# 获取主日历
lansenger calendar primary --user-token userToken

# 创建日程（秒级时间戳）
lansenger calendar create-schedule calendarId "项目评审会" \
  1735689600 1735693200 \
  '[{"staffId":"openId","attendeeFlag":"yes"}]' \
  --tz Asia/Shanghai --user-token userToken

# 创建全天日程
lansenger calendar create-schedule calendarId "团建活动" 0 0 '[]' \
  --all-day yes --date 2026-01-15 --user-token userToken

# 查询日程
lansenger calendar fetch-schedule calendarId scheduleId --user-token userToken

# 日程列表
lansenger calendar list-schedules calendarId 1735689600 1735776000 --user-token userToken

# 删除日程
lansenger calendar delete-schedule calendarId scheduleId --user-token userToken

# 参与人员
lansenger calendar attendees calendarId scheduleId --user-token userToken
```

## 待办任务

```bash
# 创建待办
lansenger todo create "请审批出差" https://example.com https://example.com "staffId1,staffId2" orgId --type 2

# 更新状态
lansenger todo update-status taskId 22 orgId  # 11=待阅 12=已阅 21=待办 22=已完成

# 查询列表
lansenger todo list orgId

# 按sourceId查询
lansenger todo fetch-by-source sourceId orgId

# 状态统计
lansenger todo status-counts staffId orgId

# 管理执行人
lansenger todo add-executors "staffId3,staffId4" orgId --task-id taskId
lansenger todo delete-executors "staffId5" orgId --task-id taskId
lansenger todo executor-list taskId orgId
```

## OAuth2 用户认证

```bash
# 生成授权 URL
lansenger oauth authorize-url https://your-app.com/callback

# 换取 userToken
lansenger oauth exchange-code authorizationCode --redirect-uri https://your-app.com/callback

# 刷新 userToken
lansenger oauth refresh-token refreshToken

# 查询用户信息
lansenger oauth user-info userToken

# 解析回调参数
lansenger oauth parse-callback "code=xxx&state=yyy"

# 验证 state
lansenger oauth validate-state callbackState expectedState
```

## 聊天记录

```bash
# 会话列表
lansenger chat list -t 1 --user-token userToken  # -t: 0=全部 1=私聊 2=群聊

# 查看聊天消息
lansenger chat messages --staff-id openId --user-token userToken  # 私聊
lansenger chat messages --group-id 群openId --user-token userToken  # 群聊
```

## 回调事件

```bash
# 解析回调数据
lansenger callback parse-payload encryptedData --encoding-key yourKey

# 验证签名
lansenger callback verify-signature timestamp nonce signature encodingKey

# 查看所有事件类型
lansenger callback event-types
```

## 文件上传下载

```bash
# 上传文件
lansenger media upload /path/to/file.pdf -t 3  # 1=视频 2=图片 3=文件

# 下载媒体
lansenger media download mediaId

# 下载并保存到本地
lansenger media download-to-file mediaId -o /path/to/save.jpg --media-type image
```

## 流式消息

```bash
# 创建流式消息（AI Agent 场景）
lansenger streaming create receiverId staff streamId

# 查询流式消息状态
lansenger streaming fetch msgId
```

## 健康检查

```bash
lansenger health check
```

输出 `OK` 表示连接正常，凭证有效。

## JSON 输出与脚本集成

`-j` 输出标准 JSON，适合脚本解析和 AI Agent 调用：

```bash
# 获取完整 msgId（避免表格截断）
lansenger -j message send-app-card openId "审批" --dynamic

# 脉冲式获取人员列表
lansenger -j staff search "张三" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data['staff_info'][0]['name'])"

# 查询群成员
lansenger -j group members 群openId | jq '.members[].name'
```

## 配置管理

```bash
# 设置凭证
lansenger config set app_id xxx
lansenger config set app_secret xxx
lansenger config set api_gateway_url https://gateway.example.com
lansenger config set passport_url https://passport.example.com

# 查看配置（密钥自动掩码）
lansenger config show

# 查看所有 Profile
lansenger config list-profiles

# 清除指定 Profile
lansenger config clear --profile staging

# 清除所有配置
lansenger config clear --all
```

## 环境变量

也可以通过环境变量提供凭证，无需 config set：

```bash
export LANSENGER_APP_ID=你的应用ID
export LANSENGER_APP_SECRET=你的应用密钥
export LANSENGER_API_GATEWAY_URL=https://gateway.example.com  # 私有部署
lansenger health check
```

## 项目地址

- Python CLI：https://github.com/lansenger-pm/lansenger-cli / https://pypi.org/project/lansenger-cli/
- Go CLI：https://github.com/lansenger-pm/lansenger-sdk-go（CLI 位于 `cmd/lansenger/`）

## License

MIT