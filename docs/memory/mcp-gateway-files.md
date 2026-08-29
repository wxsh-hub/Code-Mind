---
name: mcp-gateway-files
description: MCP Gateway 文件位置索引
metadata:
  type: reference
---

# MCP Gateway 文件位置索引

## 说明

MCP Gateway 是 Code-Mind 项目的 Python 子模块，位于 `D:\11111111111\AAAworkAAA\mcp-gateway\`。

## 源码文件

```
mcp_gateway/
├── gateway.py               # FastMCP 网关主入口
├── server.py                # Server 类和 GatewayContext
├── config.py                # 配置加载
├── sanitizers.py            # 数据脱敏
├── rag_client.py            # RAG HTTP 客户端
├── rag_tools.py             # search_experience MCP Tool
├── memory_tools.py          # 记忆管理 MCP Tools
├── skill_tools.py           # 技能管理 MCP Tools
├── feature_tools.py         # 模块/功能管理 MCP Tools
├── discovery_tools.py       # list_mcp_tools
├── conflict_review.py       # 矛盾审核 MCP Tools
├── vector_delete.py         # 向量删除 MCP Tools
├── path_resolver.py         # 路径引用解析
├── collector/               # GitLab/GitHub 采集模块
│   ├── gitlab_fetcher.py
│   ├── github_fetcher.py
│   ├── slimmer.py
│   ├── metadata_extractor.py
│   ├── ingest_client.py
│   └── scheduler.py
├── conflict/                # 矛盾检测模块
│   ├── detector.py
│   ├── resolver.py
│   ├── voter.py
│   └── aware_search.py
├── plugins/                 # 插件系统
│   ├── base.py
│   ├── manager.py
│   ├── guardrails/
│   └── tracing/
└── security_scanner/        # 安全扫描器
```

## 测试文件

```
tests/
├── test_rag_client.py       # RAG 客户端测试（4 个）
├── test_rag_tools.py        # RAG 工具测试（4 个）
├── test_memory_tools.py     # 记忆工具测试（8 个）
├── test_skill_tools.py      # 技能工具测试（12 个）
├── test_feature_tools.py    # 功能工具测试（9 个）
├── test_discovery_tools.py  # 发现工具测试（9 个）
├── test_conflict_review.py  # 矛盾审核测试（9 个）
├── test_vector_delete.py    # 向量删除测试（9 个）
├── test_collector.py        # 采集模块测试（9 个）
├── test_conflict.py         # 矛盾检测测试（16 个）
├── test_path_resolver.py    # 路径解析测试（13 个）
├── test_github_fetcher.py   # GitHub 获取器测试（7 个）
├── test_basic_guardrail.py  # 基础防护测试
├── test_config.py           # 配置测试
├── test_plugin_pipeline.py  # 插件管道测试
├── test_sanitizers.py       # 数据脱敏测试
├── test_security_scanner.py # 安全扫描测试
└── test_tool_poisoning_analyzer.py # 工具分析测试
```

## 测试数据

```
test_data/
├── 编码规范_Java.md
├── 编码规范_数据库.md
├── 编码规范_Git.md
├── 项目经验_分页实现.md
├── 项目经验_缓存设计.md
├── 架构设计_微服务.md
└── 架构设计_数据库.md
```

## 文档

```
docs/
├── FEATURE_PLAN.md          # 功能计划
├── HELP_SYSTEM.md           # 帮助文档
├── SUBMISSION_STANDARDS.md  # 提交规范
└── plans/                   # 详细计划
    ├── F1_vector_delete.md
    ├── F2_mcp_discovery.md
    ├── F3_submission_standards.md
    ├── F5_conflict_review.md
    ├── F6_help_docs.md
    └── F7_vector_metadata.md
```

## 测试脚本

```
test_final.sh                # 集成测试（28 个检查点）
test_mcp_gateway.bat         # Windows 单元测试
test_mcp_gateway.sh          # Linux/Mac 单元测试
test_skills.sh               # Skills 测试
test_integration.sh          # 旧集成测试
```

## 运行命令

```bash
# 单元测试
cd D:\11111111111\AAAworkAAA\mcp-gateway
python -m pytest tests/ -v

# 集成测试
bash test_final.sh
```
