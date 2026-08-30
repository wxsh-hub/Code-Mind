# 分批 Push 计划

共 10 天，16 个 commit。按开发顺序排列，每天 1-3 个 commit。

> **执行说明**：每个 commit 对应一个独立的文件集合。执行时先按集合整理文件，确认无误后提交。
> 同一天的 commit 之间保持逻辑递进关系（骨架 → 功能 → 测试）。
>
> **提交规范**：
> - 提交概括必须使用中文
> - 提交概括中禁止包含任何表示天数的标识（如"第一天"、"Day 1"等）

---

## Day 1 — 项目初始化 + MCP 服务器骨架

**Commit 1:** `feat: initialize project structure with MCP server foundation`

文件清单：
```
pyproject.toml                          # 项目配置，依赖声明
requirements.txt                        # 依赖锁定
MANIFEST.in                             # 打包清单
.gitignore                              # 忽略规则
LICENSE                                 # MIT 许可证
mcp_gateway/__init__.py                 # 包入口，版本号
mcp_gateway/server.py                   # Server 类基础框架（start/stop 生命周期）
mcp_gateway/config.py                   # 配置文件发现与加载
README.md                               # 最简版：标题 + 一句话简介 + 安装命令
```

说明：`server.py` 此阶段只包含 `Server` 类的骨架（`__init__`、`start`、`stop`），不含 Gateway 逻辑。

---

## Day 2 — 插件架构设计

**Commit 1:** `feat: design plugin system with abstract base classes`

文件清单：
```
mcp_gateway/plugins/__init__.py
mcp_gateway/plugins/base.py             # Plugin / GuardrailPlugin / TracingPlugin ABC + PluginContext
mcp_gateway/plugins/manager.py          # @register_plugin 装饰器 + discover_plugins() + PluginManager
mcp_gateway/plugins/README.md           # 插件开发文档
```

**Commit 2:** `test: add plugin manager and context tests`

文件清单：
```
tests/__init__.py
tests/test_plugin_pipeline.py           # PluginManager 初始化、Pipeline 透传、PluginContext 构造
```

---

## Day 3 — Token 脱敏核心功能

**Commit 1:** `feat: implement basic guardrail with regex-based token masking`

文件清单：
```
mcp_gateway/plugins/guardrails/__init__.py
mcp_gateway/plugins/guardrails/basic.py # 12 种正则模式 + secret_cleaner + process_request/response
```

**Commit 2:** `feat: add sanitization dispatch layer`

文件清单：
```
mcp_gateway/sanitizers.py               # sanitize_request / sanitize_response / sanitize_tool_call_args/result
```

**Commit 3:** `test: add guardrail and sanitizer tests`

文件清单：
```
tests/test_sanitizers.py                # 11 个测试：请求/响应/资源读取/参数脱敏
```

---

## Day 4 — 网关核心：动态注册

**Commit 1:** `feat: implement gateway with dynamic tool and prompt registration`

文件清单：
```
mcp_gateway/gateway.py                  # FastMCP + inspect 动态注册 + lifespan + parse_args()
mcp_gateway/server.py                   # 补完：GatewayContext、并发能力获取、get_prompt/read_resource
```

说明：此 commit 对 `server.py` 进行增量修改，添加 Gateway 相关逻辑。`server.py` 的完整归属为 Day 1（骨架）+ Day 4（网关功能）。

**Commit 2:** `test: add config loading tests`

文件清单：
```
tests/test_config.py                    # 14 个测试：find_config_file、load_config、get_tool_params_description
```

---

## Day 5 — 安全扫描器：数据采集层

**Commit 1:** `feat: add security scanner with multi-source data collectors`

文件清单：
```
mcp_gateway/security_scanner/__init__.py
mcp_gateway/security_scanner/config.py              # URLS / Keys / MarketPlaces 常量
mcp_gateway/security_scanner/github_collector.py    # GitHub API 元数据采集
mcp_gateway/security_scanner/npm_collector.py       # NPM Registry 下载量采集
mcp_gateway/security_scanner/smithery_collector.py  # Smithery 市场页面 HTML 爬取
```

---

## Day 6 — 安全扫描器：评分 + 检测

**Commit 1:** `feat: implement reputation scoring and tool poisoning detection`

