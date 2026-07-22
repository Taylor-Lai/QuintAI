# 仓库工程规范

## 命名规则

- Python 包和模块使用 `snake_case`；
- Python 类使用 `PascalCase`，函数和变量使用 `snake_case`；
- Vue 组件和页面使用 `PascalCase.vue`，路由页面以 `View.vue` 结尾；
- JavaScript 模块使用小写领域名，例如 `auth.js`、`user.js`；
- 测试文件使用 `test_<behavior>.py`，测试函数描述可观察行为；
- 环境变量使用 `UPPER_SNAKE_CASE`，并在 `.env.example` 中记录。

## 文件放置规则

- HTTP 参数解析、状态码和 FastAPI 依赖放在 `api/`；
- 安全基础能力和配置放在 `core/`；
- SQL 查询放在 `repositories/`，会话与模型放在 `db/`；
- 跨领域应用操作放在 `services/`；
- AI 工作流与算法放在 `docnexus.ai`，不得导入 API 路由；
- 运行数据、报告、缓存、环境、依赖目录和构建产物不得提交。

## 变更要求

- 公开 API 变更必须更新路由契约测试或验收测试；
- 新增配置项必须同步更新 `.env.example`；
- 架构、部署或操作方式发生变化时，必须同步更新对应文档。
