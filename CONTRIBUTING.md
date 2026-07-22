# 贡献指南

## 开发流程

1. 从当前主分支创建职责单一的开发分支。
2. 以 editable 模式安装后端，并安装前端依赖。
3. 按照已记录的前后端边界放置代码。
4. 为可观察行为和公开接口补充或更新测试。
5. 运行 Python 测试、Ruff、前端代码检查和生产构建。
6. 涉及配置、架构或操作流程时，同步更新 `.env.example`、相关文档和 ADR。

不得提交密钥、本地数据库、生成报告、虚拟环境、依赖目录或构建产物。

提交信息使用祈使语气，并建议附加范围，例如
`api: split authentication routes` 或 `web: validate multi-source uploads`。
提交类型和范围属于工具约定，因此保留英文。

命名和文件放置规则见[仓库工程规范](docs/development/conventions.md)。
