# Bootstrap 盘点报告（Harness 阶段 0 · 只读）

> 生成：2026-10-13 ｜ 执行者：Fabric Agent ｜ 依据：Harness Bootstrap Playbook v3
> 定位：本报告是 AGENTS.md / verify / 边界表等所有约束产物的**事实源**；后续探测更新时增量维护。

## ① 技术栈清单

| 维度 | 事实 | 事实源 |
|---|---|---|
| 语言 | Python ≥ 3.10 | pyproject.toml `requires-python` |
| CLI 框架 | typer ≥ 0.9（rich_markup_mode="rich"） | pyproject.toml + main.py |
| 输出渲染 | rich ≥ 13 | pyproject.toml |
| 核心依赖 | lansenger-sdk ≥ 1.12.0（同步客户端 + CredentialStore + 认证） | pyproject.toml |
| 构建 | setuptools ≥ 64（PEP 621）；`uv build` 实测可用 | pyproject.toml `[build-system]` |
| 包管理 | uv（uv.lock 存在，实测 uv 0.12.5）；发布走 PyPI | uv.lock、release.yml |
| Lint | ruff（line-length=120，select F/E/W/B，ignore E501/F401/F821/F841/B008） | pyproject.toml `[tool.ruff]` |
| 类型检查 | 无（mypy/pyright 未配置） | 缺失 |
| 测试 | pytest ≥ 7（实测 88 passed） | tests/ + 实测 |
| CI | GitHub Actions：ci.yml = pytest 矩阵 3.10–3.13；release.yml = tag↔pyproject 版本硬校验 + 测试 + 发布 | .github/workflows/ |
| 运行时凭证 | 用户凭证存 `~/.lansenger/sdk_state.json`（README 声明 0600，CLI 代码未见 chmod 实现——可能由 SDK 负责，验证=人工待办） | README.md、config.py |

## ② 目录地图

```
lansenger-cli/
├── src/lansenger_cli/
│   ├── main.py            # typer app 装配：注册 16 个命令组 + 全局选项 callback
│   ├── qr.py              # 零依赖 QR 编码/渲染（设备码登录终端制码 + --qr-png）
│   ├── utils.py           # 共享层：全局状态 setter、get_client 工厂、退出码契约、confirm_high_risk 门、output_result
│   ├── commands/          # 16 个命令域模块（config/message/group/staff/department/
│   │                      #   calendar/oauth/callback/media/streaming/chat/health/
│   │                      #   bot-command/personal-app/videoconference + __init__）
│   ├── __init__.py / __main__.py
├── tests/                 # 8 个测试文件（88 例），CliRunner + mock get_client 模式
├── .github/workflows/     # ci.yml / release.yml
├── scripts/               # 【新增 Harness】verify.sh、scan_secrets.py、hooks/
├── docs/                  # 【新增 Harness】architecture.md、action-boundary.md
├── harness/               # 【新增 Harness】盘点/凭证/棘轮/成熟度
├── evals/                 # 【新增 Harness】约束回归集
├── templates/             # 【新增 Harness】交付报告度量模板
├── AGENTS.md              # 【新增 Harness】Agent 索引 + 红线
├── KNOWLEDGE.md           # 【新增 Harness】踩坑沉淀
└── README*.md（5 语言）   # 用户文档：任何用户可见面变更必须 5 语言同步
```

