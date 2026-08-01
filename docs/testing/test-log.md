# 持续测试日志

本文件记录稳定结论；原始证据位于本地 `reports/test-runs/`。状态只有“通过”“不通过”“受阻”，不使用含义不清的“基本通过”。

## 2026-08-01：真实材料基线

- 代码状态：业务逻辑重构前；
- 环境：Windows、Docker Compose、PostgreSQL、Redis、Celery、真实 OpenAI-compatible 模型；
- 后端非真实模型测试：161 passed，8 deselected；
- Web 单元测试：5 passed；
- 真实模型 API acceptance：6 passed，2 failed；
- `tests/manual`：15 套中 10 个任务完成、5 个任务失败，严格结果比较 0/15；
- Android：受阻，本机缺少 Java / `JAVA_HOME`；
- 结论：不通过。主要问题为表格空值/公式缺失、文档动作未生效、提取归一化不一致以及字段分隔协议不一致。

原始基线保存在本地 `reports/manual_acceptance_20260801/` 和 `reports/api_acceptance_20260801.stdout.log`。这些文件不提交 Git，避免把账号、任务 ID、绝对路径和大量二进制产物混入源码历史。

## 2026-08-01：业务完整性重构后

- 代码状态：工作区，尚未提交；
- 关键变化：增加模板锚定关系数据路径、真实公式写入、单位换算、主键去重、终审/生效选择、异常追踪、严格输出覆盖门禁、文档感知动作、统一字段列表协议；
- 真实模型：`qwen3.7-max-2026-05-17`，OpenAI-compatible DashScope 接口；
- 真实模型首次完整验收：6 passed、2 failed，耗时 465.35 秒。失败为 AQI Top3 写回顺序被置信度重排，以及多源 COVID 计划丢弃 DOCX 中国记录；
- 根因修复：写回合并保持业务排序；追加型多源任务统一使用完整候选流；无明确关联语义时拒绝模型臆造的 `join`；无明确缺失值语义时拒绝模型臆造的 `impute`；RAG 后按原文位置恢复顺序敏感段落；国家/大洲中英文别名归一；
- 失败项复验：AQI 单项通过；COVID 最终单项 1 passed（69.49 秒），精确验证 `China/2020-07-27/68` 与 `China/2020-08-01/45`；
- 真实模型最终完整验收：8 passed，耗时 335.68 秒；命令为 `python -m pytest backend/tests/acceptance -q`；
- 后端普通回归：174 passed、8 deselected，耗时 26.82 秒；其中确定性业务回归见 `backend/tests/test_business_integrity.py`；
- Ruff：通过；Web lint：0 warnings、0 errors；Web 单元测试：2 files / 5 tests passed；Vite 生产构建：通过；
- Android：本轮按 `scripts/test.ps1 -SkipAndroid` 未执行；此前因本机缺少 Java / `JAVA_HOME` 受阻，仍不得视为通过；
- 原始真实运行报告：本地 `reports/table_fill/`，不提交 Git；报告包含任务计划、证据摘要、候选统计和单元格追踪；
- 结论：除 Android 环境受阻项外，本轮可执行的项目标准回归与真实模型验收均通过。

## 2026-08-01：`tests/manual` Web 网关验收

