# 泄露响应手册（harness/incident-response.md）

> 定位：Harness ⑥权限层·凭证治理四件套之一。发现凭证疑似泄露时按类型执行「止血 → 排因 → 加固」。
> 原则：Agent 发现泄露迹象**立即停止相关操作并报告人工**，本手册动作全部由人工执行（Agent 只提供定位信息：文件:行:键名）。

## app_id / app_secret（蓝信开放平台应用凭证）

- **止血**：登录蓝信开放平台管理后台 → 重置应用 Secret（旧值立即失效）；若 CLI 侧 `~/.lansenger/sdk_state.json` 已泄露，同步删除该文件。
- **排因**：查泄露源——git 历史（`git log -p -- <path>`）、CI 日志、终端历史、分享材料；扫描器历史日志在 `harness/verify-logs/`（本地，不入库）。
- **加固**：确认无硬编码（`bash scripts/verify.sh` 全绿）；优先用 `LANSENGER_APP_SECRET` 环境变量通道；如曾在仓库出现 → 联系平台清理 git 历史前先评估（改历史属 🚫，须人工决策）。

## userToken（OAuth2 用户令牌，`--as` 刷新链路）

- **止血**：蓝信 Passport 侧吊销该 userToken（撤销会话）；删除本地 sdk_state.json 中该 profile（人工操作）。
- **排因**：确认泄露渠道（终端回显 / 日志 verbose / 截图）；`--verbose` 会开 SDK DEBUG 日志——检查是否在共享终端/CI 输出过 token。
- **加固**：回归「禁回显 token」红线（docs/action-boundary.md 🚫）；对外支持场景改用 `--dry-run` 展示计划动作而非真实调用。

## encoding_key / callback_token（回调验签密钥）

- **止血**：开放平台后台轮换 encoding_key / callback_token；旧密钥在轮换窗口后失效。
- **排因**：检查是否有测试/示例把真实密钥写进仓库（扫描器只拦「入库」，不拦口头/截图外泄）；核对 `harness/verify-allowlist` 存量段是否被异常扩充（洗白用法是红线）。
- **加固**：回调解析示例一律用占位符；`evals/` 增加对应回归案例。

## PyPI 发布凭证（GitHub Actions Secrets）

- **止血**：PyPI 项目页撤销该 token；GitHub repo Settings → Secrets 删除并重建。
- **排因**：GitHub Security → Secret scanning / Audit log（按时间+workflow 名反查）；确认 release.yml 是否被异常改动（PR 记录）。
- **加固**：保持 release.yml `permissions: contents: read` 最小权限；发布凭证限 scoped token；Agent 对 `.github/workflows/` 的改动走 ⚠️ 级授权。

## 通用升级路径

1. Agent 侧：发现即停 → 只报告「文件:行:键名 + 已执行只读动作」→ 不自行轮换/改历史。
2. 人工侧：按上文类型执行三段 → 处理完在 KNOWLEDGE.md 记一条坑（脱敏）→ 高频场景回登记 docs/action-boundary.md 或升级为机制。
