# 慧文融通

慧文融通是 QuaintAI 团队开发的文档智能处理平台，面向复杂文档编辑、结构化信息提取和多源表格填充场景。仓库同时包含 Web 端、Android 原生客户端、FastAPI 后端、异步任务系统和可追溯的 AI 工作流。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3-42b883.svg)](https://vuejs.org/)
[![Android](https://img.shields.io/badge/Android-8.0%2B-3ddc84.svg)](android-app/README.md)

## 产品能力

- 使用自然语言编辑 Word 文档的内容、结构与格式；
- 从合同、报告、说明书等非结构化材料中提取字段，并保留证据与历史记录；
- 融合 DOCX、XLSX、TXT 等多个来源，完成模板表格填充、公式计算与异常追溯；
- 以真实任务节点展示进度、执行时间线、质量报告、失败原因和重试状态；
- 提供用户认证、任务中心、文档工作台、人工复核、批量审批和一键演示任务；
- 提供组织、成员、角色、审计日志、评论、通知、工作流版本和定时任务；
- 提供混合检索、知识图谱、API 密钥、签名 Webhook、配额与运行分析；
- Web 与 Android 原生端共用同一套后端接口和业务数据。

## 技术架构

- Web：Vue 3、Pinia、Vue Router、Axios、ECharts、Vite；
- Android：Kotlin、Jetpack Compose、ViewModel、Repository、Retrofit；
- 后端：FastAPI、SQLAlchemy、Pydantic、Alembic；
- AI 工作流：LangChain、LangGraph、规则、RAG 与 Agent Skill；
- 文档处理：python-docx、openpyxl、pandas；
- 数据与任务：PostgreSQL、Redis、Celery；
- 部署与监控：Docker Compose、Prometheus。

## 仓库结构

```text
.
|-- android-app/             # Kotlin + Jetpack Compose 原生客户端
|-- backend/                 # FastAPI、数据层、AI 工作流与 Celery 任务
|-- frontend/                # Vue 3 Web 客户端
|-- deploy/                  # 容器、监控与部署资源
|-- docs/                    # 架构、开发和运维文档
|-- requirements/            # Python 运行与开发依赖
|-- scripts/                 # 质量检查、备份恢复与辅助脚本
|-- tests/manual/            # 人工端到端验收材料
|-- compose.yaml             # 本地及单机部署编排
|-- environment.yml          # Conda 环境定义
`-- pyproject.toml           # 仓库级 Python 工具配置
```

后端发行包名为 `docnexus-backend`，Python 导入包仍为 `docnexus`；它们是内部工程标识，不是产品名称。Android 应用 ID 为 `com.quaintai.huiwenrongtong`，其中 `quaintai` 表示团队命名空间。

## 快速启动

最省事的本地体验方式是 Docker Compose：

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
```

服务就绪后访问：

- Web 与 API：`http://127.0.0.1:8000`
- OpenAPI：`http://127.0.0.1:8000/docs`
- 就绪检查：`http://127.0.0.1:8000/health/ready`

Compose 会启动 API、Worker、调度器、PostgreSQL 和 Redis。首次启动及重新构建可能需要下载镜像和依赖。

## 本地开发

### 后端

```powershell
conda env create -f environment.yml
conda activate huiwen-rongtong
python -m pip install --no-deps -e backend
Copy-Item .env.example .env
python -m alembic upgrade head
uvicorn docnexus.main:app --host 127.0.0.1 --port 8000 --reload
```

异步任务还需要 Redis 和 Worker：

```powershell
celery -A docnexus.worker.celery_app:celery_app worker --loglevel=INFO
```

### Web

```powershell
Set-Location frontend
npm install
npm run dev
```

### Android

使用 Android Studio 打开 `android-app` 目录。模拟器调试包默认访问宿主机 `http://10.0.2.2:8000/`；真机联调、签名和正式构建请参阅 [Android 开发指南](android-app/README.md)。

## 质量检查

```powershell
pytest -m "not api_acceptance" --cov=docnexus --cov-fail-under=59
ruff check backend scripts
mypy
python scripts/evaluate_table_engine.py

Set-Location frontend
npm run lint
npm run build
npm audit --omit=dev

Set-Location ../android-app
./gradlew.bat :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
```

真实模型验收位于 `backend/tests/acceptance`，需要单独配置模型凭据。跨端人工验收材料位于 [tests/manual](tests/manual/README.md)。

## 文档导航

- [文档索引](docs/README.md)
- [系统架构](docs/architecture/overview.md)
- [开发环境配置](docs/development/setup.md)
- [仓库工程规范](docs/development/conventions.md)
- [部署与运维](docs/operations/deployment.md)
- [发布就绪检查](docs/release-readiness.md)
- [贡献指南](CONTRIBUTING.md)
- [安全策略](SECURITY.md)

## 许可证

本项目采用 [MIT License](LICENSE)。
