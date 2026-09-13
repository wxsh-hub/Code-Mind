---
name: quick-start
description: 新 AI 开发者快速入门指南
metadata:
  type: reference
---

# Code-Mind 快速入门指南

## 你是谁

你是 Code-Mind 项目的 AI 开发者。Code-Mind 是企业级 AI 知识管理平台，让 AI 能够访问和管理企业知识库。

## 项目在哪里

| 模块 | 路径 | 语言 |
|------|------|------|
| ragent (后端) | D:\11111111111\AAAworkAAA\ragent | Java 17 |
| mcp_gateway (MCP网关) | D:\11111111111\AAAworkAAA\ragent\mcp_gateway | Python 3.10+ |
| frontend (前端) | D:\11111111111\AAAworkAAA\ragent\frontend | React 18 |
| tests (测试) | D:\11111111111\AAAworkAAA\ragent\tests | Python |

## 第一步：读记忆

在开始任何工作之前，先读取记忆文件：

```
D:\11111111111\AAAworkAAA\ragent\docs\memory\
├── MEMORY.md              # 项目总览（必读）
├── QUICK_START.md         # 本文件
├── mcp-gateway-status.md  # MCP Gateway 状态
├── rag-status.md          # RAG 状态
├── chunk-api-status.md    # Chunk API 状态
├── metadata-status.md     # 元数据状态
├── integration-design.md  # 集成设计
└── mcp-gateway-files.md   # 文件位置索引
```

## 第二步：了解架构

```
AI Agent
    ↓ (MCP 协议)
MCP Gateway (Python)
    ↓ (HTTP API)
ragent (Java)
    ↓
PostgreSQL + pgvector
```

## 第三步：运行测试

### 单元测试（172 个）
```bash
cd D:\11111111111\AAAworkAAA\ragent
python -m pytest tests/test_memory_tools.py tests/test_conflict_review.py tests/test_rag_tools.py -v
```

### 混合检索测试（19 个）
```bash
cd D:\11111111111\AAAworkAAA\ragent
python tests/scripts/test_hybrid_search.py
```

### Playwright 前端测试
```bash
cd D:\11111111111\AAAworkAAA\ragent\frontend
python tests/scripts/test_frontend_simple.py
```

## 第四步：了解 MCP 工具

使用 `list_mcp_tools` 查看所有可用工具（30+ 个）。

主要工具：
- **知识检索**：search_experience（向量检索 + AI 回答）
- **记忆管理**：upload_memory, ask_project, batch_upload_memories, batch_delete_memories
- **模块管理**：create_module, list_modules, delete_module
- **功能管理**：create_feature, list_features, delete_feature
- **矛盾审核**：submit_conflict_for_review, list_conflicts, review_conflict
- **向量管理**：deprecate_chunk, batch_deprecate_chunks

## 第五步：开始开发

### 添加新功能
1. 在 ragent 添加 API
2. 在 mcp-gateway 添加 MCP 工具
3. 写测试
4. 运行测试
5. 更新记忆文件

### 代码规范
- ragent：Java 17 + Spring Boot + MyBatis Plus
- mcp-gateway：Python 3.10+ + FastMCP
- 测试：每个模块必须有对应测试

### 提交规范
```
feat: 新功能
fix: 修复 bug
docs: 文档更新
test: 测试相关
```

## 本地服务

| 服务 | 地址 | 说明 |
|------|------|------|
| ragent API | http://localhost:9090/api/ragent | Java 后端 |
| PostgreSQL | localhost:5432 | 向量数据库 |
| Redis | localhost:6379 | 缓存 |
| RocketMQ | localhost:9876 | 消息队列 |

## 常见任务

### 查询知识（推荐：向量检索 + AI 回答）
```python
result = search_experience(
    query="如何实现分页",
    top_k=5
)
# 返回: ai_answer, results, deprecated_chunks
```

### 查询知识（逐级降级检索）
```python
result = ask_project(
    project="Code-Mind",
    question="如何实现分页",
    feature_codes=["2437"],
    module="user"
)
# 检索顺序: 功能级 → 模块级 → 全库 → 向量
```

### 上传知识
```python
upload_memory(
    project="Code-Mind",
    filename="2437_人员管理.md",
    content="...",
    feature_codes=["2437"],
    module="user"
)
```

### 批量上传
```python
batch_upload_memories(
    project="Code-Mind",
    files=[
        {"filename": "doc1.md", "content": "..."},
        {"filename": "doc2.md", "content": "..."},
    ],
    feature_codes=["2437"],
    module="user"
)
```

### 删除过时向量
```python
deprecate_chunk(chunk_id="过时向量ID")

# 批量删除
batch_deprecate_chunks(chunk_ids=["id1", "id2", "id3"])
```

## 注意事项

1. **先读记忆**：开发前先读取记忆文件
2. **运行测试**：每次改动后运行测试
3. **更新记忆**：完成开发后更新记忆文件
4. **中文问题**：中文 LIKE 检索不准确，使用向量检索
5. **编码问题**：RocketMQ 传输中文可能乱码

## Git 仓库

- **地址**：git@github.com:wxsh-hub/Code-Mind.git
- **分支**：main
- **提交**：使用 SSH 方式

## 需要帮助？

读取 `docs/HELP_SYSTEM.md` 获取完整使用指南。
