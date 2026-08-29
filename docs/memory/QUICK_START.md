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

| 项目 | 路径 | 语言 |
|------|------|------|
| ragent | D:\11111111111\AAAworkAAA\ragent | Java 17 |
| mcp-gateway | D:\11111111111\AAAworkAAA\mcp-gateway | Python 3.10+ |

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

### MCP Gateway 测试
```bash
cd D:\11111111111\AAAworkAAA\mcp-gateway
python -m pytest tests/ -v
```

### 集成测试
```bash
cd D:\11111111111\AAAworkAAA\mcp-gateway
bash test_final.sh
```

## 第四步：了解 MCP 工具

使用 `list_mcp_tools` 查看所有可用工具（28 个）。

主要工具：
- **模块管理**：create_module, list_modules, delete_module
- **功能管理**：create_feature, list_features, delete_feature
- **记忆管理**：upload_memory, ask_project, delete_memory
- **技能管理**：upload_skill, search_skill, delete_skill
- **向量管理**：delete_vector, delete_vectors
- **矛盾审核**：list_conflicts, review_conflict

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

### 查询知识
```python
result = ask_project(
    project="Code-Mind",
    question="如何实现分页",
    feature_codes=["2437"],
    module="user"
)
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

### 删除错误向量
```python
delete_vector(
    project="Code-Mind",
    chunk_id="错误向量ID",
    find_similar=True
)
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
