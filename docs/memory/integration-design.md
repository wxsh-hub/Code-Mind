# 集成设计状态

## 状态
- 完成度：60%
- 最后更新：2026-08-29

## 整体架构

```
GitLab (MD文件)
    │  定时拉取
    ▼
mcp-gateway (Python)
    ├── 瘦身 + 元数据标注
    ├── 矛盾检测 + 投票
    └── search_experience MCP Tool
           │
    Guardrail 插件自动过滤敏感信息
           │
ragent (Java) MCP Client 连接
           │
    Agent 写代码时调用 → 查企业经验
```

## 已完成

### rag 端
- ✅ KnowledgeChunkApiController（相似检索、引用计数、矛盾标记）
- ✅ 数据库元数据扩展
- ✅ 实体类和 VO 扩展
- ✅ MCP Gateway 配置

### mcp-gateway 端
- ✅ RAG 客户端和 MCP Tool
- ✅ 采集器模块（GitLab、瘦身、元数据、入库、调度）
- ✅ 矛盾检测模块（检测、解决、投票、感知检索）

## 待完成

### rag 端
- [ ] Agent Prompt 指引（search_experience 使用说明）
- [ ] 向量检索接口优化（当前用关键词模糊匹配）

### mcp-gateway 端
- [ ] GitLab 采集联调测试
- [ ] 矛盾检测端到端验证
- [ ] 投票机制持久化（Redis/DB）

### 集成测试
- [ ] ragent → mcp-gateway 连接测试
- [ ] search_experience 端到端测试
- [ ] 采集 → 瘦身 → 入库 → 检索全流程

## 关键决策

1. **MCP 协议**：ragent 作为 MCP Client 连接 mcp-gateway
2. **检索接口**：mcp-gateway 调用 ragent 的 `/knowledge-base/docs/search` 接口
3. **矛盾处理**：同文件取新版，不同文件都保留，同源用投票机制
4. **元数据存储**：在 chunk 表添加字段，不引入新表

## 相关文件
- `docs/design/RAGENT_PART.md`
- `docs/design/MCP_GATEWAY_PART.md`
