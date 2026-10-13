# 凭证盘点报告（harness/report-credentials.md）

> 纪律：全程**只读元数据**（文件存在性 / 权限位 / 键名），禁止摘录、回显、转存任何凭证值。
> 分级：高 = 全局可写 / 明文落盘且 Agent 可读；中 = 组可读 / 明文存储；低 = Keychain / 动态短时化。
> 盘点：2026-10-13 ｜ 手段：`scripts/scan_secrets.py`（键名集见 harness/verify-allowlist 头部）+ 文件系统元数据探测。

| # | 工具/位置 | 盘点结果（权限/键名级） | 风险 | 说明 |
|---|---|---|---|---|
| 1 | `~/.lansenger/sdk_state.json`（运行时） | 存在性由 README 证实；键面含 app_id / app_secret / api_gateway_url / identity_type / passport_url / encoding_key / callback_token / userToken（键名级，值未读） | 高 | CLI 的核心凭证落盘处。README 声明 0600，但 **CLI 代码内未见 chmod 实现**（可能在 SDK）——验证=人工待办。Agent 禁读值 |
| 2 | 仓库内源码/文档/CI 配置 | 扫描零命中（43 文件；`token_data = store.load_user_token()` 类误报已机制化过滤） | — | 详见 harness/verify-allowlist 误报段判据 |
| 3 | `LANSENGER_*` 环境变量（用户 shell / CI） | 键名面见 README（APP_ID/APP_SECRET/ENCODING_KEY/CALLBACK_TOKEN）；值在环境，不在仓库 | 中 | CI/CD 友好通道；Agent 禁 print/export 回显 |
| 4 | GitHub Actions Secrets | release.yml 需 PyPI 发布凭证（平台侧配置，仓库不可见） | 中 | 轮换入口在 GitHub repo Settings → Secrets |
| 5 | OAuth2 userToken（`--as` 自动刷新后） | 由 SDK 写回 #1 位置 | 高 | 同 #1 |
| 6 | 测试中的凭证 | tests/ 全量 mock（`MagicMock`），无真实凭证字面量（扫描证实） | — | 保持此模式：新增测试禁止引入真实凭证 |

## 已执行动作（权限收紧：只减不增、逐条可逆、先评估影响）

- N/A——仓库内文件权限位扫描无过宽项（`find -perm -go+w` 零命中）；#1、#3、#4 均在仓库外，本次不触碰（跨边界动作一律人工）。

## 遗留风险与预案（诚实登记）

| 做不到什么 | 拿什么补 | 人工待办 |
|---|---|---|
| 无法验证 sdk_state.json 实际权限位与 SDK 端 0600 实现 | 扫描器挡住凭证入库；边界表禁读值 | 人工执行 `ls -l ~/.lansenger/sdk_state.json`；非 0600 则 `chmod 600` 并查 SDK 是否需要修复 |
| 自研扫描器为键名+赋值形态匹配，非数据流分析，存在理论漏报（如拼接构造的凭证字符串） | 最小键名集 + 棘轮只减不增；演进项可接 gitleaks（`brew install gitleaks` 后把 verify.sh 第 4 步替换/叠加） | 团队确认是否引入 gitleaks |
| CI 尚无扫描步骤，本地 verify 可被绕过 | 边界表 🚫 + 评审拦截 | P1：ci.yml 加 `bash scripts/verify.sh`（或至少 ruff + scan_secrets） |
| 凭证轮换无法由 Agent 代办 | incident-response.md 提供人工响应清单 | 无 |

## 响应手册

## 安全门（提交前校验条件，2026-10-13 起）

verify 第 4 步即安全门，以下检测器任一命中 = FAIL 阻断提交（probe 负向自检已验证拦截）：

| 检测器 | 抓什么 | 误报出口 |
|---|---|---|
| 凭证形态（R1/R2 + 占位符过滤） | 键值形态的 secret/token/credential… | 误报段判据 / is_placeholder 机制 |
| `internal-endpoint` | 内部测试环境主机族（open-*/user-*.{e,t}.lanxin.cn） | 误报段 |
| `long-hex-value` | ≥32 位涣散 hex（stray token/哈希） | 误报段（legit 依赖哈希等）/ 存量棘轮段 |
| `blocklisted-value` | 本地黑名单片段（会话真实凭证/测试 appId/内部端点） | 黑名单文件本身维护（gitignored+0600） |

维护规则：新增高危值 → 追加 `harness/security-blocklist.local` 一行（该文件绝不入库）；黑名单内容本身含敏感片段，泄露面 = 本机。

凭证泄露的止血/排因/加固三段清单见 [harness/incident-response.md](incident-response.md)。
