# 发布就绪检查

本文档只维护当前候选版本的发布门禁和结论。历史验证记录归档在 [`docs/releases`](releases/)，逐次测试事实记录在[持续测试日志](testing/test-log.md)。

## 当前结论

评估日期：2026-08-03

| 发布范围 | 状态 | 说明 |
| --- | --- | --- |
| Web 与后端核心业务 | 受阻 | 生产 API 路由缺陷已修复并通过生产产物浏览器测试；最近完整材料基线为 15/15，本轮信息提取仍有 4 项被 Docker 外部 TLS 阻断 |
| Android 调试构建 | 受阻 | 本轮环境缺少 Java / `JAVA_HOME`，未重新执行 Android 测试、Lint 和构建 |
| Android 应用商店发布 | 不通过 | 尚未用组织发布密钥完成候选 AAB/APK 与实体设备全量业务回归 |
| 生产部署 | 不通过 | 正式域名、HTTPS、CORS、备份恢复、模型配额和告警仍须在目标环境确认 |

因此，当前代码回归及用户反馈对应的 Web 用例已通过，但恢复 Docker 到模型供应商的 TLS 链路并重跑信息提取前，不能宣称 Web/后端候选版本完成本轮全量验收；整个产品也尚未满足 Android 商店发布或生产部署条件。

## 统一发布门槛

- 产品名称、应用名称、页面标题和用户文案统一使用“慧文融通”；
- API、Worker、PostgreSQL 和 Redis 健康，数据库迁移可执行，任务文件卷可写；
- 后端单元与集成测试、Ruff、Mypy、覆盖率门槛和表格引擎评测通过；
- Web lint、单元测试、生产构建、依赖审计和真实浏览器核心流程通过；
- Android 单元测试、Lint、Debug 构建和已授权真机核心流程通过；
- 信息提取、Word 编辑、表格填充的真实材料严格验收通过；
- 生产域名、HTTPS、CORS、模型凭据、数据库备份和 Android 发布签名已配置；
- 不包含 `.env`、密钥、签名文件、真实用户数据、上传文件、数据库或构建产物。

## 当前证据

| 门禁 | 最近结果 | 证据 |
| --- | --- | --- |
| Python 标准回归 | 195 passed、8 deselected，覆盖率 71.08% | [持续测试日志](testing/test-log.md) |
| 表格引擎确定性评估 | 3/3 | [持续测试日志](testing/test-log.md) |
| Web 静态检查与构建 | lint 无错误；生产构建通过 | [持续测试日志](testing/test-log.md) |
| Web 单元与浏览器测试 | 9/9 单元测试；生产构建产物 4/4 Playwright | [持续测试日志](testing/test-log.md) |
| Web 依赖审计 | 0 vulnerabilities | [持续测试日志](testing/test-log.md) |
| 15 套真实材料 | 最近完整基线 15/15；本轮表格 5/5、信息提取 1/5（4 项环境受阻） | [持续测试日志](testing/test-log.md) |
| Android | 本轮未执行 | [持续测试日志](testing/test-log.md) |

## 发布前仍需完成

1. 在具备 Java 环境的构建机执行 Android 单元测试、Lint、Debug/Release 构建；
2. 使用组织发布密钥验证候选 AAB/APK，并在至少一台实体设备完成核心业务回归；
3. 在目标生产环境确认域名、HTTPS、CORS、数据库备份恢复、模型配额和告警；
4. 以上门禁全部重新执行后，按[测试记录规范](testing/README.md)写入新的候选版本结论。

## 历史记录

- [2026-07-30 Web 与 Android 验证](releases/2026-07-30-validation.md)
- [2026-08-01 持续测试日志](testing/test-log.md)
