# 三级行动边界表（docs/action-boundary.md）

> 定位：Harness ⑥权限层 + ④变更层。Agent 在本仓库的授权边界**唯一事实源**；新权限规则必须回登记本表。与 AGENTS.md / 其他文档冲突时以本表为准，本表与 🚫 级机制冲突时取更严者。
> 维护：新增/调整须经人工确认；每季度审计一次从未生效的条目考虑裁剪。

## ✅ 一级：始终执行（无需询问）

- 跑 `bash scripts/verify.sh`、pytest、ruff、uv build
- 读仓库文件与检索（先收窄路径；检索排除构建产物与 `.venv/`）
- git 只读：status / diff / log / show / branch -a / blame
- 任务范围内文件编辑（编辑后 `git diff` 回读核对）
- 运行 `uv run lansenger --help` / `--version` / `config show`（不涉网、不涉凭证值）
- 运行离线命令域：`callback parse-payload/decrypt-payload/verify-signature`（用户提供 payload、本地密钥由用户传入时）、`oauth validate-state / authorize-url`（纯计算）

## ⚠️ 二级：事先询问（默认列出待办，得到明确授权后才做）

- 新增第三方依赖 / 升级 `lansenger-sdk` 版本下限（触发 C6 联动）
- 改公共契约：退出码、全局选项、`confirm_high_risk` 语义、`output_result` 结构（触发 C1–C4 联动）
- 改 `.github/workflows/`（CI/发布流水线）
- 删除文件 / 移动模块 / 拆分大文件（videoconference.py、message.py、utils.py）
- 单任务改动超过 10 个文件（应先拆任务）
- 同一文件与其他会话/他人并发改动（先对齐再动）
- `git add` / `git commit`（走受控流程：verify 全绿 → 用户确认 diff → 原子提交；push 另行确认）
- 用真实凭证执行任何联网命令，包括只读的 `health check`、`staff`/`department`/`chat list` 查询、`media download`
- 修改 README 五语言之外的对外文档口径（如发布说明、公告）

## 🚫 三级：绝对禁止

- git 丢弃类：`git stash`、`git reset --hard`、`git checkout .`、`git clean`、改历史
- 绕过 verify 门禁提交；推未验证改动；删除失败测试来"转绿"
- 提交或输出密钥、token、密码、内网凭证；读取或回显 `~/.lansenger/sdk_state.json` 的值（只允许确认存在性与权限位）
- **用真实凭证对真实环境执行 lansenger 写命令**（message send/revoke、group create/update/dismiss、calendar 写、personal-app create/delete、bot-command create/delete、videoconference 任何操作等）——功能验证一律用 mock 测试
- 把 `encoding_key` / `callback_token` / `app_secret` 写进测试、文档、日志或任何产物
- 修改 `dist/`、`.venv/` 等构建产物
- 单凭一次检索「无匹配」下清零/残留结论（必须双通道复核）
- 同一失败连续重试 3 次仍不改变方法（停下诊断 / 换工具 / 升级人工）

## CLI 子命令白名单（Agent 调用边界，冲突取更严；新 CLI 先入表再用）

| CLI | ✅ 可直接调用 | ⚠️ 需人工授权 | 🚫 禁止 |
|---|---|---|---|
| `git` | status/diff/log/show/branch（只读） | add/commit（verify 全绿 + 展示 diff 后）、push（发布/协作者流程） | stash/reset/checkout/clean 丢弃类、force-push、改 hooksPath（激活 pre-commit 留人工命令） |
| `uv` | run/lock/build/add --dry-run | `uv add` 真实写入（=新增依赖）、`uv lock` 升级 | `uv publish`（PyPI 发布只走 tag 流程） |
| `pytest` / `ruff` | 全部（只读检查与测试） | — | 用 `--deselect`/注释跳过失败用例凑绿 |
| `lansenger`（本仓 CLI） | `--help`、`--version`、`config show`、离线计算类（见 ✅ 级） | 联网只读查询、`health check`（消耗凭证换 token） | 任何写命令对真实环境执行；`config set` 真实凭证；读取/打印 sdk_state.json 值 |
| `pip` | `pip install -e ".[dev]"`（环境搭建） | 安装未在 pyproject 声明的包 | 全局安装 / 改系统 Python |

## 本仓库特有高危项（Bootstrap 阶段 0 探测后登记）

| 高危项 | 说明 | 防线 |
|---|---|---|
| `~/.lansenger/sdk_state.json` | 真实用户凭证落盘（app_secret / userToken / encoding_key / callback_token） | 🚫 禁读值；report-credentials.md 登记；扫描器挡入库 |
| 真实消息面 | message/group/calendar 命令面向真实用户与群组，误发即事故 | exit-10 高危门（产品机制）+ 本表 🚫 mock-only 红线 + CR-03 |
| PyPI 发布 | `uv publish` 或 tag 流程误触发即对外发版 | 发布只走 tag==version 硬校验（release.yml）；Agent 不执行发布命令 |
| 5 README 同步 | 漏改任一语言即用户文档漂移 | C8 契约清单 + CR-05 |
| CI/发布流水线 | release.yml 有真实发布副作用 | 改动列 ⚠️ 级 |

## ④变更约束（内置于本表）

- diff 软上限：单任务 >10 文件先拆（⚠️ 级）
- 重试上限：同一失败连试 3 次必须换方法（🚫 级兜底）
- 受控提交：verify 全绿 → 展示 diff → 用户确认 → 原子提交（⚠️ 级流程）
