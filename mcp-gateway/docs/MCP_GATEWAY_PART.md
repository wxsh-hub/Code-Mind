# MCP Gateway 改造方案（MCP 部分）

## 功能清单

| 编号 | 功能 | 状态 | 测试 |
|------|------|------|------|
| F1 | RAG 客户端 | ✅ 完成 | test_rag_client.py |
| F3 | search_experience MCP Tool | ✅ 完成 | test_rag_tools.py |
| F8 | GitLab 采集器 | ✅ 完成 | test_collector.py |
| F9 | 内容瘦身 | ✅ 完成 | test_collector.py |
| F10 | 元数据提取 | ✅ 完成 | test_collector.py |
| F11 | 文档摄入客户端 | ✅ 完成 | test_collector.py |
| F12 | 采集调度器 | ✅ 完成 | test_collector.py |
| F13 | 矛盾检测 | ✅ 完成 | test_conflict.py |
| F14 | 冲突解决 | ✅ 完成 | test_conflict.py |
| F15 | 投票机制 | ✅ 完成 | test_conflict.py |
| F16 | 矛盾感知搜索 | ✅ 完成 | test_conflict.py |

---

## 详细设计

### F1: RAG HTTP 客户端

```
文件：mcp_gateway/rag_client.py
类：RAGClient, RAGConfig
```

功能：
- 登录认证（自动获取 token）
- 相似 chunk 检索（search_similar）
- 引用计数（record_reference）
- 投票分数查询（get_vote_score）
- 矛盾对设置（set_conflict_pair）
- 废弃标记（deprecate_chunk）
- RAG 问答（rag_chat）
- 分块列表（get_chunks）

使用 urllib 标准库，无需额外依赖。

### F3: search_experience MCP Tool

```
文件：mcp_gateway/rag_tools.py
函数：search_experience_impl, register_rag_tools
```

功能：
- 注册为 MCP Tool，Agent 可直接调用
- 搜索企业知识库中的项目经验和编码规范
- 自动记录引用（触发投票机制）
- 返回格式化的搜索结果

在 gateway.py 的 lifespan 中自动注册。

### F8-F12: GitLab 采集链路

```
文件：mcp_gateway/collector/
├── gitlab_fetcher.py    # GitLab API 获取 MD 文件
├── slimmer.py           # 内容瘦身（过滤短期价值）
├── metadata_extractor.py # 元数据提取（标题、标签、分类）
├── ingest_client.py     # 文档上传到 ragent
└── scheduler.py         # 定时调度
```

采集流程：
```
GitLab 仓库 → 获取 MD 文件 → 内容瘦身 → 元数据提取 → 上传 ragent → 分块向量化
```

调度器支持：
- 多项目采集
- 自定义路径模式
- 可配置间隔时间
- 状态查询

### F13-F16: 矛盾检测与投票

```
文件：mcp_gateway/conflict/
├── detector.py          # 矛盾检测器
├── resolver.py          # 冲突解决器
├── voter.py             # 投票机制
└── aware_search.py      # 矛盾感知搜索
```

矛盾检测流程：
```
新内容 → 相似检索 → 矛盾判断 → 冲突解决 → 记录结果
```

解决策略：
1. 同一文件冲突 → 保留新版本，废弃旧版本
2. 不同文件冲突 → 设置矛盾对，保留两者
3. 同源冲突 → 投票机制（引用计数达到阈值自动淘汰）

---

## MCP Tool 清单

### search_experience

```json
{
  "name": "search_experience",
  "description": "搜索企业项目经验和编码规范",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "搜索内容"
      },
      "kb_id": {
        "type": "string",
        "description": "限定知识库 ID（可选）"
      },
      "top_k": {
        "type": "integer",
        "description": "返回数量，默认 5"
      }
    },
    "required": ["query"]
  }
}
```

---

## 运行方式

```bash
# 安装依赖
pip install -e .

# 运行 MCP Gateway（包含 RAG 工具）
mcp-gateway --mcp-json-path mcp.json

# 运行测试
python -m pytest tests/ -v
```

---

## 配置示例

### mcp.json

```json
{
  "mcpServers": {
    "experience-gateway": {
      "command": "mcp-gateway",
      "args": ["--mcp-json-path", "mcp.json"]
    }
  }
}
```

### ragent 连接配置

在 mcp_gateway/rag_client.py 中修改 RAGConfig：

```python
RAGConfig(
    base_url="http://localhost:9090/api/ragent",
    username="admin",
    password="admin",
)
```
