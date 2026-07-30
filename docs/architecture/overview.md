# 系统架构

## 总体结构

```mermaid
flowchart LR
    Web["Vue Web"] -->|"HTTPS / JSON / 文件上传"| API["FastAPI API"]
    Android["Android 原生端"] -->|"HTTPS / JSON / 文件上传"| API
    API --> PG[("PostgreSQL")]
    API --> Redis[("Redis")]
    Redis --> Worker["Celery Worker"]
    Scheduler["Celery Beat 调度器"] --> Redis
    Worker --> Engine["文档、提取与表格引擎"]
    Worker --> PG
    Worker --> Files[("任务文件卷")]
    Worker --> Webhook["签名 Webhook"]
    Engine --> LLM["模型供应商"]
    API --> Knowledge["混合检索与知识图谱"]
    Knowledge --> PG
```

Web 与 Android 是同一业务平台的两个客户端，共用认证、任务、文档工作台和企业平台接口。客户端只负责交互、展示与本地会话状态，业务事实以服务端数据为准。

## 组件职责边界

| 组件 | 职责范围 | 非职责范围 |
| --- | --- | --- |
| Web / Android | 输入校验、交互状态、文件选择、任务展示与下载 | 直接访问数据库，或在客户端保存服务端密钥 |
| FastAPI API | 鉴权、所有权隔离、参数与文件校验、任务创建和查询 | 在 HTTP 请求中同步执行耗时 AI 任务 |
| Celery Worker | 文档处理、模型调用、表格计算、质量校验和结果持久化 | 接受未经 API 校验的外部请求 |
| Scheduler | 扫描到期计划并投递任务 | 执行业务处理或维护第二套调度状态 |
| PostgreSQL | 用户、组织、任务、审计和业务元数据 | 保存 Redis 队列状态 |
| Redis | Celery 队列与任务结果后端 | 作为长期业务事实来源 |
| 任务文件卷 | 保存上传文件和生成交付物 | 替代数据库中的权限和生命周期记录 |
| 模型供应商 | 按受控提示完成推理 | 决定权限、任务状态或最终确定性校验结果 |

## 请求与任务生命周期

1. 客户端提交认证信息、任务参数和文件；
2. API 完成鉴权、用户或组织隔离、文件安全校验与参数校验；
3. API 写入任务记录并将异步任务投递至 Redis；
4. Worker 执行真实处理节点，并写入进度、时间线、证据、质量结果和错误；
5. 客户端轮询或刷新任务状态，并在成功后下载交付物；
6. 需要外部集成时，Worker 按配置投递带签名的 Webhook。

耗时 AI 操作不占用 HTTP 请求生命周期。任务状态按 `queued → running → succeeded/failed/cancelled` 变化，进度只在真实节点状态变化时更新，不按等待时间模拟。

## 后端分层

```text
docnexus/
|-- api/                     # HTTP 路由、鉴权与请求依赖
|-- ai/                      # 文档、提取、表格、RAG 与图谱能力
|-- core/                    # 配置、安全、限流和可观测性
|-- db/                      # SQLAlchemy 模型和会话
|-- repositories/            # 带所有权隔离的数据访问
|-- schemas/                 # HTTP 传输契约
|-- services/                # 文件解析、质量、调度、企业与回调服务
|-- worker/                  # Celery 任务执行器
`-- main.py                  # ASGI 应用入口
```

数据库结构由 `backend/alembic` 中的迁移脚本统一管理。下载、查询、取消、重试和删除操作均须重新校验资源所有权，不得仅依据客户端传入的资源 ID 授权。

## 客户端分层

- Web：路由页面调用 Pinia Store 或 API 模块，HTTP 客户端统一处理令牌和错误；
- Android：Composable 只表达 UI 和用户事件，ViewModel 管理状态，Repository 负责远程数据访问；
- 两端应对齐业务能力和视觉语言，但遵循各平台的导航、权限、文件选择和生命周期规范。

## 网络环境

- Web 开发服务器通过 Vite 代理访问 API；
- Android 模拟器使用 `10.0.2.2` 访问宿主机；
- Android 真机本地调试可使用 `adb reverse`，仅限开发连接；
- 生产 Web 与 Android 必须使用受信任证书的 HTTPS API，不应依赖局域网地址或 ADB 隧道。

## 可靠性与可观测性

Worker 使用软硬超时、延迟确认和有限重试；容器异常退出后，未确认消息可重新投递。健康检查区分存活与就绪状态，Prometheus 指标通过 `/metrics` 暴露。日志、任务时间线与 Webhook 投递记录共同用于故障定位。
