# 慧文融通后端

后端发行包名为 `docnexus-backend`，Python 导入包名为 `docnexus`。上述名称作为稳定工程标识予以保留；所有面向最终用户的产品名称统一为“慧文融通”。

## 目录结构

```text
src/docnexus/
|-- api/                     # FastAPI 路由和请求依赖
|-- ai/                      # 文档智能、RAG、知识图谱与表格引擎
|-- core/                    # 配置、安全、限流和可观测性
|-- db/                      # SQLAlchemy 模型、会话与初始化
|-- repositories/            # 带所有权隔离的持久化操作
|-- schemas/                 # HTTP 数据契约
|-- services/                # 文件解析、质量、调度、企业和回调服务
|-- worker/                  # Celery 异步任务
`-- main.py                  # ASGI 应用入口
```

## 本地启动

在仓库根目录执行：

```powershell
python -m pip install -r requirements/runtime.txt -r requirements/dev.txt
python -m pip install --no-deps -e backend
Copy-Item .env.example .env
python -m alembic upgrade head
uvicorn docnexus.main:app --host 127.0.0.1 --port 8000 --reload
```

异步任务处理还需启动 Redis 与 Celery Worker：

```powershell
celery -A docnexus.worker.celery_app:celery_app worker --loglevel=INFO
```

启动后可访问 `/docs` 查看 OpenAPI，使用 `/health/ready` 检查 PostgreSQL 与 Redis。

## 测试与检查

```powershell
pytest -m "not api_acceptance" --cov=docnexus --cov-fail-under=59
ruff check backend
mypy
```

`backend/tests/acceptance` 中的真实模型测试带有 `api_acceptance` 标记，仅允许在已配置模型凭据的受控环境中显式运行；常规 CI 与无凭据环境默认排除该测试集。

## 命令行工具

安装完成后，可通过 `any2table` 命令行入口运行表格处理流水线。CLI 与 HTTP 任务必须复用同一领域实现，以避免业务规则和算法行为产生差异。

更多内容见[开发环境配置](../docs/development/setup.md)和[系统架构](../docs/architecture/overview.md)。
