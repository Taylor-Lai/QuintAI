# 部署指南

## 启动

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
```

Compose 包含以下服务：

- `app`：FastAPI、编译后的前端和数据库迁移；
- `worker`：独立执行 AI 与文档任务；
- `postgres`：业务数据和任务状态；
- `redis`：任务队列与结果后端。

生产部署前必须替换 `SECRET_KEY` 和 `POSTGRES_PASSWORD`，限制 `CORS_ORIGINS`，
并通过密钥管理系统注入模型凭据。不得提交 `.env`。

## 健康检查

- `GET /health/live`：进程存活；
- `GET /health/ready`：检查 PostgreSQL 与 Redis；
- `GET /health`：基础服务信息。

容器以非 root 用户运行。PostgreSQL、Redis 和任务文件使用不同的数据卷；删除数据卷
会永久清除相应数据，升级时不要执行 `docker compose down -v`。

## 数据库迁移

API 启动前自动执行 `alembic upgrade head`。手工检查版本：

```powershell
docker compose exec app alembic current
```
