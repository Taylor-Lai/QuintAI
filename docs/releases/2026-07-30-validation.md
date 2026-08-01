# 2026-07-30 Web 与 Android 验证归档

> 本记录已被 2026-08-01 的全量真实材料回归更新，不代表当前发布状态。当前结论见[发布就绪检查](../release-readiness.md)。

## Web 验证

环境：Windows、Docker Desktop、PostgreSQL 16、Redis 7、生产模式 FastAPI + Celery、真实浏览器和真实模型。

- 后端 144 项非 API-acceptance 测试通过，覆盖率 60.97%；8 项真实模型压力验收通过；
- Ruff、Python 字节码编译和当时 CI 范围内的 Mypy 检查通过；
- Oxlint、ESLint、Vitest、Vite 构建、Playwright 桌面与移动视口通过，`npm audit` 为 0 个已知漏洞；
- API、Worker、PostgreSQL、Redis 和 Scheduler 正常；注册、登录与路由保护通过；
- 信息提取、Word 编辑和报名表填充各完成一项真实任务；
- 文档库、人工复核、工作流、执行驾驶舱、知识与证据、企业控制台完成数据加载验证；
- 1280×720 与 390×844 响应式页面通过，业务页面控制台未发现错误或警告。

该轮只覆盖三项代表性真实任务，后来被 15 套严格材料验收发现不足，因此不得作为当前业务验收依据。

## Android 验证

环境：Android Studio、AGP 9.3.1、Gradle 9.5、Pixel 8 模拟器、Android 16（API 36），Debug API 通过 ADB reverse 连接本机容器。

- Debug APK、Release APK/AAB、R8、资源压缩和 Lint Vital 构建链路通过；
- 3 项 JVM 测试和 1 项模拟器 Compose 启动与品牌测试通过；
- 注册、登录、会话保存和覆盖安装后的会话恢复通过；
- 演示任务可轮询到完成并展示结构化字段与处理轨迹；
- 主要业务模块完成加载验证；
- Android Lint 为 0 error、8 warning；
- APK 安装到 vivo V2339FA，但受厂商安装拦截影响，完整业务回归改在模拟器执行；
- 当时产物未配置组织发布密钥，不具备应用商店发布条件。

## 当时未完成项

- 组织发布密钥签名和实体设备完整业务回归；
- 正式域名、HTTPS、CORS、备份恢复、模型配额和告警；
- 认证、任务下载、企业管理和工作台写入路径的进一步覆盖。
