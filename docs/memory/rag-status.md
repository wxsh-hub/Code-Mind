---
name: rag-status
description: RAG 核心模块状态
metadata:
  type: project
---

# RAG 核心模块状态

## 状态
- 完成度：90%
- 最后更新：2026-08-29

## 核心功能

### 多通道检索
- **向量检索**：pgvector + COSINE 相似度
- **关键词检索**：LIKE 模糊匹配（中文不准确）
- **知识图谱**：默认关闭
- **Web 搜索**：默认关闭

### RRF 融合 + Rerank
- 多通道结果融合
- Rerank 重排序

### 向量存储
- **数据库**：PostgreSQL + pgvector
- **维度**：1536（qwen-emb-8b）
- **度量**：COSINE

### Embedding 模型
- **模型**：qwen-emb-8b（阿里百炼 text-embedding-v4）
- **维度**：1536

## 配置

```yaml
ai:
  providers:
    bailian:
      api-key: sk-ws-H.xxx
rag:
  mcp:
    servers:
      - name: experience-gateway
        url: http://localhost:8000
```

## 测试

- test_rag_flow.sh：8/8 通过
- test_chunk_api.sh：12/12 通过

## 已知问题

1. **中文 LIKE 检索不准确**：需要改为向量检索
2. **RocketMQ 编码问题**：中文内容可能乱码
