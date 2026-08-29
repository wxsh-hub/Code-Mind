# MCP Gateway 文件位置索引

## 说明

MCP Gateway 是 Code-Mind 项目的 Python 子模块，位于 `mcp-gateway/` 目录。
当需要修改 MCP Gateway 的代码、测试或记忆时，参考本文件定位。

## 记忆文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 规范 | `mcp-gateway/.claude/rules/project.md` | 项目规范（测试、代码、目录结构） |
| 设计文档 | `mcp-gateway/docs/MCP_GATEWAY_PART.md` | MCP Gateway 端改造方案 |

## 测试文件

| 文件 | 路径 | 覆盖范围 |
|------|------|----------|
| test_rag_client.py | `mcp-gateway/tests/test_rag_client.py` | RAG 客户端 |
| test_rag_tool_registration.py | `mcp-gateway/tests/test_rag_tool_registration.py` | MCP Tool 注册 |
| test_slimmer.py | `mcp-gateway/tests/test_slimmer.py` | MD 瘦身 |
| test_metadata.py | `mcp-gateway/tests/test_metadata.py` | 元数据标注 |
| test_conflict_detector.py | `mcp-gateway/tests/test_conflict_detector.py` | 矛盾检测 |
| test_conflict_resolver.py | `mcp-gateway/tests/test_conflict_resolver.py` | 矛盾解决 |
| test_voter.py | `mcp-gateway/tests/test_voter.py` | 投票机制 |
| test_aware_search.py | `mcp-gateway/tests/test_aware_search.py` | 冲突感知检索 |
| test_gateway_integration.py | `mcp-gateway/tests/test_gateway_integration.py` | 集成测试 |
| test_basic_guardrail.py | `mcp-gateway/tests/test_basic_guardrail.py` | Guardrail 插件 |
| test_config.py | `mcp-gateway/tests/test_config.py` | 配置加载 |
| test_sanitizers.py | `mcp-gateway/tests/test_sanitizers.py` | 清洗器 |
| test_security_scanner.py | `mcp-gateway/tests/test_security_scanner.py` | 安全扫描 |
| test_plugin_duplicates.py | `mcp-gateway/tests/test_plugin_duplicates.py` | 插件去重 |
| test_plugin_pipeline.py | `mcp-gateway/tests/test_plugin_pipeline.py` | 插件管线 |
| test_ingest_tools.py | `mcp-gateway/tests/test_ingest_tools.py` | 入库工具 |

## 测试运行命令

```bash
# 运行全部测试
cd mcp-gateway && python -m pytest tests/ -v --tb=short -s --ignore=tests/xetrack_tracing_test.py --ignore=tests/test_npm_version_simple.py

# 运行指定模块
cd mcp-gateway && python -m pytest tests/test_rag_client.py -v --tb=short -s
```

## 源码文件

| 模块 | 路径 | 说明 |
|------|------|------|
| RAG 客户端 | `mcp-gateway/mcp_gateway/rag_client.py` | 调用 ragent 检索 API |
| RAG MCP Tool | `mcp-gateway/mcp_gateway/rag_tools.py` | search_experience 工具 |
| 入库工具 | `mcp-gateway/mcp_gateway/ingest_tools.py` | 文档入库 MCP Tool |
| GitLab 采集 | `mcp-gateway/mcp_gateway/collector/gitlab_fetcher.py` | 拉取 MD 文件 |
| MD 瘦身 | `mcp-gateway/mcp_gateway/collector/slimmer.py` | AI 判断长期价值 |
| 元数据 | `mcp-gateway/mcp_gateway/collector/metadata.py` | ChunkMetadata 定义 |
| 入库接口 | `mcp-gateway/mcp_gateway/collector/ingest.py` | 调用 ragent 入库 |
| 定时调度 | `mcp-gateway/mcp_gateway/collector/scheduler.py` | 定时采集 |
| 矛盾检测 | `mcp-gateway/mcp_gateway/conflict/detector.py` | 检测矛盾 chunk |
| 矛盾解决 | `mcp-gateway/mcp_gateway/conflict/resolver.py` | 处理策略 |
| 投票机制 | `mcp-gateway/mcp_gateway/conflict/voter.py` | 引用频次投票 |
| 冲突感知 | `mcp-gateway/mcp_gateway/conflict/aware_search.py` | 检索时感知矛盾 |

## 更新规则

修改 MCP Gateway 代码后：
1. 更新 `mcp-gateway/.claude/rules/project.md`（如涉及规范变更）
2. 更新本文件 `docs/memory/mcp-gateway-files.md`（如新增/删除文件）
3. 更新 `docs/memory/MEMORY.md` 索引
