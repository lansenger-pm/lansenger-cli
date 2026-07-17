# 代码质量规范

## 当前测试覆盖

| 仓库 | 测试文件数 | 测试数 |
|---|---|---|
| Go SDK | 24 | ~200 |
| Python SDK | 25 | ~250 |
| Python CLI | 4 | 9 |
| TS SDK | 19 | ~180 |
| TS CLI | 3 | 38 |

## 质量漏洞

1. **无 CI/CD** — 测试只在本地运行
2. **CLI 测试覆盖不足** — 已改善（Python CLI 4→9 tests, TS CLI 3→38 tests）
3. **发版后未验证** — 发布后没有运行 smoke test

## 每次发版前必须执行

```bash
# 1. 全量测试
cd lansenger-sdk-go       && go test ./... -count=1           # Go SDK
cd lansenger-sdk-python   && uv run pytest -q                # Python SDK
cd lansenger-cli          && uv run pytest -q                # Python CLI
cd lansenger-sdk-ts       && npx jest --passWithNoTests      # TS SDK
cd lansenger-cli-ts       && npx jest --passWithNoTests      # TS CLI

# 2. 构建验证
cd lansenger-sdk-ts       && npm run build                   # TS SDK
cd lansenger-cli-ts       && npm run build                   # TS CLI
cd lansenger-sdk-go       && go build ./...                  # Go SDK + CLI
cd lansenger-sdk-python   && uv build                        # Python SDK
cd lansenger-cli          && uv build                        # Python CLI

# 3. Lint 检查
cd lansenger-sdk-python   && uv run ruff check src/          # Python SDK
cd lansenger-cli          && uv run ruff check src/          # Python CLI
cd lansenger-sdk-go       && golangci-lint run               # Go SDK
cd lansenger-sdk-ts       && npx tsc --noEmit                # TS SDK type-check
cd lansenger-cli-ts       && npx tsc --noEmit                # TS CLI type-check
```

## 推荐改进（按优先级）

1. **GitHub Actions CI** — 每次 push 自动跑测试
2. **mypy / tsc --noEmit / go vet** — 静态类型检查
3. **smoke test** — 发版后运行 `lansenger health check` 验证基础连接
4. **CLI 命令级测试** — 为 `config show`、`message send-text` 等核心命令加测试
