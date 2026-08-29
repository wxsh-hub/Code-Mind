# Code-Mind 项目记忆

## 项目概述

Code-Mind 是企业级 AI 知识管理平台，融合 RAG 检索与 MCP 协议，将项目经验沉淀为可复用的知识资产。

## 模块状态

| 模块 | 状态 | 最后更新 | 详细记忆 |
|------|------|----------|----------|
| RAG 核心 | ✅ 可用 | 2026-08-29 | [rag-status.md](rag-status.md) |
| MCP Gateway | ✅ 可用 | 2026-08-29 | [mcp-gateway-status.md](mcp-gateway-status.md) |
| Chunk API | ✅ 可用 | 2026-08-29 | [chunk-api-status.md](chunk-api-status.md) |
| 元数据扩展 | ✅ 完成 | 2026-08-29 | [metadata-status.md](metadata-status.md) |
| 集成设计 | ✅ 完成 | 2026-08-29 | [integration-design.md](integration-design.md) |
| MCP Gateway 文件索引 | ✅ 完成 | 2026-08-29 | [mcp-gateway-files.md](mcp-gateway-files.md) |

## 关键决策

1. **向量库选择**：使用 PostgreSQL + pgvector（而非 Milvus），简化部署
2. **Embedding 模型**：使用 `qwen-emb-8b`（百炼 text-embedding-v4），维度 1536
3. **MCP 协议**：ragent 作为 MCP Client 连接 mcp-gateway
4. **元数据扩展**：在 `t_knowledge_chunk` 表添加 source_type、vote_count 等字段
5. **矛盾检测**：同文件取新版，不同文件都保留，同源用投票机制

## 已知问题

1. **RocketMQ 编码**：broker 需配置 `brokerIP1=127.0.0.1` 才能从宿主机连接
2. **中文请求**：curl 发送中文 JSON 需要 `--data-binary` 和 `charset=UTF-8`
3. **知识库名称**：不能重复，测试脚本用时间戳保证唯一性

## 测试状态

| 测试脚本 | 通过率 | 最后运行 |
|----------|--------|----------|
| test_rag_flow.sh | 8/8 | 2026-08-29 |
| test_chunk_api.sh | 12/12 | 2026-08-29 |

## 下一步

- [ ] MCP Gateway 端集成测试
- [ ] GitLab 采集功能联调
- [ ] 矛盾检测端到端验证
- [ ] 前端管理界面适配
