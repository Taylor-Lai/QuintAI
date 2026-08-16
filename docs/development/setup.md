# 开发环境配置

## 环境要求

- Python 3.11 与 Conda（推荐 Miniconda 或 Anaconda）；
- Node.js 20.19+ 或 22.12+，以及 npm；
- Docker Desktop（运行完整依赖栈或验证容器时需要）；
- Android Studio、Android SDK 和 JDK 17（开发 Android 客户端时需要）；
- Git。

Windows 项目路径建议使用纯 ASCII 字符。Android Gradle Plugin 已允许当前中文路径构建，但部分第三方工具或 JVM 测试运行器仍可能受路径编码影响。

## 环境变量

在仓库根目录创建本地配置：

```powershell
Copy-Item .env.example .env
```

至少须替换 `SECRET_KEY`。启用真实模型服务时，还需配置 `LLM_PROVIDER`、`OPENAI_API_KEY`、`OPENAI_BASE_URL` 与 `OPENAI_MODEL`；项目默认使用阿里云百炼兼容接口上的 `qwen3.8-max`。Docker 服务需要通过宿主机代理访问模型时，使用 `CONTAINER_HTTP_PROXY` / `CONTAINER_HTTPS_PROXY` 并填写容器可访问的地址（Windows Docker Desktop 通常为 `http://host.docker.internal:<port>`），不能填写宿主机 `127.0.0.1`。`.env`、发布签名及任何真实密钥均不得提交至版本库。

## 方式一：Docker Compose

该方式适用于完整服务栈的本地集成验证：

```powershell
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/api/health/ready
```

API、Web、Worker、调度器、PostgreSQL 和 Redis 会一并启动。查看日志：

```powershell
docker compose logs -f app worker scheduler
```

## 方式二：本地后端与 Web

### Python 环境

```powershell
conda env create -f environment.yml
conda activate huiwen-rongtong
python -m pip install --no-deps -e backend
```

如不使用 `environment.yml`，可按以下步骤创建 Python 环境：

```powershell
conda create -n huiwen-rongtong python=3.11 pip -y
conda activate huiwen-rongtong
python -m pip install -r requirements/runtime.txt -r requirements/dev.txt
python -m pip install --no-deps -e backend
```

### 数据库与 API

```powershell
python -m alembic upgrade head
uvicorn docnexus.main:app --host 127.0.0.1 --port 8000 --reload
```

AI 接口采用异步任务模式，因此还需启动 Redis 与 Celery Worker：

```powershell
celery -A docnexus.worker.celery_app:celery_app worker --loglevel=INFO
```

验证定时工作流时，还应启动 Celery Beat，或使用 Compose 中的 `scheduler` 服务。

### Web 前端

```powershell
Set-Location frontend
npm install
npm run dev
```

开发服务器通过 Vite 代理访问本地 API。`VITE_*` 变量会写入浏览器构建产物，因此严禁用于保存生产密钥或其他敏感信息。

## Android 开发

1. 在 Android Studio 中打开仓库下的 `android-app` 目录；
2. 等待 Gradle 同步完成；
3. 启动 API 与所需的 Worker；
4. 选择模拟器或已授权的真机运行 `app`；
5. 按 [Android 开发指南](../../android-app/README.md) 配置调试 API 地址。

## 基础验证

在仓库根目录执行统一检查入口：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./scripts/test.ps1
```

该脚本执行 Python 静态检查、覆盖率回归、表格评估、Web lint、单元测试、生产构建、依赖审计、Playwright，以及 Android 测试、Lint 和 Debug 构建。Android 工具链受阻时可显式使用 `-SkipAndroid`，但必须记录未执行原因。真实模型验收另见[测试与验收](../testing/README.md)。
