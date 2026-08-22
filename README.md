<div align="center">

# MCP Gateway

**MCP 生态的安全中间层 — 在 LLM 与工具服务器之间建立防护屏障**

[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)

</div>

## 它解决什么问题？

当 LLM Agent 通过 MCP 协议调用外部工具时，存在三个核心风险：

1. **凭据泄露** — 工具返回的响应中可能包含 API Key、Token 等敏感信息，直接暴露给 LLM 上下文
2. **隐私数据外泄** — 用户个人信息（姓名、身份证、银行卡号）可能在工具调用链中被传递
3. **恶意工具注入** — 工具描述中可能隐藏 prompt injection 指令，诱导 Agent 执行危险操作

MCP Gateway 作为代理层拦截所有流量，在请求/响应到达 Agent 之前进行安全过滤。

## 架构概览

```
┌─────────────┐      ┌──────────────────────────────────┐      ┌─────────────┐
│             │      │          MCP Gateway             │      │             │
│   LLM Agent │ ───► │  ┌──────────┐  ┌──────────────┐  │ ───► │  MCP Server │
│             │      │  │ Sanitize │  │   Plugin     │  │      │  (tools)    │
│             │ ◄─── │  │ Request  │  │   Pipeline   │  │ ◄─── │             │
└─────────────┘      │  └──────────┘  └──────────────┘  │      └─────────────┘
                     │         ▲               │         │
                     │         │    ┌──────────▼──┐      │
                     │         │    │  Sanitize   │      │
                     │         │    │  Response   │      │
                     │         │    └─────────────┘      │
                     └──────────────────────────────────┘
```

核心流程：
- **请求方向**：Plugin Pipeline 对参数进行脱敏（如移除 PII、过滤注入指令）
- **响应方向**：对工具返回值进行 Token 掩码、敏感信息过滤
- **启动阶段**：Security Scanner 对所有配置的 MCP Server 进行信誉评估

## 快速开始

### 安装

```bash
git clone <your-repo-url>
cd mcp-gateway
pip install -e .
```

可选依赖：
```bash
pip install -e .[presidio]   # 启用 PII 检测（基于 Microsoft Presidio）
```

### 最简配置

在项目根目录创建 `mcp.json`：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    }
  }
}
```

### 启动

```bash
# 启用基础 Token 掩码
mcp-gateway -p basic

# 启用 Token 掩码 + PII 检测
mcp-gateway -p basic -p presidio

