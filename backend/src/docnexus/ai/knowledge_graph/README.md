# 知识图谱模块

知识图谱模块可以把结构化提取结果转换为轻量实体关系图，并导出 JSON 数据，
用于结果展示、证据追踪、实体消歧和 GraphRAG 扩展。

## 功能

- 归并人名、机构名、城市名等重复实体；
- 记录字段之间的来源关系和上下文关系；
- 关联字段值、证据片段和原始文档块；
- 导出便于展示、调试和检索增强使用的 JSON 数据。

## 使用示例

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
