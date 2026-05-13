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

# 安装 SDK（可编辑模式，如需调试 SDK 联动）
pip install -e ../lansenger-skills-official

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

## 提交信息格式

使用简洁的英文描述，关注"为什么"而非"是什么"：

- `Add streaming command group`
- `Fix config show crash on empty state`
- `Support comma-separated executor IDs in todo create`