# 调试模式
LOGLEVEL=DEBUG mcp-gateway -p basic
```

### 集成到 Cursor / Claude Desktop

<details>
<summary>Cursor 配置示例</summary>

```json
{
  "mcpServers": {
    "mcp-gateway": {
      "command": "mcp-gateway",
      "args": [
        "--mcp-json-path", "~/.cursor/mcp.json",
        "-p", "basic",
        "-p", "xetrack"
      ],
      "servers": {
        "filesystem": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
        }
      }
    }
  }
}
```
</details>

<details>
<summary>Claude Desktop 配置示例</summary>

```json
{
  "mcpServers": {
    "mcp-gateway": {
      "command": "<python-path>",
      "args": [
        "-m", "mcp_gateway.server",
        "--mcp-json-path", "<path-to-config>",
        "-p", "basic"
      ],
      "servers": {
        "filesystem": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
        }
      }
    }
  }
}
```
</details>

## 安全防护能力

### Token 掩码 (`basic` 插件)

自动识别并替换响应中的敏感凭据，支持 12 种主流云平台和开发工具的密钥格式：

| 类型 | 示例格式 |
|------|---------|
| AWS Access Key | `AKIA...` |
| GitHub Token | `ghp_...`, `gho_...` |
| Azure Client Secret | `*.azure.com` 相关 |
| GCP API Key | `AIza...` |
| JWT Token | `eyJ...` |
| HuggingFace Token | `hf_...` |
| GitLab Session Cookie | `_gitlab_session=...` |
| Slack App Token | `xapp-...` |
| Microsoft Teams Webhook | `*.webhook.office.com` |

```bash
mcp-gateway -p basic
```

### PII 检测 (`presidio` 插件)

基于 Microsoft Presidio 引擎，自动识别并匿名化文本中的个人身份信息：

- 信用卡号、IP 地址、电子邮箱
- 电话号码、身份证号（SSN）
- 更多实体类型见 [Presidio 文档](https://microsoft.github.io/presidio/supported_entities/)

```bash
pip install -e .[presidio]
mcp-gateway -p presidio
```

### 安全扫描器 (`--scan`)

启动前对所有 MCP Server 进行信誉评估和工具描述分析：

```bash
mcp-gateway --scan -p basic
```

扫描维度：
- **信誉评估** — 基于 GitHub 数据（Star、Fork、Issue 活跃度）和 NPM 下载量计算综合评分
- **工具描述扫描** — 检测隐藏的 prompt injection 指令、敏感文件路径引用、危险操作指令
- **自动阻断** — 信誉分低于阈值（默认 30 分）的 Server 会被标记为 `blocked` 并阻止加载

扫描结果会写入配置文件：

```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "blocked": "passed"
    }
  }
}
```

状态值：`"passed"` (安全) | `"blocked"` (阻断) | `"skipped"` (手动跳过) | `null` (未扫描)

## 调用追踪

### Xetrack 追踪插件

记录所有工具调用的完整上下文，支持 SQLite 和 DuckDB 查询：

```bash
pip install xetrack
mcp-gateway -p xetrack
```

环境变量配置：
- `XETRACK_DB_PATH` — SQLite 数据库路径
- `XETRACK_LOGS_PATH` — 日志文件目录

```json
{
  "mcpServers": {
    "mcp-gateway": {
      "command": "mcp-gateway",
      "args": ["--mcp-json-path", "~/.cursor/mcp.json", "-p", "xetrack"],
      "env": {
        "XETRACK_DB_PATH": "tracing.db",
        "XETRACK_LOGS_PATH": "logs/"
      }
    }
  }
}
```

查询示例：

```python
from xetrack import Reader
df = Reader("tracing.db").to_df()
```

```sql
-- DuckDB
INSTALL sqlite; LOAD sqlite; ATTACH 'tracing.db' (TYPE sqlite);
SELECT server_name, capability_name, content_text FROM db.events LIMIT 10;
```

## 代理工具

Gateway 向 LLM 暴露两个标准化工具：

| 工具 | 功能 |
|------|------|
| `get_metadata` | 获取所有已注册 MCP Server 的能力列表，帮助 LLM 选择合适的工具 |
| `run_tool` | 通过 Gateway 执行任意 MCP 工具调用，自动进行请求/响应的安全处理 |

## 插件开发

插件系统基于 ABC 基类 + 装饰器注册模式：

```python
from mcp_gateway.plugins.base import GuardrailPlugin
from mcp_gateway.plugins.manager import register_plugin

@register_plugin
class MyPlugin(GuardrailPlugin):
    @property
    def name(self) -> str:
        return "my-plugin"

    def process_request(self, context):
        # 请求方向的处理逻辑
        return context.arguments

    def process_response(self, context, response):
        # 响应方向的处理逻辑
        return response
```

插件通过 `PluginManager` 自动发现和加载，支持请求/响应双向拦截。

## 项目结构

```
mcp_gateway/
├── __init__.py              # 包入口
├── server.py                # MCP Server 生命周期管理
├── gateway.py               # 动态工具注册、CLI 参数解析
├── config.py                # 配置文件加载
├── sanitizers.py            # 请求/响应安全分发
├── plugins/
│   ├── base.py              # Plugin ABC 基类
│   ├── manager.py           # 插件发现、注册、Pipeline
│   ├── guardrails/
│   │   ├── basic.py         # Token 掩码插件
│   │   └── presidio.py      # PII 检测插件
│   └── tracing/
│       └── xetrack.py       # 调用追踪插件
├── security_scanner/
│   ├── scanner.py           # 扫描器主入口
│   ├── github_collector.py  # GitHub API 数据采集
│   ├── npm_collector.py     # NPM Registry 数据采集
│   ├── smithery_collector.py# Smithery 市场数据采集
│   ├── project_analyzer.py  # 综合信誉评分算法
│   └── tool_poisoning_analyzer.py  # 工具描述安全分析
└── tests/
    ├── test_sanitizers.py
    ├── test_tool_poisoning_analyzer.py
    ├── test_plugin_pipeline.py
    └── test_config.py
```

## License

[MIT](./LICENSE)
