# Chunk API 状态

## 状态
- 完成度：100%
- 最后更新：2026-08-29

## 新增接口

### KnowledgeChunkApiController

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 相似检索 | POST | `/knowledge-base/search/similar` | 基于关键词模糊匹配 |
| 记录引用 | POST | `/knowledge-base/chunks/{id}/reference` | vote_count + 1 |
| 查询投票 | GET | `/knowledge-base/chunks/{id}/vote` | 返回 vote_count |
| 设置矛盾对 | POST | `/knowledge-base/chunks/{id}/conflict-pair` | 设置 conflict_pair_id |
| 标记废弃 | POST | `/knowledge-base/chunks/{id}/deprecate` | deprecated = true |

## 请求格式

### 相似检索
```json
POST /knowledge-base/search/similar
{
  "query": "规范",
  "kbId": "可选",
  "topK": 10
}
```

### 响应格式
```json
{
  "code": "0",
  "data": [
    {
      "chunkId": "xxx",
      "content": "chunk 内容",
      "docId": "xxx",
      "kbId": "xxx",
      "metadata": {
        "sourceType": "upload",
        "sourceRef": null,
        "chunkVersion": 1,
        "voteCount": 0,
        "conflictPairId": null,
        "deprecated": false
      }
    }
  ]
}
```

## 测试验证
- Chunk API 测试：12/12 通过
- 覆盖：相似检索、引用计数、矛盾标记、废弃标记

## 相关文件
- `rag/src/main/java/.../knowledge/controller/KnowledgeChunkApiController.java`
- `test_chunk_api.sh`
