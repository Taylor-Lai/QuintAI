# 慧文融通文档中心

本文档集覆盖系统设计、开发环境、工程约定、部署运维和质量验收。第一次接触项目时，建议先阅读根目录 [README](../README.md)，再按职责进入对应文档。

## 开发与架构

- [系统架构](architecture/overview.md)：客户端、API、任务队列、数据层和 AI 工作流的关系；
- [开发环境配置](development/setup.md)：后端、Web、Android 与 Docker 的本地配置；
- [仓库工程规范](development/conventions.md)：命名、目录边界、测试和文档要求；
- [后端开发说明](../backend/README.md)；
- [Web 前端说明](../frontend/README.md)；
- [Android 原生端说明](../android-app/README.md)。

## 运维与质量

- [部署与运维](operations/deployment.md)：Compose、健康检查、升级、日志和备份恢复；
- [发布就绪检查](release-readiness.md)：发布门槛、当前验证结果和交付前剩余事项；
- [人工验收测试](../tests/manual/README.md)：Web 与 Android 的跨端业务验收；
- [贡献指南](../CONTRIBUTING.md)；
- [安全策略](../SECURITY.md)；
- [MIT 许可证](../LICENSE)。

## 名称约定

- 产品名称：慧文融通；
- 团队名称：QuaintAI；
- Android 应用 ID：`com.quaintai.huiwenrongtong`；
- 后端内部 Python 包：`docnexus`。

内部包名用于兼容现有代码和数据迁移，不应在面向用户的界面中替代产品名称。
