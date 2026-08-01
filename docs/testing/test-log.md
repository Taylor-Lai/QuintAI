# 持续测试日志

本文件按时间记录测试事实。状态只使用“通过”“不通过”“受阻”；代码修改说明和技术债记录在[维护记录](../development/maintenance-log.md)，当前发布判断见[发布就绪检查](../release-readiness.md)。

## 当前有效基线

| 范围 | 最近有效结果 | 状态 |
| --- | --- | --- |
| Python 非真实模型回归 | 189 passed、8 deselected；覆盖率 66.01% | 通过 |
| 表格引擎确定性评估 | 3/3 | 通过 |
| Web lint / unit / build / audit / E2E | 0 errors；9/9；通过；0 vulnerabilities；4/4 | 通过 |
| 15 套真实材料 Web 验收 | 信息提取 5/5、文档编辑 5/5、表格填充 5/5 | 通过 |
| Android 本轮回归 | 未执行，缺少 Java / `JAVA_HOME` | 受阻 |
| DOCX 页面级渲染 | 未执行，缺少 LibreOffice/soffice；结构与格式快照已通过 | 受阻 |

真实模型 Web 结论来自 `qwen3.7-max-preview` 最终运行；此后未重新消耗模型 Token。确定性代码回归是更新后的当前结果，不能替代新的真实模型全量验收。

## WT-20260801-01：真实材料初始基线

- 源码状态：业务完整性重构前；
- 环境：Windows、Docker Compose、PostgreSQL、Redis、Celery、真实 OpenAI-compatible 模型；
- 自动化：后端 161 passed、8 deselected；Web 5 tests passed；
- 真实模型 API：6 passed、2 failed；
- 15 套材料：10 个任务完成、5 个失败，严格比较 0/15；
- Android：缺少 Java / `JAVA_HOME`，受阻；
- 原始运行：本地 `reports/manual_acceptance_20260801/`、`reports/api_acceptance_20260801.stdout.log`；
- 结论：不通过。主要失败为表格空值和公式缺失、文档动作未生效、提取归一化及字段协议不一致。

## WT-20260801-02：业务完整性重构后的 API 验收

- 源码状态：重构工作区；
- 模型：`qwen3.7-max-2026-05-17`，OpenAI-compatible DashScope 接口；
- 首轮真实模型验收：6 passed、2 failed；失败为 AQI Top3 顺序和多源 COVID 中国记录；
- 修复后真实模型全量验收：8 passed，命令为 `python -m pytest backend/tests/acceptance -q`；
- 确定性回归：174 passed、8 deselected；Ruff、Web lint、5 项 Web 单元测试和 Vite 构建通过；
- Android：按 `scripts/test.ps1 -SkipAndroid` 未执行；
- 结论：API 真实模型验收和当时可执行的标准回归通过，Android 受阻。

## WT-20260801-03：15 套材料 Web 网关迭代

- 运行方式：源材料经本机 Web 网关提交；期望文件只用于下载后的严格比较，不作为模型输入；
- `qwen3.7-max-2026-05-17` 基线：12 个任务完成、3 个失败，严格比较 0/15；运行 ID `20260801-web-qwen37-full-manual`；
- 切换 `qwen3.7-max-preview` 后：13 个任务完成、2 个失败，严格比较 2/15；运行 ID `20260801-web-qwen37-preview-manual`；
- 定向复验：报名名单通过，产品简报仍失败；运行 ID `20260801-web-preview-targeted1-manual`；
- 当时标准回归：后端 177 passed、8 deselected；Web lint、5 项单元测试和生产构建通过；
- 结论：不通过。该阶段记录只用于追踪修复过程，不是当前有效业务基线。

## WT-20260801-04：15 套材料最终交付验收

- 源码基线：最终业务修复后来提交于 `43297aa`，CI 修复为 `24dcaed`；
- 模型：`qwen3.7-max-preview`；
- 主运行：15 个任务成功、严格比较 15/15；运行 ID `20260801-web-preview-final1-manual`；
- 严格口径复验：信息提取额外字段也判失败，最终 5/5 且无额外字段；运行 ID `20260801-web-extraction-strict-final-manual`；
- 表格复验：5/5；运行 ID `20260801-web-tables-final-manual`；
- 单项质量复验：报名名单与经营驾驶舱首次执行成功、严格通过、质量 `pass`、证据覆盖率 100%；
- 故障复盘字段契约复验：1/1；
- 当时标准回归：后端 186 passed、8 deselected；Web lint、5 项单元测试和生产构建通过；
- 环境边界：Android 与 DOCX 页面级渲染受阻；
- 证据：见[最终验收摘要](final-acceptance-summary.md)和[测试材料问题](fixture-issues.md)；
- 结论：Web 核心业务和当时可执行的标准回归通过；不代表 Android 或生产部署门禁通过。

## WT-20260801-05：冗余与命名重构回归

- 源码状态：本记录所在提交；未重新调用真实模型；
- Python：Ruff、Mypy、compileall 通过；189 passed、8 deselected；覆盖率 66.01%；
- 表格引擎确定性评估：3/3；
- Web：lint 0 warnings/0 errors；3 files / 9 tests passed；生产构建通过；`npm audit` 为 0 vulnerabilities；Playwright 4/4；
- 真实材料覆盖：受影响的 5 套 DOCX 夹具已在后端逐段落、格式和表格快照回归中通过；未重新运行 15 套真实模型 Web 验收；
- Android：按 `-SkipAndroid` 未执行；
- 结论：本次代码变更涉及的确定性回归通过；真实模型结论仍以 `WT-20260801-04` 为准。