模块依赖方向（实测 import 关系）：`main.py → commands/* → utils → lansenger_sdk`；**commands/* 之间零横向依赖**（grep 实证）；tests → CliRunner 驱动 main，mock `commands.*.get_client`。

## ③ 已有可执行检查清单（盘点时已存在）

| 检查 | 命令 | 状态 |
|---|---|---|
| Lint | `uv run ruff check .` | ✅ 实测 All checks passed |
| 单测 | `uv run --extra dev pytest -q` | ✅ 实测 88 passed |
| 构建 | `uv build` | ✅ 实测通过 |
| CI 单测 | ci.yml（Python 3.10/3.11/3.12/3.13 矩阵） | ✅ 远端执行 |
| 发版门禁 | release.yml：git tag 必须等于 pyproject version | ✅ 机制级 |
| 产品内高危门 | `confirm_high_risk`：高危写命令无 `--yes` → 结构化确认 + exit 10；`--dry-run` 只验参不执行 | ✅ 机制级（utils.py:273） |

## ④ 缺失清单（Bootstrap 前不存在、本次补齐或列为待办）

| 缺失项 | 影响 | 处置 |
|---|---|---|
| AGENTS.md（release.yml 甚至引用了它但文件不存在且被 gitignore） | Agent 每次会话无项目约束 | ✅ 本次补齐（并修正 .gitignore） |
| 统一 verify 入口 | 各检查散落、无四态语义 | ✅ 本次补齐 scripts/verify.sh |
| 凭证扫描 + 棘轮基线 | 凭证入库无防线 | ✅ 本次补齐（首跑零命中，误报 1 类已机制化修复） |
| 三级行动边界表 / CLI 白名单 | Agent 对本仓高危面无授权边界 | ✅ 本次补齐 docs/action-boundary.md |
| 架构文档 / 契约同步清单 | 契约漂移无清单可查 | ✅ 本次补齐 docs/architecture.md |
| CI 只跑 pytest：**ruff 未进 CI**、无凭证扫描、无构建验证 | 本地绿不等于远端绿 | ⚠️ 列人工待办 P1（改 CI 属 ⚠️ 级，本次不动） |
| 类型检查（mypy/pyright） | 大型命令模块（videoconference 484 行）缺静态保障 | ⚠️ 演进项（成本 M） |
| 测试覆盖不均：16 个命令域只有 7 个测试文件 | 新增/改动域可能无回归 | ⚠️ 演进项（新域必须带测试，存量渐进补） |

## ⑤ 风险 Top5

1. **用户可见面=5 语言 README 同步负担**：0.14.0 移除 7 个应用域时五语言 README/命令表/能力矩阵全量同步——漏改任意一份即文档漂移（CHANGELOG 实证该流程存在）。→ 已入 AGENTS.md 红线 + evals CR-05。
2. **退出码与高危门是脚本/Agent 集成契约**：EXIT 0/1/10 + `--yes`/`--dry-run` 语义被外部脚本依赖，改动即破坏调用方。utils.py 注释明言「stable contract for agents/scripts」。→ 契约清单 + CR-03。
3. **凭证面**：`~/.lansenger/sdk_state.json` 是真实用户凭证落盘处（app_secret/userToken/encoding_key）；README 声明 0600 但 CLI 代码未见实现。Agent 严禁读取/回显其值。→ 凭证治理四件套。
4. **CI 门禁缺口**：远端只跑 pytest；lint 凭自觉、凭证扫描不存在、构建不验证。→ 人工待办 P1。
5. **单文件体量**：videoconference.py 484 行 / message.py 483 行 / utils.py 388 行——尚可维护，但新增域继续膨胀将逼近巨型文件红线。→ 演进项（拆分属 ⚠️ 级）。

## ⑥ 推荐门禁清单（成本标尺 S≤2h / M≤2d / L>2d）

| 优先级 | 门禁 | 成本 | 状态 |
|---|---|---|---|
| P0 | verify 统一入口（lint+test+build+secrets 四态） | S | ✅ 已建 |
| P0 | 凭证扫描 + 棘轮基线 | S | ✅ 已建 |
| P0 | AGENTS.md + 边界表 + 架构文档 | S | ✅ 已建 |
| P1 | ci.yml 增加 ruff + secrets 扫描（对齐 verify） | S | ⚠️ 人工待办 |
| P1 | pre-commit 挂 verify（scripts/hooks/ 已落盘，激活命令一条） | S | ⚠️ 人工激活 |
| P2 | mypy/pyright 渐进接入（先 utils.py + 高危门） | M | 演进 |
| P2 | 补齐 9 个无测试命令域的最小回归 | M | 演进 |
| P3 | CI 增加 3.13 之外的下限版本冒烟 + uv build 产物校验 | M | 演进 |

## 盘点附注

- 凭证专项按纪律只做元数据级探测：仓库内扫描零命中（键名集见 harness/verify-allowlist 头部）；仓库外敏感面（`~/.lansenger/`、GH Secrets、本地 shell 环境变量）只登记存在性，详见 harness/report-credentials.md。
- git 分支策略：单主干 main + tag 发布（`v*`）；无长期分支约定。
- 工作区状态：开工前 `git status` 干净（仅本次新增 Harness 产物）。
