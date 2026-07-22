# QuintAI（DocNexus）

QuintAI 是一套文档智能处理系统，由 FastAPI 后端、Vue 3 前端和内置 AI
工作流组成，支持文档编辑、信息提取以及多源数据表格填充。

## 项目结构

```text
.
|-- backend/                 # Python 后端及服务端 AI 能力
|   |-- src/docnexus/        # 可安装的应用包
|   `-- tests/               # 单元、契约和真实接口验收测试
|-- frontend/                # Vue 3 + Vite 前端
|-- deploy/docker/           # 生产容器构建文件
|-- docs/                    # 架构、开发、运维和 ADR 文档
|-- requirements/            # Python 运行与开发依赖
|-- scripts/                 # 可重复执行的 PowerShell 脚本
|-- tests/manual/            # 跨系统人工验收场景及测试资料
|-- compose.yaml
|-- environment.yml          # 本地 Anaconda 环境定义
`-- pyproject.toml           # 仓库级测试和代码检查配置
```

仓库包含 `backend` 和 `frontend` 两个部署边界。服务端 AI 代码位于
`docnexus.ai`，作为后端内部能力随后端一起开发、测试和发布，不作为独立包发布。

## 使用 Anaconda 配置本地环境

```powershell
conda activate wangtiao-engineering
python -m pip install -r requirements/dev.txt
python -m pip install --no-deps -e backend
Copy-Item .env.example .env
```

新环境也可以在仓库根目录执行 `conda env create -f environment.yml` 创建。
调用 AI 接口前，请在 `.env` 中设置高强度 `SECRET_KEY` 并配置模型供应商。

## 启动项目

启动后端：

```powershell
uvicorn docnexus.main:app --host 127.0.0.1 --port 8000 --reload
```

启动前端：

```powershell
Set-Location frontend
npm install
npm run dev
```

## 质量检查

```powershell
pytest -m "not api_acceptance"
ruff check backend
Set-Location frontend
npm run lint
npm run build
```

需要真实模型凭据的测试位于 `backend/tests/acceptance`，并带有
`api_acceptance` 标记。人工端到端测试及其输入、模板和预期结果位于
`tests/manual`，每个场景均附有中文说明。

## 容器部署

```powershell
docker compose up --build
```

生产容器通过 8000 端口同时提供编译后的前端和 API。SQLite 数据保存在
`docnexus-data` 数据卷中，报告目录挂载到仓库的 `reports/`。

更多内容请查看[文档索引](docs/README.md)。

## 开源许可证

除另有说明的第三方资料外，本项目源代码采用 [MIT License](LICENSE)。在保留
版权和许可声明的前提下，可以自由使用、复制、修改、合并、发布、分发、再许可
及销售本软件。第三方依赖与人工测试资料的权利边界见 [NOTICE](NOTICE)。
