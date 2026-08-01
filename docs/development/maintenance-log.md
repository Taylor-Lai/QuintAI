# 维护与技术债记录

本文件记录不属于测试结果的代码维护事实和后续结构工作。测试结果见[持续测试日志](../testing/test-log.md)。

## 2026-08-01：冗余与命名结构复查

已完成：

- 删除文档指令处理中重复维护、运行时重复合并的 Unicode 规则解析器；
- 将中文逗号分段和“第一段/首段”识别并入唯一规则入口；
- 新增 `DocumentAction`、`DocumentOperationPlan` 和领域化工作流名称；旧名称仅作为兼容别名保留；
- 将 `UploadPanel.vue` 中无组件状态依赖的文件大小、Content-Disposition、JSON 和 Blob 解析逻辑移入 `utils/httpResult.js`；
- 审查表格引擎中的 `_field_role`、`_identity_fields` 和 `_number`。这些同名函数处于不同业务阶段且语义不同，没有进行会破坏边界的机械合并。

后续结构债：

| 模块 | 问题 | 建议边界 |
| --- | --- | --- |
| `frontend/src/components/UploadPanel.vue` | 同时承载三种工作台形态 | 按文档操作、信息提取、表格填充拆分子工作台与 composable |
| `backend/src/docnexus/ai/table_engine/agents.py` | 代理职责和模型交互集中 | 按规划、提取、校验和模型适配器拆分 |
| `backend/src/docnexus/api/routes/enterprise.py` | 路由与企业业务编排过度集中 | 将业务规则移入企业领域服务，路由只保留 HTTP 契约 |
| `backend/src/docnexus/ai/document_operations.py` | 解析、规划和执行仍在同一模块 | 按指令解析、动作计划和 DOCX 执行器拆分 |

拆分要求：先补迁移边界的契约测试，再移动职责；不得只按文件行数切割，也不得用兼容壳掩盖未迁移的业务逻辑。

## 2026-08-02：验收用例确定性加固

- 故障复盘的显式事件时间线改为确定性提取，完整命中时不再消耗模型调用；
- 报名名单的中文行内多记录改为模板锚定解析，避免模型或接口波动造成整单失败；
- 报名名单和项目台账新增完整 Agent/Writer 流水线精确工作簿测试；
- 5 个信息提取字段文件统一为英文逗号协议，并由测试锁定格式。
