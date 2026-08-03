# 持续测试日志

本文件按时间记录测试事实。状态只使用“通过”“不通过”“受阻”；代码修改说明和技术债记录在[维护记录](../development/maintenance-log.md)，当前发布判断见[发布就绪检查](../release-readiness.md)。

## 当前有效基线

| 范围 | 最近有效结果 | 状态 |
| --- | --- | --- |
| Python 非真实模型回归 | 195 passed、8 deselected；覆盖率 71.08% | 通过 |
| 表格引擎确定性评估 | 3/3 | 通过 |
| Web lint / unit / build / audit / E2E | 0 errors；9/9；通过；0 vulnerabilities；4/4 | 通过 |
| 15 套真实材料 Web 验收 | 最近完整基线 15/15；本轮定向复验：信息提取 1/5、表格填充 5/5 | 受阻 |
| Android 本轮回归 | 未执行，缺少 Java / `JAVA_HOME` | 受阻 |
| DOCX 页面级渲染 | 未执行，缺少 LibreOffice/soffice；结构与格式快照已通过 | 受阻 |

当前容器配置模型为 `qwen3.7-max-preview`。本轮真实 Web 定向复验结果见 `WT-20260802-01`；确定性代码回归不能替代被 Docker 外部 TLS 阻断的模型调用。

## WT-20260803-01：生产网关认证路由修复

- 生产部署发现首页“登录/注册”无法进入认证页；根因是请求客户端只在开发模式默认使用 `/api`，生产构建错误地请求 `/user/profile`，并被 Nginx SPA 回退返回首页 HTML；
- 请求客户端的默认 API 根路径统一为 `/api`，所有认证、任务、文档、工作台与企业接口继续共用该客户端；
- Playwright 运行器改为先执行 Vite 生产构建，再通过生产预览服务执行桌面与移动端流程，覆盖 `import.meta.env.DEV=false` 的真实构建分支；
- Python：195 passed、8 deselected，覆盖率 71.08%；Ruff、Mypy、compileall 通过；表格引擎确定性评估 3/3；
- Web：lint 0 warnings/0 errors；9/9 单元测试；生产构建通过；生产产物 Playwright 4/4；`npm audit` 为 0 vulnerabilities；
- Android：当前机器仍缺少 Java / `JAVA_HOME`，单元测试、Lint 与构建受阻；
- 结论：生产 API 路由缺陷已修复并由生产构建浏览器门禁覆盖；真实模型材料验收、目标服务器 HTTPS、备份恢复与告警仍未完成。

## WT-20260803-02：公网 IP/HTTP 临时会话模式

- 为不使用域名的临时 HTTP 部署增加 `SESSION_COOKIE_SECURE` 显式开关；生产模式默认仍启用 Secure Cookie，仅设置为 `false` 时允许浏览器通过 HTTP 保存会话；
- 登录和退出使用同一 Cookie 安全配置，避免删除属性与创建属性不一致；
- 认证、配置和安全定向回归 26/26；Ruff、Mypy 通过；
- 结论：HTTP/IP 登录具备显式、可审计的临时配置路径；关闭 Secure Cookie 会降低传输安全性，不改变生产部署仍需 HTTPS 的发布判断。

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

## WT-20260802-01：用户反馈用例回归修复

- 反馈范围：文档智能操作通过；信息提取 1—4 通过、故障复盘失败；表格填充 2/4/5 通过、报名名单报错、项目台账部分错误；
- 材料协议：5 个 `提取字段.txt` 已统一为单行英文逗号分隔，并新增协议回归测试；
- 信息提取：故障复盘 13 个显式字段改为确定性时间线提取；完整命中时不调用模型，结果与 `期望结果.json` 精确一致；
- 表格填充：报名名单增加模板锚定的中文行内多记录解析；报名名单和项目台账均通过完整 Agent、计算、Writer 流水线的逐单元格、公式和格式精确比较；
- 定向回归：信息提取和业务完整性 35 tests passed；
- 项目门禁：Ruff、Mypy、compileall 通过；195 passed、8 deselected；覆盖率 71.08%；表格评估 3/3；Web lint、9 项单元测试、生产构建、0 vulnerabilities、Playwright 4/4 均通过；
- 真实 Web 表格复验：通过网关登录、上传、异步 Worker、下载及严格工作簿比较，5/5 任务成功、5/5 比较通过；报名名单和项目台账均为 0 个单元格、公式或格式差异。原始明细保存在未提交的 `reports/test-runs/20260802-web-tables-recheck-manual/results.json`；
- 真实 Web 信息提取复验：故障复盘成功，13/13 字段精确匹配；其余 4 项均在调用 `qwen3.7-max-preview` 的外部 TLS 建连阶段失败。Worker 直连与通过宿主机代理均复现 `SSL: UNEXPECTED_EOF_WHILE_READING`，而宿主机绕过 Docker 直连同一 DashScope 端点得到 HTTP 401，证明端点可达且故障位于当前 Docker 出网链路，不是字段比较失败。原始明细保存在未提交的 `reports/test-runs/20260802-web-extraction-recheck-manual/results.json`；
- 运行器修复：本地 `BASE_URL` 明确忽略宿主机代理，避免访问 `127.0.0.1` 被错误代理成 502；Compose 增加独立的可选容器代理配置，不复用宿主机回环地址；
- Android：按 `-SkipAndroid` 未执行；
- 结论：用户反馈的三个业务缺陷均已在真实 Web 链路验证修复（信息提取用例 5、表格用例 1/3）；表格全量 5/5。信息提取用例 1—4 的本轮失败属于 Docker 到模型供应商的 TLS 环境阻断，不能登记为通过，恢复容器出网后必须重新执行 5 项提取验收。