- 范围：使用 `tests/manual` 下 15 套真实源文件提交到本机 Web 网关；期望文件只用于下载后的严格比对，未作为模型输入；
- 专用 Web 账号：通过注册页创建并登录；页面上传冒烟测试已执行；
- `qwen3.7-max-2026-05-17` 完整基线：15 个任务中 12 个完成、3 个失败，严格产物比对 0/15；原始报告为本地 `reports/test-runs/20260801-web-qwen37-full-manual/results.json`；
- 基线根因：中文日期空格未归一、重复字段数组导致 Pydantic 整单失败、文档嵌套结构化请求被兼容接口拒绝、Excel 数字被写成文本、计算列被写成静态值、复杂表格记录关联失败；
- 已修复：提取数组兼容和日期归一、限流等待与上传流重置、Excel 数字类型、计算列公式保留、预置模板行匹配、文档普通 JSON 响应本地校验；相关定向单元测试 19 passed；
- 切换模型：按要求改为 `qwen3.7-max-preview`，并在 worker 容器内通过 `printenv OPENAI_MODEL` 确认；
- preview 完整基线：15 个任务中 13 个完成、2 个失败，严格产物比对 2/15（员工入职、销售汇总）；原始报告为本地 `reports/test-runs/20260801-web-qwen37-preview-manual/results.json`；
- 修复后定向复验：产品简报与报名名单任务均完成；报名名单严格通过，产品简报仍因摘要位置/内容、遗留 Markdown 表格段落和表格措辞差异不通过；原始报告为本地 `reports/test-runs/20260801-web-preview-targeted1-manual/results.json`；
- 修复后项目标准回归：Ruff 通过；后端 177 passed、8 deselected；Web lint 0 warnings/0 errors；Web 单元测试 5 passed；Vite 生产构建通过；Android 按命令显式跳过；
- 当前结论：不通过。已确认严格通过的 manual 用例为 3 个；文档编辑 5 个均需继续修复，复杂表格中的项目台账、供应商评分和经营驾驶舱仍需修复，其他提取用例仍有规范化差异。

## 2026-08-01：`tests/manual` 最终交付验收

- 原则：任务状态成功与产物正确分开判定；仅当下载产物与期望字段、文档段落/格式或 Excel 单元格/公式/格式严格一致时记为通过；
- 模型：`qwen3.7-max-preview`，已在 worker 容器内确认；
- Web 全量结果：15 个任务成功，15 个期望字段/文档/工作簿比较通过；信息提取 5/5、文档编辑 5/5、表格填充 5/5；原始报告为本地 `reports/test-runs/20260801-web-preview-final1-manual/results.json`；
- 严格口径加固：信息提取比较器现将额外字段也判为失败；修正故障复盘字段契约后，`reports/test-runs/20260801-web-extraction-strict-final-manual/results.json` 在新口径下 5/5，且无额外字段；结合文档 5/5 和最终表格 5/5，最终严格结果为 15/15；
- 最终表格链路复验：`reports/test-runs/20260801-web-tables-final-manual/results.json` 为 5/5；随后针对发现的模型复核误判继续修复，报名名单在 `20260801-web-signup-quality-final-manual` 中首次执行成功、严格通过、质量 `pass`、证据覆盖率 100%；经营驾驶舱在 `20260801-web-dashboard-quality-final-manual` 中首次执行成功、严格通过、质量 `pass`、证据覆盖率 100%；
- 故障复盘字段契约修正后复验：`reports/test-runs/20260801-web-incident-fixture-final-manual` 为 1/1；
- 核心业务修复：模板锚定多源关联、主键去重与终审/生效覆盖、退款和版本异常追溯、公式保留、模板新增行样式继承、自动序号、公式/序号证据追溯、文档结构化编辑、提取字段归一化；
- 去除无效智能壳：已关联完成的最终记录不再被模型计划二次聚合；确定性可完整解析的表不再调用模型规划；没有下游消费者的候选选择模型调用已删除；确定性质量门禁通过后不再调用模型复核；
- 确定性夹具回归：5 个文档编辑夹具逐段落/格式/表格精确比较；4 个复杂表格夹具逐单元格/公式/格式精确比较；
- 项目标准回归：Ruff 通过；后端 186 passed、8 deselected；Web lint 0 warnings/0 errors；Web 单元测试 2 files / 5 tests passed；Vite 生产构建通过；
- 材料修正：经营驾驶舱华东净收入按源数据算术改为 1372；合作备忘录乙方期望统一为“远帆理工大学”；故障复盘请求字段统一为“改进动作数量”；应急预案要求补充了期望版本日期的来源约束；详见 `fixture-issues.md`；
- 环境说明：Android 因本机缺少 Java / `JAVA_HOME` 未执行；DOCX 外观渲染因缺少 LibreOffice/soffice 未执行，已完成 python-docx 结构和格式快照精确校验；Windows 下根目录 `.pytest_cache` 权限异常会阻塞旧版 Docker context 扫描，`scripts/test.ps1` 已禁用 pytest cache，最终运行容器通过文件同步加载最后的 worker 修改；
- 结论：本轮 Web 核心业务验收与可执行的项目标准回归全部通过；Android 和 DOCX 页面级渲染仍是明确记录的环境受阻项，不计作通过。
