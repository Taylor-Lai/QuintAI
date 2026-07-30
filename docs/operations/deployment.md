# 部署与运维

## 部署前检查

- 使用至少 32 字符的随机 `SECRET_KEY`；
- 设置独立的 `POSTGRES_PASSWORD`，不得沿用示例值；
- 限制 `CORS_ORIGINS`，并通过密钥管理系统注入模型凭据；
- 为域名配置 HTTPS，并确保 Android 与浏览器均信任证书链；
- 规划 PostgreSQL、Redis 和任务文件卷的备份与容量；
- 不得将 `.env`、发布签名、数据库备份或用户文件提交至 Git 仓库。

## Docker Compose 启动

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
```

服务说明：

- `app`：执行数据库迁移，提供 FastAPI、OpenAPI 和编译后的 Web；
- `worker`：执行 AI、文档与表格任务；
- `scheduler`：扫描到期的定时工作流并投递任务；
- `postgres`：保存用户、任务、文档元数据与企业数据；
- `redis`：任务队列与结果后端；
- `prometheus`：可选监控服务，通过 `monitoring` profile 启动。

## 健康检查

- `GET /health/live`：API 进程存活；
- `GET /health/ready`：PostgreSQL 与 Redis 已就绪；
- `GET /health`：基础服务信息；
- `GET /metrics`：Prometheus 指标。

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/ready
docker compose logs --tail 200 app worker scheduler
```

## 数据库迁移与升级

`app` 启动时会执行 `alembic upgrade head`。部署新版本前必须完成数据库备份，随后执行镜像构建与服务启动：

```powershell
./scripts/backup-database.ps1
docker compose build
docker compose up -d
docker compose exec app alembic current
```

升级完成后，应验证服务健康状态、Worker 日志、关键 API 及至少一项完整业务任务。升级期间禁止执行 `docker compose down -v`，该命令会删除持久化数据卷。

## 备份与恢复

```powershell
./scripts/backup-database.ps1
./scripts/restore-database.ps1 -BackupPath ./backups/huiwenrongtong-时间.dump -ConfirmRestore
```

恢复操作会覆盖当前数据库，必须在维护窗口执行，并确保目标环境和备份版本匹配。任务文件卷需要使用独立的文件或快照备份策略。

## 监控

```powershell
docker compose --profile monitoring up -d
```

Prometheus 默认监听 `9090`。生产环境还应配置日志聚合、告警、磁盘容量监控、数据库备份验证和证书到期提醒。

## Android 正式环境

发布包必须通过 `-PapiBaseUrl=https://.../` 写入正式 API 地址，并使用稳定的发布签名。ADB 反向端口、`127.0.0.1`、`10.0.2.2` 和明文 HTTP 只用于调试，不属于生产部署方案。

## Windows 路径提示

如果 Docker BuildKit 或第三方构建工具无法处理包含中文字符的工作区路径，可将仓库复制或映射到纯 ASCII 路径后构建。映射仅用于本地构建，不应写入 Compose、源码或 CI 配置。
