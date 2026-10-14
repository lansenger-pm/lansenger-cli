# KNOWLEDGE.md（踩坑沉淀）

> 定位：Harness ⑦学习层。分节：构建 / 测试 / 工具坑。约定：任务收尾回顾，坑回写本文件；**同一问题反复出现 3 次必须机制化**（脚本/门禁/hook）。
> 条目格式：`- [日期] 现象 → 根因 → 处置（机制化则标注 ✅机制）`。

## 构建

- [2026-10-13] `uv run pytest` 报 `Failed to spawn: pytest` → uv 默认不装 `[project.optional-dependencies]`，本仓 pytest 在 `dev` extra；`[dependency-groups] dev` 只有 ruff → 统一用 `uv run --extra dev pytest`（verify.sh 已固化 ✅机制）。
- [2026-10-13] `uv build` 产物落 `dist/`，已 gitignore；勿手改产物（边界表 🚫）。

## 测试

- [2026-10-13] utils.py 使用模块级全局状态（`_json_output`/`_active_profile`/token 等），测试间会互相污染 → tests/ 以 **autouse fixture 统一重置**；新增全局状态必须同步加入该 fixture，否则出现「单跑过、全跑挂」类问题。
- [2026-10-13] 测试不打真实 API：统一 `patch("lansenger_cli.commands.<域>.get_client")` 返回 MagicMock；断言 `exit_code` 与 mock 调用次数。新增命令域照抄该模式（test_high_risk_gate.py 是高危门范例）。
- [2026-10-13] 高危门断言重点：无 `--yes` 时 **`get_client` 不得被调用**（`gc.assert_not_called()`）+ `exit_code == 10`——两断言缺一不可，只断 exit code 挡不住"确认前已打 API"的实现。

## 工具坑

