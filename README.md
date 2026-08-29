# Code-Mind

企业级 AI 知识管理平台，规范管理企业代码系统知识库。

## 核心功能

| 功能 | 说明 |
|------|------|
| 知识存储 | 按项目/模块/功能三级结构管理知识 |
| 语义检索 | 向量检索 + 逐级降级（功能→模块→全库） |
| 矛盾检测 | 自动检测反义向量，人工审核 |
| 置信度评分 | 基于上传次数和时间的可信度评估 |
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
cd D:\11111111111\AAAworkAAA\ragent
docker-compose up -d
```

启动服务：
- PostgreSQL + pgvector (localhost:5432)
- Redis (localhost:6379)
- RocketMQ (localhost:9876)

### 2. 启动 ragent

```bash
cd D:\11111111111\AAAworkAAA\ragent
./mvnw spring-boot:run -pl bootstrap
```

API 地址：http://localhost:9090/api/ragent

### 3. 运行测试

```bash
# MCP Gateway 单元测试
cd D:\11111111111\AAAworkAAA\mcp-gateway
python -m pytest tests/ -v

# 集成测试
bash test_final.sh
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

## MCP 工具（28 个）

### 模块管理
```python
create_module(project, name, description)
list_modules(project)
delete_module(project, name)
```

### 功能管理
```python
create_feature(project, code, name, module, description)
list_features(project, module)
delete_feature(project, code)
```

### 记忆管理
```python
upload_memory(project, filename, content, feature_codes, module)
ask_project(project, question, top_k, feature_codes, module)
list_projects(project)
delete_memory(project, filename)
```

### 技能管理
```python
upload_skill(project, skill_name, content, category, tags)
search_skill(project, task_description, top_k, category)
list_skills(project)
get_skill(project, skill_name, category)
delete_skill(project, skill_name, category)
```

### 向量管理
```python
delete_vector(project, chunk_id, find_similar, similarity_threshold)
delete_vectors(project, chunk_ids, find_similar, similarity_threshold)
```

### 矛盾审核
```python
list_conflicts(project, kb_id, confidence_threshold)
review_conflict(project, chunk_a_id, chunk_b_id, winner, reason)
```

### 系统信息
```python
list_mcp_tools(categorized)
```

## 使用示例

### 初始化项目

```python
# 创建模块
create_module(project="MyApp", name="user", description="用户管理模块")

# 创建功能
create_feature(
    project="MyApp",
    code="1001",
    name="用户注册",
    module="user",
    description="用户注册功能"
)
```

### 上传知识

```python
# 上传技能
upload_skill(
    project="MyApp",
    skill_name="用户注册指南",
    content="...",
    category="coding",
    feature_codes=["1001"],
    module="user"
)

# 上传记忆
upload_memory(
    project="MyApp",
    filename="1001_用户注册.md",
    content="...",
    feature_codes=["1001"],
    module="user"
)
```

### 查询知识

```python
# 逐级降级检索
result = ask_project(
    project="MyApp",
    question="如何实现用户注册",
    feature_codes=["1001"],
    module="user"
)
# 检索顺序：功能级 → 模块级 → 全库
```

### 删除错误知识

```python
# 删除错误向量及相似向量
delete_vector(
    project="MyApp",
    chunk_id="错误向量ID",
    find_similar=True,
    similarity_threshold=0.8
)
```

## 目录结构

```
Code-Mind/
├── mcp_gateway/                # Python MCP 网关
│   ├── mcp_gateway/            # 源码
│   │   ├── gateway.py          # 网关主入口
│   │   ├── rag_client.py       # RAG 客户端
│   │   ├── memory_tools.py     # 记忆管理
│   │   ├── skill_tools.py      # 技能管理
│   │   ├── feature_tools.py    # 功能管理
│   │   ├── vector_delete.py    # 向量删除
│   │   └── conflict_review.py  # 矛盾审核
│   ├── tests/                  # 测试文件
│   └── docs/                   # 文档
├── rag/                        # Java RAG 模块
│   └── src/main/java/.../
│       ├── knowledge/controller/  # API 控制器
│       └── knowledge/dao/         # 实体和 Mapper
├── agent/                      # Java Agent 模块
└── docs/                       # 项目文档
```

## 测试

| 测试类型 | 数量 | 状态 |
|----------|------|------|
| 单元测试 | 181 | ✅ 通过 |
| 集成测试 | 28 | ✅ 通过 |

## 文档

| 文档 | 说明 |
|------|------|
| docs/HELP_SYSTEM.md | 完整使用指南 |
| docs/SUBMISSION_STANDARDS.md | 提交规范 |
| docs/FEATURE_PLAN.md | 功能计划 |
| docs/memory/ | 项目记忆文件 |

## 已知问题

1. **中文 LIKE 检索不准确**：使用向量检索替代
2. **RocketMQ 编码问题**：中文内容可能乱码

## Git

- **仓库**：git@github.com:wxsh-hub/Code-Mind.git
- **分支**：main
- **提交**：使用 SSH 方式

## 许可证

MIT
