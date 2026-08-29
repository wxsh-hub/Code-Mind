# MCP Gateway 项目规范

## 项目概述

MCP Gateway 是 Code-Mind 系统的网关层，负责：
- MCP 协议代理和工具注册
- RAG 知识库集成（search_experience）
- GitLab 文档采集和处理
- 矛盾检测和投票机制
- 安全扫描和数据脱敏

## 目录结构

```
mcp-gateway/
├── mcp_gateway/
│   ├── __init__.py
│   ├── gateway.py              # FastMCP 网关主入口
│   ├── server.py               # Server 类和 GatewayContext
│   ├── config.py               # 配置加载
│   ├── sanitizers.py           # 数据脱敏
│   ├── rag_client.py           # RAG HTTP 客户端
│   ├── rag_tools.py            # search_experience MCP Tool
│   ├── plugins/                # 插件系统
│   │   ├── base.py             # 插件基类
│   │   ├── manager.py          # 插件管理器
│   │   ├── guardrails/         # 安全防护插件
│   │   └── tracing/            # 追踪插件
│   ├── collector/              # GitLab 采集模块
│   │   ├── gitlab_fetcher.py   # GitLab API 客户端
│   │   ├── slimmer.py          # 内容瘦身
│   │   ├── metadata_extractor.py # 元数据提取
│   │   ├── ingest_client.py    # 文档摄入客户端
│   │   └── scheduler.py        # 采集调度器
│   ├── conflict/               # 矛盾检测模块
│   │   ├── detector.py         # 矛盾检测器
│   │   ├── resolver.py         # 冲突解决器
│   │   ├── voter.py            # 投票机制
│   │   └── aware_search.py     # 矛盾感知搜索
│   └── security_scanner/       # 安全扫描器
├── tests/                      # 测试文件
│   ├── test_rag_client.py      # RAG 客户端测试
│   ├── test_rag_tools.py       # RAG 工具测试
│   ├── test_collector.py       # 采集模块测试
│   ├── test_conflict.py        # 矛盾检测测试
│   └── ...                     # 其他测试
├── docs/                       # 文档
│   └── MCP_GATEWAY_PART.md     # 设计文档
└── .claude/rules/              # 项目规范
    └── project.md              # 本文件
```

## 编码规范

### Python 版本
- 最低版本：Python 3.10
- 使用类型注解
- 使用 dataclass 定义数据结构

### 命名规范
- 文件名：snake_case
- 类名：PascalCase
- 函数名：snake_case
- 常量：UPPER_SNAKE_CASE

### 导入规范
```python
# 标准库
import logging
from typing import Any, Dict, List, Optional

# 第三方库
from mcp import types

# 本项目
from mcp_gateway.rag_client import RAGClient
```

### 日志规范
```python
logger = logging.getLogger(__name__)
logger.info("操作成功")
logger.warning("警告信息")
logger.error("错误信息", exc_info=True)
```

## 测试规范

### 测试文件位置
所有测试文件放在 `tests/` 目录下，命名为 `test_*.py`。

### 测试命名
```python
class TestModuleName(unittest.TestCase):
    def test_function_name_scenario(self):
        """测试描述"""
        pass
```

### 测试覆盖要求
- 每个模块必须有对应的测试文件
- 核心功能必须有单元测试
- 测试必须全部通过才能提交

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_rag_client.py -v

# 运行并显示覆盖率
python -m pytest tests/ -v --cov=mcp_gateway
```

## 提交规范

### Commit 格式
```
<类型>: <简短描述>

<详细描述（可选）>
```

### 类型
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `test`: 测试相关
- `refactor`: 重构
- `style`: 代码格式
- `perf`: 性能优化

### 示例
```bash
git commit -m "feat: 添加 search_experience MCP Tool"
git commit -m "test: 添加 RAG 客户端单元测试"
git commit -m "docs: 更新 MCP Gateway 设计文档"
```

## 与 ragent 集成

### API 端点
- 基础 URL：`http://localhost:9090/api/ragent`
- 认证：Token 方式（通过 /auth/login 获取）

### 关键接口
- `POST /knowledge-base/search/similar` - 相似 chunk 检索
- `POST /knowledge-base/chunks/{id}/reference` - 记录引用
- `GET /knowledge-base/chunks/{id}/vote` - 查询投票
- `POST /knowledge-base/chunks/{id}/conflict-pair` - 设置矛盾对
- `POST /knowledge-base/chunks/{id}/deprecate` - 标记废弃

### 数据流
```
Agent 调用 search_experience
  ↓
MCP Gateway (rag_tools.py)
  ↓
RAG Client (rag_client.py)
  ↓
ragent API (KnowledgeChunkApiController)
  ↓
PostgreSQL + pgvector
```

## 依赖

### 核心依赖
- `mcp[cli]>=1.6.0` - MCP 协议
- `requests>=2.32.3` - HTTP 客户端
- `beautifulsoup4>=4.13.4` - HTML 解析

### 可选依赖
- `presidio-anonymizer>=2.2.0` - PII 脱敏
- `presidio-analyzer>=2.2.0` - PII 检测
- `xetrack>=0.3.4` - 追踪

### 开发依赖
- `pytest>=8.3.5` - 测试框架
- `pytest-asyncio>=0.21.0` - 异步测试
- `pytest-cov>=4.1.0` - 覆盖率
