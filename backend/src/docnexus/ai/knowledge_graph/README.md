# 知识图谱旁路模块

这是 QuintAI AI 模块中预留的实验性知识图谱能力。

当前边界：

- 不接入信息提取主流程；
- 不接入自动填表主流程；
- 不影响 RAG、Agent Skill、规则抽取和结果写回；
- 可以从结构化提取结果生成轻量实体关系图；
- 可以导出 JSON，供展示、调试或后续 GraphRAG 扩展使用。

设计用途：

- 实体消歧：归并同一人名、机构名或城市名；
- 关系约束：记录字段间的来源关系和上下文关系；
- 证据追踪：把字段值、证据片段和文档块组织成图；
- GraphRAG：作为检索增强过程的图结构补充。

示例：

```python
from docnexus.ai.knowledge_graph import KnowledgeGraphBuilder, export_graph_json

result = {
    "项目名称": "QuintAI",
    "负责人": "张三",
    "_meta": {
        "evidence": {
            "负责人": {"chunk_id": 0, "snippet": "项目负责人为张三"}
        }
    },
}

graph = KnowledgeGraphBuilder().from_extraction_result(result)
json_text = export_graph_json(graph)
```
