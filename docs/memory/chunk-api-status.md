---
name: chunk-api-status
description: Chunk API 状态
metadata:
  type: project
---

# Chunk API 状态

## 状态
- 完成度：100%
- 最后更新：2026-08-29

## API 清单

### KnowledgeChunkApiController

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 相似检索 | POST | /knowledge-base/search/similar | 支持 JSONB 过滤 |
| 记录引用 | POST | /knowledge-base/chunks/{id}/reference | vote_count + 1 |
| 查询投票 | GET | /knowledge-base/chunks/{id}/vote | 返回 vote_count |
| 设置矛盾对 | POST | /knowledge-base/chunks/{id}/conflict-pair | 设置 conflict_pair_id |
| 标记废弃 | POST | /knowledge-base/chunks/{id}/deprecate | 设置 deprecated |
| 计算置信度 | POST | /knowledge-base/chunks/{id}/calculate-confidence | 计算 confidence |
| 查询置信度 | GET | /knowledge-base/chunks/{id}/confidence | 返回 confidence |
| 归一化置信度 | POST | /knowledge-base/chunks/normalize-confidence | 批量归一化到100 分 |

### 相似检索参数

```json
{
    "query": "搜索内容",
    "kbId": "知识库ID（可选）",
    "topK": 10,
    "featureCodes": "2437,2438（可选，逗号分隔）",
    "module": "user（可选）"
}
```

### 返回字段

```json
{
    "chunkId": "向量ID",
    "content": "内容",
    "docId": "文档ID",
    "kbId": "知识库ID",
    "metadata": {
        "sourceType": "upload",
        "sourceRef": null,
        "chunkVersion": 1,
        "voteCount": 5,
        "conflictPairId": null,
        "deprecated": false
    },
    "uploadCount": 10,
    "lastUploadAt": "2026-08-29T18:00:00",
    "confidence": 10
}
```

## 测试状态

- 单元测试：通过
- 集成测试：通过
