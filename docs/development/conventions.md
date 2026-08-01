# 仓库工程规范

## 产品与命名

- 面向用户的产品名称统一使用“慧文融通”；
- “QuaintAI”仅表示开发团队或组织命名空间；
- 后端 `docnexus` 包名和 Android `com.quaintai.huiwenrongtong` 应用 ID 属于稳定工程标识，修改前必须评估兼容、迁移和发布影响；
- 新增页面、通知、安装名称和文档标题不得继续使用旧产品名称。

## 代码命名

- Python 包、模块、函数和变量使用 `snake_case`，类使用 `PascalCase`；
- Vue 组件和页面使用 `PascalCase.vue`，路由页面以 `View.vue` 结尾；
- JavaScript 模块使用小写领域名，例如 `auth.js`、`tasks.js`；
- Kotlin 类型和 Composable 使用 `PascalCase`，函数与属性使用 `camelCase`，包名全小写；
- Python 测试文件使用 `test_<behavior>.py`，Kotlin 测试类以 `Test` 结尾；
- 环境变量使用 `UPPER_SNAKE_CASE`，并同步记录在 `.env.example`。

## 目录边界

- `backend/src/docnexus/api`：HTTP 路由、鉴权、状态码和请求依赖；
- `backend/src/docnexus/core`：配置、安全、限流与可观测性；
- `backend/src/docnexus/db`：SQLAlchemy 模型和会话；
- `backend/src/docnexus/repositories`：带用户或组织隔离的数据访问；
- `backend/src/docnexus/services`：文件解析、质量校验、调度、企业能力和外部回调；
- `backend/src/docnexus/ai`：AI 工作流、算法与运行时 Skill，不得反向依赖 API 路由；
- `frontend/src/views`、`components`、`stores`、`api`：分别承载页面、组件、状态和 HTTP 客户端；
- `android-app`：UI 通过 ViewModel 调用 Repository；Composable 不得直接实现网络访问或持久化逻辑。

## 变更要求

- 公开 API 变更必须更新契约测试、Web 与 Android 调用方；
- 新增配置项必须同步更新 `.env.example` 和相关文档；
- 数据库结构变更必须提供 Alembic 迁移，不得只修改 ORM 模型；
- 可观察行为应包含自动化测试；无法自动化的跨端场景应更新 `tests/manual`；
- 架构、部署、构建或操作方式变化时，必须同步更新对应 README；
- 不得提交密钥、真实用户数据、上传文件、报告、数据库、虚拟环境、依赖目录或构建产物。

## 文档边界

- 根 `README.md` 只维护产品、仓库和职责入口，不重复各端的完整命令；
- `backend/README.md`、`frontend/README.md` 与 `android-app/README.md` 分别维护对应子系统的开发和检查方法；
- `docs/architecture` 解释稳定的组件关系，`docs/development` 说明开发约定，`docs/operations` 说明部署运行；
- `docs/release-readiness.md` 只记录当前发布门槛和结论，历史快照移入 `docs/releases`；
- `docs/testing/test-log.md` 只记录测试事实，代码维护与技术债写入 `docs/development/maintenance-log.md`；
- `tests/manual` 只保存可复现的验收材料和期望结果，不保存真实用户数据或临时截图。

## 提交前检查

开发过程中可优先执行与变更相关的最小检查集；合并前必须完成受影响子系统的完整检查。严禁通过降低安全校验、删除有效测试或静默忽略异常的方式规避质量门禁。
