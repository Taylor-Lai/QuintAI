# 部署指南

## 构建容器

```powershell
docker build -f deploy/docker/Dockerfile -t quintai:latest .
```

镜像使用 Node 构建阶段和 Python 运行阶段。最终运行镜像只包含编译后的前端、
一体化后端包和 Python 运行依赖。

## 使用 Compose

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

生产部署前应完成以下配置：

- 设置至少 32 个字符的随机 `SECRET_KEY`；
- 严格限制 `CORS_ORIGINS`；
- 配置模型供应商凭据；
- 使用托管密钥注入，不提交 `.env`。

默认 Compose 服务将 SQLite 数据持久化到 `/app/data`。多实例部署应通过
`DATABASE_URL` 配置托管关系型数据库，不得让多个实例共享 SQLite 文件。

健康检查接口：`GET /health`。
