# Contributing

欢迎贡献！请遵循以下流程：

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交修改：`git commit -m 'Add your feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 创建 Pull Request

## 开发环境

```bash
# 安装 CLI（可编辑模式）
pip install -e .

# 安装 SDK（可编辑模式，如需调试 SDK 联动；SDK 源码仓为 lansenger-sdk-python，
# PyPI 包名 lansenger-sdk 的元数据 Homepage 错指向 skills 仓，勿按包元数据找源码）
pip install -e ../lansenger-sdk-python

# 安装开发依赖
pip install pytest
```

## 代码风格

- 不添加注释（除非必要说明）
- 函数和类命名遵循现有模式
- 新命令应放在 `commands/` 目录下对应模块中

## 测试

```bash
pytest
```

## AI 辅助开发（Agent Harness）

本仓库已 Harness 化（七层约束栈，2026-10-13 起生效）：

- Agent 入口与红线：[AGENTS.md](AGENTS.md)（平台自动加载）；行动边界：[docs/action-boundary.md](docs/action-boundary.md)
- 提交前统一验证：`bash scripts/verify.sh`（lint + test + build + 凭证扫描，四态输出）；可选激活 pre-commit：`git config core.hooksPath scripts/hooks`
- 踩坑回写 [KNOWLEDGE.md](KNOWLEDGE.md)；约束回归案例见 [evals/README.md](evals/README.md)

## 提交信息格式

使用简洁的英文描述，关注"为什么"而非"是什么"：

- `Add streaming command group`
- `Fix config show crash on empty state`
- `Support comma-separated executor IDs in todo create`