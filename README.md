# 智汇文枢 · DocNexus

基于 FastAPI + Vue 的文档智能处理平台，提供三大核心能力：

| 模块 | 接口 | 功能 |
|---|---|---|
| 模块一 | `POST /doc-chat/upload` | 自然语言驱动的 Word 文档格式化 |
| 模块二 | `POST /doc-extract/upload` | 从文档中提取结构化字段信息 |
| 模块三 | `POST /table-fill/upload` | 多智能体跨文档自动填表（xlsx / docx）|

---

## 快速开始

### 环境要求

| 组件 | 版本要求 |
|---|---|
| Python | 3.11+ |
| Node.js | ^20.19.0 或 >=22.12.0 |
| LLM API | OpenAI 兼容接口（模块三必需）|

**LLM 提供商推荐：**
- 阿里云百炼（`qwen-max`）- [申请地址](https://dashscope.console.aliyun.com)（免费额度）
- 智谱 GLM-4
- OpenAI

---

## 启动步骤

### 1. 安装后端依赖

```bash
# 进入项目根目录
cd /path/to/your/project

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 AI 核心模块
cd ai_core && pip install -e . && cd ..
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# LLM 提供商选择：openai 或 zhipu
LLM_PROVIDER=openai

# 模块一、二（使用智谱时填写）
ZHIPU_API_KEY=your_zhipu_api_key

# 模块三 AI 核心（填写任意 OpenAI 兼容接口）
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-max

# JWT 密钥（随意填写一个字符串）
SECRET_KEY=any_random_string
```

> **注意：** 模块三的规则提取能力**不调用 LLM**，无需 API Key 即可验证基础填表效果。只有 LLM Skill 增强路径才需要有效 API Key。

### 3. 启动后端服务

打开 **终端窗口 1**：

```bash
# 进入项目根目录
cd /path/to/your/project

# 启动 FastAPI 服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

后端启动成功后：
- API 文档：`http://localhost:8000/docs`
- 后端服务：`http://localhost:8000`

### 4. 安装前端依赖

打开 **终端窗口 2**：

```bash
# 进入前端目录
cd /path/to/your/project/FE

# 安装 Node.js 依赖
npm install
```

### 5. 启动前端开发服务器

在 **终端窗口 2** 中继续：

```bash
# 启动 Vue 开发服务器
npm run dev
```

前端启动成功后访问：`http://localhost:5173`

---

## 项目结构

```
智汇文枢/
├── main.py                  # FastAPI 路由入口
├── database.py              # 数据库模型与初始化
├── requirements.txt         # Python 依赖
├── .env                     # 环境变量（需自行创建）
├── Dockerfile
├── services/                # 业务服务层
│   ├── auth.py              # 认证服务
│   ├── db_service.py        # 数据库服务
│   └── table_filler.py      # 填表服务
├── ai_core/                 # 模块三 AI 核心
│   ├── engine/              # FastAPI 接入层
│   └── src/any2table/       # Any2table 多智能体流水线
└── FE/                      # 前端 Vue 项目
    ├── src/
    │   ├── views/           # 页面视图
    │   ├── components/      # 组件
    │   ├── api/             # API 请求
    │   └── router/          # 路由配置
    ├── package.json
    └── vite.config.js
```

---

## 核心功能测试

### 模块一：智能操作文档（自然语言）

**接口：** `POST /doc-chat/upload`

| 参数 | 类型 | 说明 |
|---|---|---|
| `command` | string | 自然语言格式指令 |
| `document` | file | 上传 `.docx` 文件 |

**指令示例：**
- "把第一段文字加粗并设置为红色"
- "将所有标题字号改为16号"
- "把第二段文字居中对齐"

### 模块二：信息提取

**接口：** `POST /doc-extract/upload`

| 参数 | 类型 | 说明 |
|---|---|---|
| `file` | file | 文档文件（docx / txt） |
| `target_entities` | string | 要提取的字段，逗号分隔 |

### 模块三：多智能体填表（核心功能）

**接口：** `POST /table-fill/upload`

| 参数 | 类型 | 说明 |
|---|---|---|
| `template` | file | 模板文件（xlsx / docx） |
| `documents` | file | 源文档（可多个） |
| `user_request` | string | 用户要求（可选） |

---

## Docker 部署（可选）

```bash
# 构建镜像
docker build -t docnexus .

# 运行容器
docker run -p 8000:8000 --env-file .env docnexus
```

---

## CLI 本地测试（无需启动服务）

```bash
cd ai_core

# 场景 A：COVID-19 数据集
python -m any2table.cli run \
  --path "../测试集/测试集/包含模板文件/COVID-19数据集"

# 场景 B：山东环境监测
python -m any2table.cli run \
  --path "../测试集/测试集/包含模板文件/2025山东省环境空气质量监测数据信息"

# 场景 C：城市经济百强
python -m any2table.cli run \
  --path "../测试集/测试集/包含模板文件/2025年中国城市经济百强全景报告"
```

---

## 技术栈

| 分类 | 技术 |
|---|---|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | SQLite + SQLAlchemy |
| 认证 | JWT (python-jose) |
| AI 核心 | Any2table 多智能体流水线 |
| LLM 集成 | LangChain + LangGraph |
| 前端框架 | Vue 3 + Vite |
| 状态管理 | Pinia |
| 图表库 | ECharts |

---

## 常见问题

### 1. 端口被占用怎么办？

**后端端口冲突：**
```bash
# 使用其他端口启动后端
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

**前端端口冲突：**
```bash
# 使用其他端口启动前端
npm run dev -- --port 5174
```

### 2. 前端无法连接后端？

确保后端服务已启动，并检查 `FE/src/api/request.js` 中的 API 地址配置是否正确。

### 3. LLM API Key 无效？

请检查 `.env` 文件中的 API Key 是否正确，确保网络能够访问对应的 LLM 服务。

---

## 许可证

MIT License