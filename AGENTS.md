# lansenger-cli Agent 指南（AGENTS.md）

> **项目身份**：蓝信（Lansenger）官方命令行工具——Python 3.10+ / typer + rich，封装 `lansenger-sdk` 同步客户端，发布 PyPI（`lansenger` 命令）。本文件是 Agent 的**索引 + 高频红线**；细则一律按第 10 节索引下沉加载，新增约束先落细则层、本文件只加一行指针（只迁移不删除）。

## 1. 目录地图与模块职责

| 路径 | 职责 |
|---|---|
| `src/lansenger_cli/main.py` | typer app 装配：注册 16 个命令组 + 全局选项（`--json/--profile/--as/--app-token/--user-token/--verbose`） |
| `src/lansenger_cli/utils.py` | 共享层：全局状态 setter、`get_client` 工厂、**退出码契约**、`confirm_high_risk` 高危门、`output_result` 输出契约 |
| `src/lansenger_cli/commands/*.py` | 16 个命令域模块；**域之间零横向依赖**，只允许 `import utils` |
| `tests/` | pytest + typer CliRunner + `MagicMock` mock `get_client`；autouse fixture 重置 utils 全局状态 |
| `docs/` | architecture.md（架构与契约清单）· action-boundary.md（三级行动边界） |
| `harness/` | 盘点 report · 凭证治理 · verify 棘轮基线 · 成熟度自评（verify-logs/ 本地日志不入库） |
| `scripts/` | verify.sh（统一验证入口）· scan_secrets.py（凭证扫描）· hooks/pre-commit（人工激活） |
| `evals/` · `templates/` · `KNOWLEDGE.md` | 约束回归集 · 交付度量模板 · 踩坑沉淀 |

依赖方向：`main → commands → utils → lansenger_sdk`，禁止反向与横向。架构图与跨模块契约同步清单见 [docs/architecture.md](docs/architecture.md)。

## 2. 常用命令（实测三档标注）

| 用途 | 命令 | 状态 |
|---|---|---|
| 统一验证（提交前必跑） | `bash scripts/verify.sh` | ✅ 可用（lint+test+build+secrets 四态） |
| Lint | `uv run ruff check .` | ✅ 可用 |
| 单测 | `uv run --extra dev pytest -q` | ✅ 可用（78 passed；**uv 必须带 `--extra dev`**） |
| 构建 | `uv build` | ✅ 可用 |
| 本地跑 CLI | `uv run lansenger --help` / `uv run lansenger <group> <cmd>` | ✅ 可用（无凭证命令可直接跑） |
| pip 安装 | `pip install -e ".[dev]"` | ⚠️ 受限可用（CI 同款命令；本地未实测） |
| 类型检查 | mypy/pyright | 🚫 未配置（接入=演进项，勿臆造命令） |

## 3. 编码规范要点（从现有代码归纳，不要发明新规范）

- **不加注释**（除非必要说明，见 CONTRIBUTING）；ruff line-length=120，select F/E/W/B。
- 新命令放 `commands/` 对应域模块并在 `main.py` 注册；一个域一个模块，禁止域间 import。
- 全局状态只经 `utils.py` 的 setter（`set_json_output` 等），测试用 autouse fixture 重置——新增全局状态必须同步加入该 fixture。
- 输出统一走 `output_result`/`console`：`--json` 输出原始 JSON，否则 rich 表格；失败 raise `SystemExit(EXIT_ERROR)`。
- **退出码契约（稳定，脚本/Agent 依赖）**：0 成功 / 1 失败 / **10 高危写未确认**。
- **高危写命令必须接 `confirm_high_risk` 门**：无 `--yes` → 结构化确认 + exit 10；`--dry-run` 只验参不执行；并配套 exit-10 测试（模式见 tests/test_high_risk_gate.py）。

## 4. 「不要做」清单

