# 客户级补充验收

本目录包含 2026-08-14 最终检查新增的 6 个文件级场景，覆盖文档编辑、信息提取和表格填充三项核心能力。样例重点验证引号内标点、局部格式保留、完整付款条款、否定语义、指定名单、无效记录排除、派生字段排序和模板数字格式。

测试材料可由 `scripts/generate_customer_acceptance_fixtures.py` 重建，通过 `scripts/run_customer_acceptance.py` 提交到已启动的本地 API。期望结果只用于下载后比较，不会作为模型输入上传。

运行示例：

```powershell
python scripts/run_customer_acceptance.py `
  --base-url http://127.0.0.1:8000/api `
  --email acceptance@example.com `
  --password "仅用于本地测试的密码" `
  --register
```

原始运行产物写入 `reports/test-runs/`，该目录不纳入版本库。
