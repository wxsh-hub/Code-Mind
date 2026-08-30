# MCP 安全网关 — 简历项目指南

## 项目简介

基于 Model Context Protocol (MCP) 的安全代理网关，为 LLM 工具调用提供统一的安全防护层。

**技术栈：** Python 3.10+ / FastMCP / Docker / pytest

---

## 我做了什么（面试话术）

### 一、核心架构设计

> "我设计了一个插件化的安全网关架构，核心是 **ABC 抽象基类 + 装饰器自动注册 + 插件管线** 三个层次。"

**技术细节：**
- `Plugin` → `GuardrailPlugin` / `TracingPlugin` 抽象继承体系，定义了统一的 `process_request` / `process_response` 接口
- `@register_plugin` 装饰器实现插件自动发现和注册，新增插件零配置
- `PluginManager` 负责插件管线编排，支持链式调用、阻断、错误降级

**面试可以展开讲：**
- 为什么用 ABC 而不是 Protocol？→ 因为需要强制子类实现特定方法，ABC 的 `@abstractmethod` 提供编译时约束
- 插件注册机制怎么实现的？→ Python 的 `__init_subclass__` + 装饰器模式，`discover_plugins()` 触发模块导入时自动注册
- 管线怎么处理错误？→ 请求阶段错误直接阻断（返回 None），响应阶段错误降级返回原始数据

### 二、安全扫描器 — 多因子信誉评分系统

> "我实现了一个 MCP 服务器安全扫描器，集成 GitHub、NPM、Smithery 三个数据源，使用对数归一化的多因子加权算法计算信誉分数。"

**技术细节：**
- 三个数据采集器（`GithubFetcher`、`NPMCollector`、`SmitheryFetcher`）独立实现，通过 `ProjectAnalyzer` 统一编排
- 评分算法：`log10(x+1)` 归一化 → 多因子加权（Owner/Repo/Source） → 0-100 分制
- 阈值 < 30 自动阻断，结果写回配置文件

**面试可以展开讲：**
- 为什么用对数归一化？→ GitHub stars 等数据分布极度右偏（少数项目有几万 star，多数只有个位数），线性归一化会失效
- 怎么处理数据缺失？→ 缺失项给 0 分，不影响其他因子的计算
- Smithery 的 HTML 爬虫有什么风险？→ CSS 选择器依赖前端结构，会随网站改版失效，可以加 fallback 或迁移到 API

### 三、工具投毒检测

> "我实现了 tool poisoning 检测，通过正则匹配分析 MCP 工具描述中是否包含隐藏指令、敏感文件引用和危险操作。"

**技术细节：**
- 三类模式：hidden instructions（prompt injection）、sensitive files（.env、id_rsa）、sensitive actions（shell exec、privilege escalation）
- 预编译正则 + `re.IGNORECASE`，支持捕获组提取匹配内容
- 扫描结果集成到 `Scanner.scan_server_tools()`，自动阻断有风险的 MCP 服务器

**面试可以展开讲：**
- 什么是 tool poisoning？→ 攻击者在 MCP 工具描述中注入隐藏指令，诱导 LLM 执行恶意操作（如泄露 API key、执行系统命令）
- 为什么用正则而不是 LLM？→ 正则确定性强、零延迟、无额外成本，适合已知模式匹配；LLM 适合检测更隐蔽的语义攻击
- 还有什么可以改进？→ 加入语义相似度检测、支持自定义规则、集成第三方威胁情报

### 四、Token 脱敏与 PII 检测

> "我实现了两层安全护栏：basic 插件用正则做 token 脱敏（GitHub/AWS/JWT 等），presidio 插件集成微软 Presidio 做 PII 检测（信用卡/邮箱/SSN 等）。"

**技术细节：**
- `BasicGuardrailPlugin`：12 种预编译正则模式，覆盖 Azure/GCP/AWS/GitHub/JWT/Slack 等
- `PresidioGuardrailPlugin`：可选依赖，`try-import` 优雅降级
- 两者都处理 `CallToolResult`、`GetPromptResult`、资源读取三种响应类型
- 不可变性：只在内容变化时创建新对象，否则返回原始引用

---

## 代码质量改进（我做的优化）

| 改进项 | 说明 |
|--------|------|
| 修复 `GetewayContext` 全局拼写错误 | 重命名为 `GatewayContext`，跨 3 个文件 |
| 消除裸 `except:` | 改为 `except Exception:`，避免捕获 SystemExit |
| 删除 5 个文件的 `if __name__` 块 | 清理临时测试脚本和 `print()` 语句 |
| 删除注释掉的代码块 | 清理 "Option 2/3" 开发笔记和 "# Removed X" 提交残留 |
| 统一日志调用 | 将 `logging.debug/info` 统一为模块级 `logger.debug/info` |
| 修正日志级别 | 成功操作从 `warning` 降为 `info`，高频操作从 `info` 降为 `debug` |
| 实现 `process_request` | 原本是空壳（只 log 不处理），现在真正遍历参数做脱敏/PII 匿名化 |
| 移除废弃 CLI 参数 | 删除 `--enable-guardrails` 和 `--enable-tracing` |
| 修正 docstring | 修复返回类型描述与实际不符的问题 |

---

## 新增测试覆盖

| 测试文件 | 覆盖内容 | 测试数 |
|----------|----------|--------|
| `test_sanitizers.py` | 请求/响应脱敏分发层、错误降级、类型校验 | 12 |
| `test_tool_poisoning_analyzer.py` | 隐藏指令检测、敏感文件检测、危险操作检测、安全描述验证 | 16 |
| `test_plugin_pipeline.py` | 插件管线透传、PluginContext 创建/序列化/替换 | 8 |
| `test_config.py` | 配置文件查找、JSON 解析、参数提取、边界情况 | 12 |

---

## 面试常见问题准备

### Q: 为什么选择插件架构而不是中间件模式？
> 插件架构允许独立开发和测试每个安全策略，新增插件不需要修改核心代码。中间件模式适合线性处理链，但我们的需求是请求和响应阶段可能需要不同的处理逻辑。

### Q: 怎么保证插件的执行顺序？
> 当前按注册顺序执行。如果需要优先级，可以给插件加 `priority` 属性，在 `PluginManager` 初始化时排序。

### Q: 安全扫描器的误报怎么处理？
> 配置文件支持 `"blocked": "skipped"` 手动跳过。未来可以加白名单机制和置信度阈值。

### Q: 怎么处理高并发场景？
> MCP Gateway 本身是异步的（`asyncio`），工具调用通过 `asyncio.gather` 并发执行。瓶颈在下游 MCP 服务器的响应速度。

### Q: 有什么可以改进的？
> 1. 配置校验（JSON Schema）防止格式错误
> 2. GitHub API Token 支持避免 rate limit
> 3. 异步 HTTP 替换同步 requests
> 4. 插件热加载
> 5. 更完善的测试覆盖率（当前重点模块已覆盖，边界情况可继续补充）