文件清单：
```
mcp_gateway/security_scanner/project_analyzer.py        # log10 归一化多因子加权评分算法
mcp_gateway/security_scanner/tool_poisoning_analyzer.py # 隐藏指令 / 敏感文件 / 危险操作正则检测
```

**Commit 2:** `feat: add scanner orchestration`

文件清单：
```
mcp_gateway/security_scanner/scanner.py                 # Scanner 类编排 + 配置文件回写 blocked 状态
```

**Commit 3:** `test: add tool poisoning analyzer tests`

文件清单：
```
tests/test_tool_poisoning_analyzer.py   # 16 个测试：隐藏指令、敏感文件、危险操作、安全描述
```

---

## Day 7 — PII 检测插件

**Commit 1:** `feat: add Presidio PII detection plugin with graceful degradation`

文件清单：
```
mcp_gateway/plugins/guardrails/presidio.py  # try-import 优雅降级 + PII 匿名化
```

---

## Day 8 — 追踪插件

**Commit 1:** `feat: add xetrack tracing plugin for tool call monitoring`

文件清单：
```
mcp_gateway/plugins/tracing/__init__.py     # try-except 导入保护（Windows 兼容）
mcp_gateway/plugins/tracing/xetrack.py      # 工具调用上下文记录 + SQLite 存储
```

---

## Day 9 — 文档完善

**Commit 1:** `docs: complete README with architecture and plugin guide`

文件清单：
```
README.md                                   # 完整版：架构图 / 安全能力表 / 插件开发 / 项目结构
docs/MCP_Flow.png                           # MCP 流程图
docs/hf_example.png                         # Token 掩码效果截图
```

---

## Day 10 — Docker + 收尾

**Commit 1:** `feat: add Docker multi-stage build`

文件清单：
```
Dockerfile                                  # 多阶段构建，支持 INSTALL_EXTRAS 参数
```

**Commit 2:** `chore: add py.typed marker and final cleanup`

文件清单：
```
mcp_gateway/py.typed                        # PEP 561 类型标记
.github/workflows/release-new-version.yml   # CI 工作流
```

---

## 每日文件归属速查

| 文件 | Day | 说明 |
|------|-----|------|
| pyproject.toml | 1 | |
| requirements.txt | 1 | |
| MANIFEST.in | 1 | |
| .gitignore | 1 | |
| LICENSE | 1 | |
| mcp_gateway/__init__.py | 1 | |
| mcp_gateway/server.py | 1, 4 | Day 1 骨架，Day 4 补完网关 |
| mcp_gateway/config.py | 1 | |
| mcp_gateway/gateway.py | 4 | |
| mcp_gateway/sanitizers.py | 3 | |
| mcp_gateway/plugins/__init__.py | 2 | |
| mcp_gateway/plugins/base.py | 2 | |
| mcp_gateway/plugins/manager.py | 2 | |
| mcp_gateway/plugins/README.md | 2 | |
| mcp_gateway/plugins/guardrails/__init__.py | 3 | |
| mcp_gateway/plugins/guardrails/basic.py | 3 | |
| mcp_gateway/plugins/guardrails/presidio.py | 7 | |
| mcp_gateway/plugins/tracing/__init__.py | 8 | |
| mcp_gateway/plugins/tracing/xetrack.py | 8 | |
| mcp_gateway/security_scanner/__init__.py | 5 | |
| mcp_gateway/security_scanner/config.py | 5 | |
| mcp_gateway/security_scanner/github_collector.py | 5 | |
| mcp_gateway/security_scanner/npm_collector.py | 5 | |
| mcp_gateway/security_scanner/smithery_collector.py | 5 | |
| mcp_gateway/security_scanner/project_analyzer.py | 6 | |
| mcp_gateway/security_scanner/tool_poisoning_analyzer.py | 6 | |
| mcp_gateway/security_scanner/scanner.py | 6 | |
| tests/__init__.py | 2 | |
| tests/test_plugin_pipeline.py | 2 | |
| tests/test_sanitizers.py | 3 | |
| tests/test_config.py | 4 | |
| tests/test_tool_poisoning_analyzer.py | 6 | |
| README.md | 1, 9 | Day 1 最简版，Day 9 完整版 |
| docs/MCP_Flow.png | 9 | |
| docs/hf_example.png | 9 | |
| Dockerfile | 10 | |
| .github/workflows/release-new-version.yml | 10 | |
| mcp_gateway/py.typed | 10 | |
