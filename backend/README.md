# QuintAI 后端

后端是名为 `docnexus-backend` 的单一可安装 Python 发行包，对外提供
`docnexus` 包。它包含 HTTP 应用、持久化层、应用服务和内部 AI 能力。

```text
src/docnexus/
|-- api/                     # FastAPI 路由和请求依赖
|-- ai/                      # 文档智能与表格处理引擎
|-- core/                    # 配置与安全基础能力
|-- db/                      # SQLAlchemy 模型、会话和初始化逻辑
|-- repositories/            # 持久化操作
|-- schemas/                 # HTTP 数据契约
|-- services/                # 应用层编排
`-- main.py                  # ASGI 应用工厂
```

在仓库根目录安装并启动：

```powershell
python -m pip install --no-deps -e backend
uvicorn docnexus.main:app --reload
```

项目保留了可选的 `any2table` 命令行入口，用于直接执行表格处理流水线；其实现
仍是 `docnexus.ai` 的内部模块，不作为独立包发布。

许可证： [MIT License](../LICENSE)。
