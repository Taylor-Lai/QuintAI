# 知识图谱模块

慧文融通采用证据驱动的知识图谱：结构化抽取结果被规范化为实体和类型化关系，每个结论均独立保存来源文档、字段、原文片段、位置与置信度。知识库内同类型、同规范名称的实体可以归并，但来源证据只累加、不覆盖。

## 数据结构

- `KnowledgeEntity`：文档、项目、人员、组织、地点、时间、指标和概念；
- `KnowledgeRelation`：记载、负责人、隶属机构、位于、发生于、具有指标等受控关系；
- `KnowledgeEvidence`：实体或关系对应的文档、片段、抽取记录和原文证据；
- `KnowledgeChunk`：用于关键词与本地特征向量检索的原始文档片段。

持久化构图由 `docnexus.services.knowledge_graph` 负责。文档加入知识库、已入库文档完成字段抽取或用户主动重新构建时，服务会基于当前授权范围同步图谱。
实体可由具备知识库编辑权限的成员标记为“已确认”或“存疑”；幂等重建会保留既有人工复核状态。

## 检索行为

检索以关键词和本地确定性特征向量完成基础排序；查询命中图谱实体时，服务沿相关关系扩展一跳，并使用有证据支持的关联文档进行有限加权。响应同时返回关系路径和原始片段引用。

当前特征向量用于离线、确定性的相关度计算，不表示外部语义 Embedding。图谱关系不得替代原始证据，也不得用于生成缺乏来源支持的事实。

## 轻量构图工具

`KnowledgeGraphBuilder` 保留为无数据库场景下的 JSON 构图工具：

```python
from docnexus.ai.knowledge_graph import KnowledgeGraphBuilder, export_graph_json

result = {
    "项目名称": "慧文融通",
    "负责人": "张三",
    "_meta": {"evidence": {"负责人": {"chunk_id": 0, "snippet": "项目负责人为张三"}}},
}

graph = KnowledgeGraphBuilder().from_extraction_result(result)
json_text = export_graph_json(graph)
```

该工具不会写入业务数据库。线上 API 必须使用持久化服务，并在读取或重建图谱前校验用户角色和组织所有权。