- 🚫 不提交/回显任何凭证：`~/.lansenger/sdk_state.json`、`LANSENGER_*` 环境变量值、token/secret（完整边界见 docs/action-boundary.md）。
- 🚫 不用真实凭证对真实环境执行写命令（message send / group create / calendar 写等）验证功能——用 mock 测试。
- 🚫 不绕过 verify 提交；不删失败测试；同一失败连试 3 次不换方法（停下诊断）。
- ⚠️ 用户可见面变更（命令增删/参数/输出格式/退出码）**必须同步 5 个语言版 README**（README.md / zhHans / zhHant / zhHantHK / fr）的命令总览表与相关章节 + CHANGELOG——历史漏改即文档漂移。
- ⚠️ 升级 `lansenger-sdk` 下限须全量回归 78 例 + CHANGELOG dep 条目；新依赖引入须事先询问。
- 不改 `dist/` 等构建产物；不动 `.github/workflows/` 除非任务明确要求。

## 5. 非目标（本仓库不负责什么）

- 不是 SDK：协议实现、认证细节在 `lansenger-sdk` 仓库，本仓只做 CLI 封装与体验。
- 不做蓝信标准接口之外的**定制应用域**（0.14.0 已移除请假/加班/问卷等 7 个交付定制域——先例：不属于「交付给谁都不变」的标准能力不进本仓）。
- 不做 GUI/Web/服务端；不做多语言运行时切换（文档 5 语言、程序单语言）。

## 6. 行动边界（详见 docs/action-boundary.md）

✅ 始终执行：verify/测试/构建/检索/git 只读/任务范围内编辑（编辑后 diff 回读）
⚠️ 事先询问：新增依赖 · 改公共契约（退出码/全局选项/输出结构）· 删文件 · 单任务 >10 文件 · 改 CI 与发布配置
🚫 绝对禁止：git 丢弃类（stash/reset --hard/checkout .）· 绕过门禁 · 推未验证改动 · 删失败测试 · 凭证值进上下文/日志/提交 · lansenger CLI 对真实环境的写操作 · 读取/回显 sdk_state.json 值
CLI 子命令白名单（git/uv/pytest/ruff/lansenger 本体）按表执行，冲突取更严者。

## 7. 提交纪律

1. **验证先于断言**：提交前 `bash scripts/verify.sh` 全绿（0 FAIL），用新鲜输出说话；其中**安全门为阻断条件**——凭证形态 / 内部端点 / 高熵 hex / 本地黑名单（harness/security-blocklist.local）任一命中即不得提交。
2. **原子提交**：一个独立需求一个提交；风格从 CONTRIBUTING（简洁英文、说 why）+ 历史惯例（`feat!:`/`chore(release):` 等 conventional 前缀可用）。
3. 发版 = tag `v*` == pyproject version（release.yml 硬校验）+ CHANGELOG 条目；破坏性变更用 `feat!:` 并写明迁移路径。

## 8. 踩坑沉淀约定

任务收尾回顾：踩到的坑回写 [KNOWLEDGE.md](KNOWLEDGE.md)（构建/测试/工具坑分节）；**同一问题反复出现 3 次必须机制化**（脚本/门禁/hook），从「文档警告」升级为「做不出来」。约束回归案例进 `evals/`。

## 9. Fabric 项目文档根

PRD / spec / 原型等项目文档统一放 `.project/`（本仓 Harness 产物在根级 docs/ 与 harness/，两套并存互不覆盖）。

## 10. 细则索引（按需加载）

| 任务 | 先读 |
|---|---|
| 理解架构 / 契约改动 | docs/architecture.md（含契约同步清单 8 项） |
| 判断能否执行某操作 | docs/action-boundary.md（三级边界 + CLI 白名单 + 特有高危项） |
| 提交 / 发版 | 本文件 §7 · CONTRIBUTING.md · CHANGELOG.md |
| verify 失败排查 | harness/verify-logs/ 日志 · harness/verify-allowlist（棘轮规则） |
| 追历史坑 | KNOWLEDGE.md · harness/report.md（风险 Top5） |
| 约束回归 | evals/README.md（CR-01…CR-05 + 回放记录） |
| 交付度量 | templates/delivery-report.md |
