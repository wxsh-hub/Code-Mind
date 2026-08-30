# Code-Mind

企业级 AI 知识管理平台，规范管理企业代码系统知识库。

## 目录结构

| 目录 | 说明 |
|------|------|
| `agent/` | AI Agent 引擎（会话管理、工具调用、记忆压缩） |
| `rag/` | RAG 检索引擎（向量检索、知识入库、意图识别） |
| `framework/` | 公共框架（异常处理、敏感数据脱敏、幂等、验证） |
| `infra-ai/` | AI 基础设施（LLM 路由、Embedding、模型选择） |
| `mcp_gateway/` | MCP 协议网关（Python，工具注册、插件管线） |
| `bootstrap/` | Spring Boot 启动入口 |
| `frontend/` | 前端页面 |
| `tests/` | Python 测试（单元测试 + 集成脚本） |
| `docs/` | 项目文档（规划、指南、记忆） |
| `resources/` | 资源文件（数据库初始化、Docker 配置） |
| `skills/` | Skill 存储 |
| `system/` | 系统配置 |

## 核心功能

| 功能 | 说明 |
|------|------|
| 知识存储 | 按项目/模块/功能三级结构管理知识 |
| 语义检索 | 向量检索 + 逐级降级（功能→模块→全库） |
| 矛盾检测 | 自动检测反义向量，人工审核 |
| 置信度评分 | 基于上传次数和时间的可信度评估 |
| 敏感数据过滤 | 入库阶段自动替换密钥、Token、PII |
| MCP 集成 | AI 通过 MCP 协议直接访问知识库 |
| 向量管理 | 删除错误向量及相似向量 |

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Java 17 + Spring Boot + MyBatis Plus |
| MCP Gateway | Python 3.10+ + FastMCP |
| 向量库 | PostgreSQL + pgvector |
| 缓存 | Redis |
| 消息队列 | RocketMQ |

## 快速开始

### 1. 启动依赖服务

```bash
docker-compose up -d
```

启动服务：
- PostgreSQL + pgvector (localhost:5432)
- Redis (localhost:6379)
- RocketMQ (localhost:9876)

### 2. 启动 ragent

```bash
./mvnw spring-boot:run -pl bootstrap
```

API 地址：http://localhost:9090/api/ragent

### 3. 运行测试

```bash
# Python 单元测试
python -m pytest tests/ -v

# Java 单元测试
mvn test

# 集成测试
bash tests/scripts/test_final.sh
```

## 项目架构

```
┌─────────────────────────────────────────────────────────┐
│                      AI Agent                           │
│                  （MCP 协议访问）                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  MCP Gateway (Python)                    │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  │模块管理│ │功能管理│ │记忆管理│ │技能管理│          │
│  └────────┘ └────────┘ └────────┘ └────────┘          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  │知识检索│ │向量删除│ │矛盾审核│ │系统信息│          │
│  └────────┘ └────────┘ └────────┘ └────────┘          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    ragent (Java)                         │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  │模块API │ │功能API │ │ChunkAPI│ │ RAG API│          │
│  └────────┘ └────────┘ └────────┘ └────────┘          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  │PostgreSQL│ │ Redis  │ │RocketMQ│ │ RustFS │          │
│  │(pgvector)│ │        │ │        │ │        │          │
│  └────────┘ └────────┘ └────────┘ └────────┘          │
└─────────────────────────────────────────────────────────┘
```

## MCP 工具

共 28 个 MCP 工具，详见 [docs/HELP_SYSTEM.md](docs/HELP_SYSTEM.md)。

| 分类 | 工具 |
|------|------|
| 模块管理 | create_module, list_modules, delete_module |
| 功能管理 | create_feature, list_features, delete_feature, search_features |
| 记忆管理 | upload_memory, ask_project, list_projects, delete_memory |
| 技能管理 | upload_skill, search_skill, list_skills, get_skill, delete_skill |
| 向量管理 | delete_vector, delete_vectors |
| 矛盾审核 | list_conflicts, review_conflict |
| 系统信息 | list_mcp_tools |

## 文档

| 文档 | 说明 |
|------|------|
| [docs/HELP_SYSTEM.md](docs/HELP_SYSTEM.md) | 完整使用指南 |
| [docs/FEATURES.md](docs/FEATURES.md) | 功能清单 |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | 用户指南 |
| [docs/memory/](docs/memory/) | 项目记忆文件 |

## 许可证

MIT
