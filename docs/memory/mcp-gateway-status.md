# MCP Gateway 状态

## 状态
- 完成度：80%
- 最后更新：2026-08-29

## 核心能力
- MCP 协议代理：动态 tool 注册
- 安全过滤：Guardrail 插件（正则过滤密钥/token）
- 安全扫描：Scanner 对工具做信誉评估
- 调用追踪：xetrack 插件记录调用上下文

## 新增模块

### RAG 客户端（rag_client.py）
- 调用 ragent 的知识库文档搜索接口
- 支持异步 HTTP 请求

### RAG MCP Tool（rag_tools.py）
- `search_experience`：检索企业项目经验与开发规范
- 自动格式化返回结果

### 采集器（collector/）
- `gitlab_fetcher.py`：从 GitLab 拉取 MD 文件
- `slimmer.py`：AI 判断长期价值，过滤短期内容
- `metadata.py`：元数据标注（来源、版本、投票等）
- `ingest.py`：入库到 ragent 知识库
- `scheduler.py`：定时采集调度

### 矛盾检测（conflict/）
- `detector.py`：检测新 chunk 与已有 chunk 的矛盾
- `resolver.py`：同文件取新版，不同文件都保留
- `voter.py`：引用频次投票机制
- `aware_search.py`：检索时感知矛盾

## 配置要点
- 启动命令：`mcp-gateway --mcp-json-path mcp.json -p basic`
- ragent 连接配置：`rag.mcp.servers[].url = http://localhost:8000`

## 测试验证
- 单元测试：pytest tests/ -v
- 集成测试：待完成

## 相关文件
- `mcp-gateway/mcp_gateway/rag_client.py`
- `mcp-gateway/mcp_gateway/rag_tools.py`
- `mcp-gateway/mcp_gateway/collector/`
- `mcp-gateway/mcp_gateway/conflict/`
