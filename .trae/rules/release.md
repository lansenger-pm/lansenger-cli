# 发版流程

每次发版必须执行以下所有步骤，不可遗漏。

## 1. 确认变更内容

- [ ] 所有 SDK/CLI 代码变更完成并测试通过
- [ ] 所有文档（README）已同步更新（5 语言一致）
- [ ] 单元测试全部通过

## 2. Bump 版本号

| 包 | 版本文件 |
|---|---|
| Python SDK | `lansenger-sdk-python/pyproject.toml` |
| Python CLI | `lansenger-cli/pyproject.toml` |
| TS SDK | `lansenger-sdk-ts/package.json` |
| TS CLI | `lansenger-cli-ts/package.json` |
| Go SDK | `lansenger-sdk-go/version.go` |
| Skills external | `lansenger-skills-external/` — 无版本号，直接提交 |
| Skills official | `lansenger-skills-official/` — 无版本号，直接提交 |
| Open docs | `lansenger-open-docs/` — 无版本号，直接提交 |

## 3. 写 CHANGELOG

**每个 repo 的 CHANGELOG.md 必须更新**，按 Keep a Changelog 格式：

```markdown
## [版本号] - YYYY-MM-DD

### Added
- 新增功能

### Changed
- 行为变更

### Fixed
- Bug 修复
```

## 4. Commit

每个 repo 独立提交，commit message 包含版本号：

```
git add -A && git commit -m "vX.Y.Z"
```

或带简略说明：

```
git add -A && git commit -m "feat: xxx

vX.Y.Z"
```

## 5. 发布

| 平台 | 命令 |
|---|---|
| PyPI (SDK) | `cd lansenger-sdk-python && uv build && uv publish dist/lansenger_sdk-X.Y.Z-*` |
| PyPI (CLI) | `cd lansenger-cli && uv build && uv publish dist/lansenger_cli-X.Y.Z-*` |
| npm (SDK) | `cd lansenger-sdk-ts && npm publish` |
| npm (CLI) | `cd lansenger-cli-ts && npm publish` |
| Go | 无需发布到中央仓库，commit + tag 即可 |

## 6. 文档类 repo

Skills 和 open-docs 无版本号，修改后直接 commit：

```
git add -A && git commit -m "docs: 变更说明"
```

## 检查清单（每项发布前确认）

- [ ] `pyproject.toml` / `package.json` / `version.go` 版本已 bump
- [ ] `CHANGELOG.md` 已添加新版本条目
- [ ] 所有 5 语言 README 内容一致，无遗留真实 URL
- [ ] 单元测试全部通过
- [ ] `uv build` / `npm run build` / `go build` 成功
- [ ] 发布后验证 PyPI/npm 页面显示正确版本
