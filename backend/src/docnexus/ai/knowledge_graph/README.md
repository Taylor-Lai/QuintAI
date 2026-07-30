# 知识图谱模块

该模块将结构化提取结果转换为轻量级实体关系图，用于慧文融通的结果展示、证据追踪、实体消歧及后续 GraphRAG 能力扩展。

## 能力边界

- 归并规范化后的人名、机构、地点和业务实体；
- 记录字段值、证据片段与原始文档块之间的关系；
- 保留来源标识，支持从图节点回到提取证据；
- 导出稳定的 JSON 结构，供 API、前端可视化和检索增强使用。

知识图谱不能替代原始证据，也不得依据图关系生成缺乏来源支持的事实。实体合并过程必须保留可解释的规范化依据。

## 使用示例

```python
from docnexus.ai.knowledge_graph import KnowledgeGraphBuilder, export_graph_json

result = {
    "项目名称": "慧文融通",
    "负责人": "张三",
    "_meta": {
        "evidence": {
            "负责人": {
                "chunk_id": 0,
                "snippet": "项目负责人为张三",
            }
        }
    },
}

graph = KnowledgeGraphBuilder().from_extraction_result(result)
json_text = export_graph_json(graph)
```

## 集成要求

- 调用方应传入已经完成字段归一化的提取结果；
- `_meta.evidence` 中的引用必须能定位到当前用户有权访问的文档；
- API 返回图数据前仍需执行用户或组织所有权校验；
- 修改节点、边或导出结构时，应同步更新相关测试和消费方。
