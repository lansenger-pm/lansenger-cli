# Harness 成熟度自评（harness/maturity.md）

> 评估：2026-10-13（Bootstrap 首建轮终审）｜ 六组件各 0–2 分：0 缺失 / 1 提示级 / 2 机制级（当前环境实际可运行生效；需人工一条命令才生效算 1）。
> 总分 **9 / 12**（合格线 7–9，且门禁/权限/指令三组件 ≥2 ✅）。

| 组件 | 得分 | 依据（本轮实证） | 距 2 分的差距 |
|---|---|---|---|
| 指令 | 2 | AGENTS.md 87 行（≤150，余量 63）纯索引+红线；细则分层落 docs/（架构+边界）、harness/（盘点/凭证/棘轮）、evals/、KNOWLEDGE.md；「只迁移不删除」与度量裁剪约定成文 | skills/ 命名层未建（以 docs/ 代位）；按需拆分 |
| 工具 | 1 | verify.sh 固化高频验证链 + 四态输出契约；退出码 0/1/10 即 CLI 自身的输出契约 | 日常操作（发版/批量命令域生成）无封装脚本 |
| 门禁 | 2 | verify 一条命令（lint/test/build/secrets 四态 + 棘轮）**实测跑通**；探针负向自检实证 FAIL 真拦截（EXIT 1）；pre-commit 已落盘待激活（`git config core.hooksPath scripts/hooks`，一条命令） | hook 激活属人工动作（计分已按规则不虚高）；CI 侧门禁待补 |
| 权限 | 2 | 三级边界表 + CLI 白名单 + 特有高危登记 + 凭证治理四件套（盘点零值化 / 收紧 N/A 如实登记 / 扫描器审计 / 响应手册）+ 产品内建 exit-10 高危门 | 「真实凭证联网查询 ⚠️」无技术强制，靠纪律+mock 红线兜底 |
| 记忆 | 1 | KNOWLEDGE.md 本轮真实沉淀 6 条（含门禁自检抓到双根因缺陷的教训）；事故档案已立 | 回写靠纪律，无会话收尾机制提醒 |
| 评估 | 1 | evals 5 案例（含本仓最易违反的 CR-03）+ 回放记录表 + 重放触发约定 | 重放为手动；未接自动触发 |

## 首建轮关键事件（诚实记录）

1. **负向自检两次抓真缺陷**：凭证探针 `API_SECRET="…"` 首跑假 PASS → 双根因（缺 IGNORECASE + `\b` 对 snake_case 失效）→ 修复 → 重放真 FAIL（EXIT 1）→ 清理后恢复全绿。已机制化沉淀 KNOWLEDGE。
2. **误报机制化**：`token_data = store.load_user_token()` 形态以扫描器规则过滤（非基线豁免）。
3. **.gitignore 修正**：原忽略 `AGENTS.md`/`docs/`，与 release.yml 引用 AGENTS.md 的事实矛盾——已解除。

## 下一批演进建议（按性价比排序，标尺 S≤2h / M≤2d / L>2d）

| # | 建议 | 成本 | 说明 |
|---|---|---|---|
| 1 | ci.yml 接入 `bash scripts/verify.sh`（或至少 ruff+secrets） | S | 堵「本地绿远端不管」缺口；改 CI 属 ⚠️ 级待授权 |
| 2 | 人工激活 pre-commit：`git config core.hooksPath scripts/hooks` | S | 已落盘，一条命令生效 |
| 3 | 人工验证 `~/.lansenger/sdk_state.json` 权限位（README 称 0600，CLI 侧未见实现） | S | 见 report-credentials.md 待办 |
| 4 | mypy/pyright 渐进接入（先 utils.py 与高危门） | M | 大模块静态保障 |
| 5 | 补 9 个无测试命令域的最小回归（group/staff/department/calendar/oauth/callback/streaming/chat/bot-command 等） | M | 测试镜像契约 C8 |
| 6 | 高频操作封装（发版 checklist 脚本 / 新命令域脚手架） | M | 工具组件 1→2 |
| 7 | SDK 联动集成测试沙箱（mock server 跑真实 client 路径） | L | 覆盖 `--as` 刷新链路 |

## 持续演化约定

- 周回顾三问：本周哪些约束被违反？（→ 候选机制化）哪些从未生效？（→ 候选裁剪）verify 有无新 SKIP？
- 约束变更 → evals 重放；模型升级 → evals 重放；新事故 → 新案例（KNOWLEDGE ↔ evals 联动）。
- 度量从下一个真实需求开始累积（templates/delivery-report.md 双表）。
