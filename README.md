# Code-Mind

企业级 AI 知识管理平台，融合 RAG 检索与 MCP 协议，将项目经验沉淀为可复用的知识资产。

## 核心能力

- **混合检索**：向量、关键词、知识图谱、联网搜索并行召回，支持去重、RRF 融合与 Rerank
- **问题理解**：查询词映射、问题重写与拆分、树形意图识别和多知识库路由
- **模型与工具**：模型档位、首包探测、熔断降级，以及 MCP 工具发现、提参与校验
- **会话记忆**：最近 N 轮消息结合持久化摘要，控制 Token 成本并保留关键上下文
- **流量保护**：Redis 公平排队与分布式并发控制，避免突发请求压垮模型服务
- **知识闭环**：可编排入库 Pipeline、远程刷新、回答溯源、用户反馈、Trace 和管理后台
- **MCP Gateway**：安全过滤、插件系统、工具代理，为 AI Agent 提供安全的外部工具访问

## 项目结构

```
Code-Mind/
├── agent/              # Agent 执行架构（ReAct 模式）
├── bootstrap/          # 启动装配层
├── framework/          # 通用基础能力
├── infra-ai/           # AI 模型客户端
├── rag/                # RAG 检索与知识库管理
├── system/             # 用户认证与审计
├── mcp-server/         # MCP 工具服务
├── mcp-gateway/        # MCP 安全网关（Python）
├── frontend/           # React 前端
└── resources/          # 数据库脚本与 Docker 配置
```

## 技术栈

- 后端：Spring Boot 4.1、Sa-Token、Redis、RocketMQ、Redisson、PostgreSQL + pgvector、MyBatis-Plus
- MCP Gateway：Python、FastMCP、Guardrail 插件
- 前端：React 18 + TypeScript

## 快速启动

```bash
# 1. 启动基础服务
docker compose up -d

# 2. 初始化数据库
docker exec -i ragent-postgres psql -U postgres -d ragent < resources/database/schema_pg.sql
docker exec -i ragent-postgres psql -U postgres -d ragent < resources/database/init_data_pg.sql

# 3. 启动后端
cd bootstrap
mvn spring-boot:run -Dspring.profiles.active=local

# 4. 启动前端
cd frontend
npm install
npm run dev

# 5. 启动 MCP Gateway（可选）
cd mcp-gateway
pip install -e .
mcp-gateway --mcp-json-path mcp.json -p basic
```

## 扩展点

| 接口 | 用途 |
|:---|:---|
| `SearchChannel` | 新增检索通道 |
| `SearchResultPostProcessor` | 新增后处理步骤 |
| `McpToolExecutor` | 注册新的 MCP 工具 |
| `IngestionNode` | 在入库流水线中插入新节点 |
| `ChatClient`（infra-ai） | 接入新的模型供应商 |
| MCP Gateway 插件 | 自定义安全过滤和监控 |
