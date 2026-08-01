# 贡献指南

## 开始之前

1. 从最新目标分支创建职责单一的开发分支；
2. 按[开发环境配置](docs/development/setup.md)安装所需端的依赖；
3. 阅读[仓库工程规范](docs/development/conventions.md)，确认代码应放置的层级；
4. 单次变更应保持职责单一，不得包含无关格式化、生成文件或个人配置。

## 实现要求

- 后端公开接口变更应同步更新契约测试、Web 与 Android 调用方；
- 数据库结构变更必须提供 Alembic 迁移；
- 新增环境变量必须更新 `.env.example`；
- UI 行为变更应覆盖加载、成功、空数据和失败状态；
- 跨端功能应明确 Web 与 Android 的能力差异，不得只凭页面外观宣称完全对标；
- 涉及配置、架构、部署或操作流程时，同步更新相应文档。

## 提交前检查

完整项目门禁以统一脚本为准：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./scripts/test.ps1
```

开发过程中可以先执行受影响子系统的快速检查。后端：

```powershell
ruff check backend scripts
mypy
pytest -m "not api_acceptance" --cov=docnexus --cov-fail-under=59
python scripts/evaluate_table_engine.py
```

Web：

```powershell
Set-Location frontend
npm run lint
npm run test:unit
npm run build
npm audit
npm run test:e2e
```

Android：

```powershell
Set-Location android-app
./gradlew.bat :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
```

只有在 Android 工具链明确不可用时才可使用 `scripts/test.ps1 -SkipAndroid`，并必须在[持续测试日志](docs/testing/test-log.md)记录未执行原因。核心 AI 逻辑或发布候选还须按[测试与验收规范](docs/testing/README.md)执行真实材料验收。

## 提交与文档

提交信息使用简短祈使语气并建议包含范围，例如 `api: validate task ownership`、`web: improve review state` 或 `android: add task retry`。

面向用户的名称统一使用“慧文融通”；“QuaintAI”仅用于团队身份。不得提交密钥、`.env`、真实用户数据、数据库、上传文件、构建产物、依赖目录或发布签名。
