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

- `gateway`：提供 Vue Web、统一 `/api/` 入口、反向代理、安全响应头和静态资源缓存；
- `app`：执行数据库迁移并提供仅限容器网络访问的 FastAPI；
- `worker`：执行 AI、文档与表格任务；
- `scheduler`：扫描到期的定时工作流并投递任务；
- `postgres`：保存用户、任务、文档元数据与企业数据；
- `redis`：任务队列与结果后端；
- 生产 API 同时使用 Redis 保存跨实例限流计数；Redis 异常时登录、注册与 AI 上传端点将返回 `503`，不得通过关闭限流绕过故障；
- 容器访问外部模型必须经过代理时，使用 `CONTAINER_HTTP_PROXY` / `CONTAINER_HTTPS_PROXY` 配置容器可达地址，并在 `CONTAINER_NO_PROXY` 中保留 PostgreSQL、Redis、API 与网关服务名；宿主机回环地址不能直接作为容器代理地址；
- `prometheus`：可选监控服务，通过 `monitoring` profile 启动。

## 健康检查

- `GET /nginx-health`：Nginx 网关存活；
- `GET /api/health/live`：API 进程存活；
- `GET /api/health/ready`：PostgreSQL 与 Redis 已就绪；
- `GET /api/health`：基础服务信息；
- `GET /api/metrics`：Prometheus 指标。

```powershell
Invoke-RestMethod http://127.0.0.1:8000/nginx-health
Invoke-RestMethod http://127.0.0.1:8000/api/health/ready
docker compose logs --tail 200 gateway app worker scheduler
```

## HTTPS 网关

默认 Compose 在 `HTTP_PORT`（默认 `8000`）提供 HTTP，适用于本地验收。仅通过公网 IP 做临时 HTTP 测试时，可设置 `SESSION_COOKIE_SECURE=false` 使浏览器接受会话 Cookie；该配置会降低传输安全性，不属于正式生产方案。公网正式部署应准备受信任证书，保持 `SESSION_COOKIE_SECURE` 为空或设为 `true`，并在 `.env` 中配置：

```dotenv
HTTP_PORT=80
NGINX_SERVER_NAME=docs.example.com
NGINX_CLIENT_MAX_BODY_SIZE=30m
TLS_CERT_DIR=/absolute/path/to/certificates
```

证书目录必须包含 `fullchain.pem` 和 `privkey.pem`，随后启动 HTTPS 覆盖配置：

```powershell
docker compose -f compose.yaml -f deploy/nginx/compose.https.yaml up --build -d
```

该配置将 HTTP 重定向至 HTTPS，在 `443` 端口启用 TLS 1.2/1.3、HTTP/2 与 HSTS。若云负载均衡、Kubernetes Ingress 或 CDN 已负责 TLS 终止，可继续使用基础 Compose，并确保 Nginx HTTP 端口只对上游网关开放。

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

企业控制台创建并下载的是当前组织的文档归档，用于业务文件导出，不等同于 PostgreSQL 全量备份。数据库灾难恢复仍须使用本节脚本或基础设施快照，并定期执行恢复演练。

Webhook 仅接受 HTTPS 公网端点，不允许本地、保留或内网字面地址。生产网络还应配置出站防火墙或代理，仅放行经批准的回调目标，以形成独立于应用校验的 SSRF 防护边界。投递队列异常会记录为失败并由调度器恢复，不应通过删除投递记录掩盖故障。

组织套餐不能由组织所有者自行提升。平台管理员通过受管理员鉴权保护的 `PUT /api/enterprise/subscription` 提交目标 `organization_id` 与套餐标识；变更会更新组织配额并写入审计日志。计费或合同系统应在完成授权后调用该接口，不得让客户端直接模拟支付成功。

## 监控

```powershell
docker compose --profile monitoring up -d
```

Prometheus 默认监听 `9090`。生产环境还应配置日志聚合、告警、磁盘容量监控、数据库备份验证和证书到期提醒。

## Android 正式环境

发布包必须通过 `-PapiBaseUrl=https://.../` 写入正式 API 地址，并使用稳定的发布签名。ADB 反向端口、`127.0.0.1`、`10.0.2.2` 和明文 HTTP 只用于调试，不属于生产部署方案。

## Windows 路径提示

如果 Docker BuildKit 或第三方构建工具无法处理包含中文字符的工作区路径，可将仓库复制或映射到纯 ASCII 路径后构建。映射仅用于本地构建，不应写入 Compose、源码或 CI 配置。
