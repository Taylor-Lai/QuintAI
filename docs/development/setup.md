# 开发环境配置

## 环境要求

- 本地 Anaconda，支持 Python 3.11；
- Node.js 20.19+ 或 22.12+，以及 npm；
- 仅在验证容器时需要 Docker Desktop。

## Python 环境

```powershell
conda create -n wangtiao-engineering python=3.11 pip -y
conda activate wangtiao-engineering
python -m pip install -r requirements/dev.txt
python -m pip install --no-deps -e backend
```

也可以在仓库根目录执行 `conda env create -f environment.yml`。editable 安装会
使单一 `docnexus` 包可直接导入，并让本地源码修改立即生效。

## 配置

将 `.env.example` 复制为 `.env`。登录功能需要 `SECRET_KEY`；调用 AI 接口时还
需要为所选 `LLM_PROVIDER` 配置凭据。

## 常用命令

`scripts/` 提供可重复执行的 PowerShell 入口。也可以直接运行根 README 中记录
的各项命令。