- [2026-10-14] **README 同步点每份文件有三处，不止两处**：命令总览表 / 对应示例章节 / 「身份能力矩阵」逐命令行（`## Identity & Permissions`）→ 只改前两处会漏矩阵行（本轮 5 份一次性核查才发现）。处置：同步后按 `grep -c '<新子命令>' README*.md` 五份计数一致（预期 ≥3）再提交；`README.fr.md` 常被批量编辑漏掉，逐份点名。
- [2026-10-14] **任务书给的 SDK 新方法签名是摘要，不是全签名**：按摘要写 CLI 会漏参——`reply_message` 实为 `(msg_id, *, emoji_id, reply_type, user_token)`、`send_authorization_request` 实为 `(*, chat_ids, department_ids, account_id, entry_id, authorization_type, user_token)` → 处置：实现前回读 SDK 源码（`lansenger-sdk-python/src/lansenger_sdk/sync_client.py`）逐字对齐关键字；mock 测试对错误关键字是瞎的（MagicMock 照收），只有回读源码能挡。
- [2026-10-13] 历史 `.gitignore` 把 `AGENTS.md`、`docs/` 整体忽略，而 release.yml 的报错信息引用 AGENTS.md（当时并不存在）→ Harness 化时已从 .gitignore 移除（✅机制：约束产物必须入库；AGENTS.md 由平台自动加载）。
- [2026-10-13] pyproject ruff ignore B008 是为 typer 惯用法（`typer.Option(...)` 作默认值）放行，不是失误；改 lint 配置前先查这条历史。
- [2026-10-13] release.yml 对 `git tag v*` 与 pyproject version 做硬校验，报错信息示例：`Version mismatch — tag=… pyproject=…` → 发版必须同 PR 改齐 version+CHANGELOG，tag 合并后打。
- [2026-10-13] CI（ci.yml）只在 push main / PR 时跑 pytest 矩阵，**不含 ruff 与凭证扫描** → 本地必须以 `bash scripts/verify.sh` 为准（把 CI 补齐列为人工待办 P1，见 harness/report.md）。
- [2026-10-13] **找 SDK 源码仓勿信 PyPI 元数据**：`lansenger-sdk` 包的 Project-URL 错指向 `lansenger-skills-official`（实为 AI Agent Skills 文档仓，无 Python 包），真源码仓是 `lansenger-sdk-python`（org 下 9 仓之一）。已实证并修正 CONTRIBUTING；SDK 1.12.0 发版时应顺带修正包元数据。
- [2026-10-13] 扫描器误报类：变量名含 token 且赋值源为运行时调用（`token_data = store.load_user_token(...)`）→ scan_secrets.py 已用「纯小写标识符值过滤」机制化（✅机制）；新误报先修扫描器规则，再考虑入 allowlist 误报段。
- [2026-10-13] 全局选项状态坑：tests 里 `set_json_output(True)` 会被 app callback 每次调用重置——JSON 断言必须通过 CLI 参数 `--json` 传入（新测试 test_cli_oauth_device.py 模式）。
- [2026-10-13] **安全门机制化（提交前校验条件）**：scan_secrets 升级三类检测器——internal-endpoint（内部测试环境主机族）/ long-hex-value（≥32 位 hex）/ blocklisted-value（本地黑名单 harness/security-blocklist.local，gitignored+0600，绝不入库）。探针负向自检：注入内部端点+黑名单值 → FAIL 拦截 ✅。教训：检测器上线首跑即在 SDK 存量测试数据上抓到 11 处 long-hex（callbacks 密文向量/persistence 夹具）——**新检测器上线必须先全量试跑再定基线**，legit 形态走存量入册而非放宽规则。
- [2026-10-13] **门禁负向自检抓到真缺陷**：注入 `API_SECRET = "…"` 探针首跑竟 PASS。双根因：① 正则缺 `re.IGNORECASE`（大写键名全漏）；② `\b` 词边界在 `_S` 处断不开（snake_case 前缀键全漏）→ 已改 lookbehind + IGNORECASE 机制化（✅机制）。教训：**扫描器/门禁必须做探针自检**，绿≠能拦。
- [2026-10-13] verify.sh fail() 的第二个参数是日志文件名，传长文案会生成垃圾文件名——fail 只收短名，原因单独 echo（✅机制：本轮已修；SDK 仓同款在首跑即踩，两仓同步修）。
- [2026-10-13] **钉 `lansenger-sdk>=1.12.0` 后 verify 必红直到 SDK 发布**：`uv run --frozen` 只是不更新锁，但每次仍向 PyPI 重新解析依赖（--frozen ≠ 离线），PyPI 只有 ≤1.11.0 时 lint/test 两步解析直接失败。发布顺序：SDK 仓 tag v1.12.0 → release.yml 发 PyPI → CLI verify/CI 才能绿。过渡期验证方案：`uv pip install --python .venv/bin/python ../lansenger-sdk-python` 后直跑 `.venv/bin/python -m pytest`（2026-10-13 已实证 62 例全绿 + ruff 干净）。
- [2026-10-13] **venv 内 SDK 快照漂移**：`uv pip install ../lansenger-sdk-python` 是普通副本（非 editable），SDK 源码后续修复（如 P0 passport_url 透传）**不会自动生效**——E2E 运行时才暴露（`LansengerConfigError: passport_url is required`，尽管单测全绿）。处置：E2E 前 `uv pip install --reinstall` 重装；教训：**单测 mock 了 get_client、评审看的是源码，只有运行时能抓安装副本漂移**——真实环境 E2E 是必要层（✅机制：evaluation.md §11.5 已固化 E2E 记录）。

- [2026-10-14] **rich 15 把模块级 `rich.print` 收窄成内建 `print` 签名**：`from rich import print as rprint; rprint(x, style="...")` 在 rich 13/14 可用，依赖解析到 15.0.0 后直接 `TypeError: print() got an unexpected keyword argument 'style'`（`soft_wrap`/`highlight` 同理）→ 需要样式的输出一律走 `Console.print`（本仓 `utils.console`，或域模块内的 `console = Console()`）。教训：依赖写 `rich>=13` 时不要依赖「模块级 print 的高级参数」——CI 与本地都装最新版，只有测试能提前抓到。
- [2026-10-14] **golden 哈希会被自家安全门拦下**：测试里存 `sha256(...).hexdigest()`（64 位 hex）触发 `long-hex-value` → `verify.sh` FAIL。处置：golden 改存 **base64(sha256)**（`base64.b64encode(hashlib.sha256(raw).digest()).decode()`），逐字节等价比对能力不变，又不落 32+ hex 形态（✅机制：tests/test_cli_qr.py 为范例，后续需要 golden 的用例照此办理；勿把测试向量塞进 allowlist）。

## 事故档案

（暂无；按 incident-response.md 处理过的真实事件在此登记脱敏摘要。）
