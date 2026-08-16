# 发布就绪检查

本文档只维护当前候选版本的发布门禁和结论。历史验证记录归档在 [`docs/releases`](releases/)，逐次测试事实记录在[持续测试日志](testing/test-log.md)。

## 当前结论

评估日期：2026-08-17

| 发布范围 | 状态 | 说明 |
| --- | --- | --- |
| Web 与后端确定性门禁 | 通过 | 后端 208 项、表格评估 3/3、Web 单元 14/14、Playwright 4/4，静态检查与生产构建通过 |
| 三项核心业务模型验收 | 通过 | 当前候选镜像使用 `qwen3.8-max` 完成新增客户材料任务 6/6、严格比较 6/6 |
| Android 调试构建 | 通过 | Android Studio JBR 21 环境下单元测试、Lint 与 Debug APK 干净构建通过 |
| Android 应用商店发布 | 不通过 | 尚未用组织发布密钥完成候选 AAB/APK 与实体设备全量业务回归 |
| 生产部署 | 不通过 | 正式域名、HTTPS、CORS、备份恢复、模型配额和告警仍须在目标环境确认 |

因此，当前候选版本的本地确定性回归、Web 生产构建、浏览器流程、Android Debug 构建、Docker 部署和三项核心业务 `qwen3.8-max` 文件验收已经通过。该结论适用于本地交付候选版本，不等同于已经完成 Android 应用商店发布或目标生产环境上线验收。

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
| Python 标准回归 | 208 passed、8 deselected，覆盖率 71.74% | [持续测试日志](testing/test-log.md) |
| 表格引擎确定性评估 | 3/3 | [持续测试日志](testing/test-log.md) |
| Web 静态检查与构建 | lint 无错误；生产构建通过 | [持续测试日志](testing/test-log.md) |
| Web 单元与浏览器测试 | 14/14 单元测试；生产构建产物 4/4 Playwright | [持续测试日志](testing/test-log.md) |
| Web 依赖审计 | 0 vulnerabilities | [持续测试日志](testing/test-log.md) |
| 真实材料 | 既有完整材料基线 15/15；当前候选镜像新增客户材料 `qwen3.8-max` 任务与严格比较 6/6 | [持续测试日志](testing/test-log.md) |
| Android | 单元测试、Lint、Debug APK 构建通过 | [持续测试日志](testing/test-log.md) |

## 发布前仍需完成

1. 使用组织发布密钥验证候选 AAB/APK，并在至少一台实体设备完成核心业务回归；
2. 在目标生产环境确认域名、HTTPS、CORS、数据库备份恢复、模型配额和告警；
3. 上述目标环境门禁完成后，按[测试记录规范](testing/README.md)写入对应发布结论。

## 历史记录

- [2026-07-30 Web 与 Android 验证](releases/2026-07-30-validation.md)
- [2026-08-01 持续测试日志](testing/test-log.md)
