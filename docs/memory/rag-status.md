# RAG 核心模块状态

## 状态
- 完成度：90%
- 最后更新：2026-08-29

## 核心能力
- 多通道检索：向量、关键词、知识图谱、联网搜索
- RRF 融合 + Rerank 重排序
- 意图识别与多知识库路由
- Agent ReAct 执行架构

## 配置要点
- Embedding 模型：`qwen-emb-8b`（百炼 text-embedding-v4）
- 向量库：PostgreSQL + pgvector（dimension=1536, metric=COSINE）
- 关键词检索：默认关闭（`rag.keyword.type=none`）
- 图谱检索：默认关闭（`rag.graph.type=none`）

## 已知配置
```yaml
rag:
  vector:
    type: pg
  default:
    collection-name: rag_default_store
    dimension: 1536
    metric-type: COSINE
```

## 测试验证
- RAG 全流程测试：8/8 通过
- 支持 Markdown 文档上传、分块、向量化、检索、生成

## 相关文件
- `rag/src/main/java/.../rag/service/KnowledgeSearchFacade.java`
- `rag/src/main/java/.../knowledge/service/impl/KnowledgeDocumentServiceImpl.java`
- `bootstrap/src/main/resources/application.yaml`
