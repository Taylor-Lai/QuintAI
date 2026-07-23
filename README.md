# QuintAI（DocNexus）

QuintAI 是一套文档智能处理系统，由 FastAPI 后端、Vue 3 前端和内置 AI
工作流组成，支持文档编辑、信息提取以及多源数据表格填充。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3-42b883.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571.svg)](https://fastapi.tiangolo.com/)

## 核心能力

- 根据自然语言要求编辑 Word 文档内容与格式；
- 从非结构化文档中提取指定字段，并保留证据与历史记录；
- 将多个 DOCX、XLSX、TXT 等来源的数据融合写入目标表格；
- 提供用户认证、任务管理、历史记录和后台管理界面；
- 支持规则、RAG、Agent Skill 与大语言模型协同处理。

## 技术栈

- 后端：FastAPI、SQLAlchemy、Pydantic、LangChain、LangGraph；
- 前端：Vue 3、Pinia、Vue Router、Axios、ECharts、ExcelJS、Vite；
- 文档处理：python-docx、openpyxl、pandas；
- 数据与任务：PostgreSQL、Redis、Celery、Alembic；
- 部署：Docker、Docker Compose。

## 项目结构

```text
.
|-- backend/                 # Python 后端及服务端 AI 能力
|   |-- alembic/             # 数据库版本迁移
|   |-- src/docnexus/        # 可安装的应用包
|   `-- tests/               # 单元、契约和真实接口验收测试
|-- frontend/                # Vue 3 + Vite 前端
|-- deploy/docker/           # 生产容器构建文件
|-- docs/                    # 架构、开发和部署文档
|-- requirements/            # Python 运行与开发依赖
|-- scripts/                 # 可重复执行的 PowerShell 脚本
|-- tests/manual/            # 跨系统人工验收场景及测试资料
|-- compose.yaml
|-- environment.yml          # 本地 Anaconda 环境定义
`-- pyproject.toml           # 仓库级测试和代码检查配置
```

服务端 AI 能力位于 `docnexus.ai`，由后端统一提供接口和任务编排。

## 使用 Anaconda 配置本地环境

```powershell
conda activate wangtiao-engineering
python -m pip install -r requirements/runtime.txt -r requirements/dev.txt
python -m pip install --no-deps -e backend
Copy-Item .env.example .env
```

新环境也可以在仓库根目录执行 `conda env create -f environment.yml` 创建。
调用 AI 接口前，请在 `.env` 中设置高强度 `SECRET_KEY` 并配置模型供应商。

## 启动项目

本地启动前先执行数据库迁移：

```powershell
python -m alembic upgrade head
uvicorn docnexus.main:app --host 127.0.0.1 --port 8000 --reload
```

AI 接口采用异步任务模式。本地联调还需启动 Redis，并在另一个终端启动 Worker：

```powershell
celery -A docnexus.worker.celery_app:celery_app worker --loglevel=INFO
```

启动前端：

```powershell
Set-Location frontend
npm install
npm run dev
```

## 质量检查

```powershell
pytest -m "not api_acceptance" --cov=docnexus.ai.table_engine.execution --cov=docnexus.ai.table_engine.planning --cov=docnexus.ai.table_engine.quality --cov-fail-under=75
ruff check backend scripts
mypy
python scripts/evaluate_table_engine.py
Set-Location frontend
npm run lint
npm run build
npm audit --omit=dev
```

需要真实模型凭据的测试位于 `backend/tests/acceptance`，并带有
`api_acceptance` 标记。人工端到端测试及其输入、模板和预期结果位于
`tests/manual`，每个场景均附有操作说明。

## 容器部署

```powershell
docker compose up --build
```

Compose 会启动 API、Worker、PostgreSQL 和 Redis。API 通过 8000 端口同时提供
编译后的前端和接口；业务数据、队列状态和任务文件分别使用独立数据卷持久化。

更多内容请查看[文档索引](docs/README.md)。

## 开源许可证

本项目采用 [MIT License](LICENSE)。
