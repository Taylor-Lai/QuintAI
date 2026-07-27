# 贡献指南

## 开始之前

1. 从最新目标分支创建职责单一的开发分支；
2. 按[开发环境配置](docs/development/setup.md)安装所需端的依赖；
3. 阅读[仓库工程规范](docs/development/conventions.md)，确认代码应放置的层级；
4. 不要把无关格式化、生成文件或个人配置混入同一变更。

## 实现要求

- 后端公开接口变更应同步更新契约测试、Web 与 Android 调用方；
- 数据库结构变更必须提供 Alembic 迁移；
- 新增环境变量必须更新 `.env.example`；
- UI 行为变更应覆盖加载、成功、空数据和失败状态；
- 跨端功能应明确 Web 与 Android 的能力差异，不得只凭页面外观宣称完全对标；
- 涉及配置、架构、部署或操作流程时，同步更新相应文档。

## 提交前检查

后端：

```powershell
pytest -m "not api_acceptance"
ruff check backend scripts
mypy
```

Web：

```powershell
Set-Location frontend
npm run lint
npm run build
```

Android：

```powershell
Set-Location android-app
./gradlew.bat :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
```

只改动单一模块时可以先运行最小相关检查；合并前应完成受影响端的完整检查，并记录任何无法运行的项目及原因。

## 提交与文档

提交信息使用简短祈使语气并建议包含范围，例如 `api: validate task ownership`、`web: improve review state` 或 `android: add task retry`。

面向用户的名称统一使用“慧文融通”；“QuaintAI”仅用于团队身份。不得提交密钥、`.env`、真实用户数据、数据库、上传文件、构建产物、依赖目录或发布签名。
