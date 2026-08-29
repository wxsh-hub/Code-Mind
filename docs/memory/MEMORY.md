# Code-Mind 项目记忆

## 项目概述

Code-Mind 是企业级 AI 知识管理平台，融合 RAG 检索与 MCP 协议，将项目经验沉淀为可复用的知识资产。

### 核心功能
- **知识存储**：按项目/模块/功能三级结构管理知识
- **语义检索**：向量检索 + 关键词检索 + 逐级降级
- **矛盾检测**：自动检测反义向量，人工审核
- **置信度评分**：基于上传次数和时间的可信度评估
- **MCP 集成**：通过 MCP 协议让 AI 直接访问知识库

### 技术栈
- **后端**：Java 17 + Spring Boot + MyBatis Plus
- **向量库**：PostgreSQL + pgvector
- **缓存**：Redis
- **消息队列**：RocketMQ
- **MCP Gateway**：Python 3.10+ + FastMCP

---

## 项目目录结构

### ragent（Java 后端）
```
D:\11111111111\AAAworkAAA\ragent\
├── rag\src\main\java\com\nageoffer\ai\ragent\
│   ├── knowledge\
│   │   ├── controller\          # API 控制器
│   │   │   ├── KnowledgeChunkApiController.java  # Chunk API（相似检索、引用计数）
│   │   │   ├── ModuleApiController.java          # 模块 CRUD
│   │   │   └── FeatureMetadataApiController.java # 功能 CRUD
│   │   ├── dao\entity\          # 实体类
│   │   │   ├── KnowledgeChunkDO.java  # Chunk 实体（含 metadata JSONB）
│   │   │   ├── ModuleDO.java          # 模块实体
│   │   │   └── FeatureMetadataDO.java # 功能实体
│   │   └── dao\mapper\          # Mapper 接口
│   └── ...
├── resources\database\upgrades\ # 数据库迁移脚本
│   └── v2.1.0\
│       ├── 260829_chunk_metadata.sql    # Chunk 元数据扩展
│       ├── 260829_chunk_confidence.sql  # 置信度字段
│       └── 260829_module_feature.sql    # 模块和功能表
├── docs\memory\                 # 项目记忆文件
└── test_rag_flow.sh             # RAG 测试脚本
```

### mcp-gateway（Python MCP 网关）
```
D:\11111111111\AAAworkAAA\mcp-gateway\
├── mcp_gateway\
│   ├── gateway.py               # FastMCP 网关主入口
│   ├── rag_client.py            # RAG HTTP 客户端
│   ├── rag_tools.py             # search_experience MCP Tool
│   ├── memory_tools.py          # 记忆管理 MCP Tools
│   ├── skill_tools.py           # 技能管理 MCP Tools
│   ├── feature_tools.py         # 模块/功能管理 MCP Tools
│   ├── discovery_tools.py       # list_mcp_tools
│   ├── conflict_review.py       # 矛盾审核 MCP Tools
│   ├── vector_delete.py         # 向量删除 MCP Tools
│   ├── path_resolver.py         # 路径引用解析
│   ├── collector\               # GitLab/GitHub 采集模块
│   │   ├── gitlab_fetcher.py
│   │   ├── github_fetcher.py
│   │   ├── slimmer.py           # 内容瘦身
│   │   ├── metadata_extractor.py
│   │   ├── ingest_client.py
│   │   └── scheduler.py
│   └── conflict\                # 矛盾检测模块
│       ├── detector.py
│       ├── resolver.py
│       ├── voter.py
│       └── aware_search.py
├── tests\                       # 测试文件
│   ├── test_rag_client.py
│   ├── test_rag_tools.py
│   ├── test_memory_tools.py
│   ├── test_skill_tools.py
│   ├── test_feature_tools.py
│   ├── test_discovery_tools.py
│   ├── test_conflict_review.py
│   ├── test_vector_delete.py
│   ├── test_collector.py
│   ├── test_conflict.py
│   ├── test_path_resolver.py
│   └── test_github_fetcher.py
├── test_data\                   # 测试知识文件
│   ├── 编码规范_Java.md
│   ├── 编码规范_数据库.md
│   ├── 编码规范_Git.md
│   ├── 项目经验_分页实现.md
│   ├── 项目经验_缓存设计.md
│   ├── 架构设计_微服务.md
│   └── 架构设计_数据库.md
├── docs\                        # 文档
│   ├── FEATURE_PLAN.md          # 功能计划
│   ├── HELP_SYSTEM.md           # 帮助文档
│   ├── SUBMISSION_STANDARDS.md  # 提交规范
│   └── plans\                   # 详细计划
└── test_final.sh                # 集成测试脚本
```

---

## 本地服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| ragent API | http://localhost:9090/api/ragent | Java 后端 API |
| PostgreSQL | localhost:5432 | 向量数据库（pgvector） |
| Redis | localhost:6379 | 缓存 |
| RocketMQ | localhost:9876 | 消息队列 |
| RustFS | localhost:9000 | 对象存储 |

### Docker 容器
```
ragent-postgres      # PostgreSQL + pgvector
ragent-redis         # Redis
ragent-rocketmq-namesrv  # RocketMQ Name Server
ragent-rocketmq-broker   # RocketMQ Broker
ragent-rustfs        # RustFS 对象存储
```

---

## 已实现功能

### F1: 向量删除 ✅
- delete_vector: 删除单个向量及相似向量
- delete_vectors: 批量删除向量
- delete_by_feature_code: 按功能编号删除
- delete_by_module: 按模块删除

### F2: MCP 接口发现 ✅
- list_mcp_tools: 列出所有可用 MCP 工具（按分类分组）

### F3: 提交规范文档 ✅
- docs/SUBMISSION_STANDARDS.md: Skills 和记忆的提交规范

### F5: 矛盾审核后台 ✅
- list_conflicts: 列出待审核的矛盾对
- review_conflict: 审核矛盾对（选择 a/b/both）

### F6: 帮助文档系统 ✅
- docs/HELP_SYSTEM.md: 完整使用指南

### F7: 元数据标记系统 ✅
- 模块管理：create_module, list_modules, delete_module
- 功能管理：create_feature, list_features, delete_feature
- 向量元数据：JSONB 字段（feature_codes, module）
- 逐级降级检索：功能级 → 模块级 → 全库
- 置信度评分：upload_count, last_upload, days_old

---

## MCP 工具清单（28 个）

### 模块管理
- create_module(project, name, description)
- list_modules(project)
- delete_module(project, name)

### 功能管理
- create_feature(project, code, name, module, description)
- list_features(project, module)
- delete_feature(project, code)

### 记忆管理
- upload_memory(project, filename, content, feature_codes, module)
- ask_project(project, question, top_k, feature_codes, module)
- list_projects(project)
- delete_memory(project, filename)

### 技能管理
- upload_skill(project, skill_name, content, category, tags, description, author)
- search_skill(project, task_description, top_k, category)
- list_skills(project)
- get_skill(project, skill_name, category)
- delete_skill(project, skill_name, category)

### 知识检索
- search_experience(query, kb_id, top_k)

### 向量管理
- delete_vector(project, chunk_id, find_similar, similarity_threshold)
- delete_vectors(project, chunk_ids, find_similar, similarity_threshold)

### 矛盾审核
- list_conflicts(project, kb_id, confidence_threshold)
- review_conflict(project, chunk_a_id, chunk_b_id, winner, reason)

### 系统信息
- list_mcp_tools(categorized)

---

## 数据库表结构

### t_knowledge_chunk（知识分块表）
- id, kb_id, doc_id, content, content_hash
- metadata (JSONB): {"feature_codes": ["2437"], "module": "user"}
- upload_count, last_upload_at, confidence
- vote_count, conflict_pair_id, deprecated

### t_module（模块表）
- id, name, description, created_by, created_at

### t_feature_metadata（功能元数据表）
- id, feature_code, feature_name, module_name, description, status

---

## 测试状态

### 单元测试
```
181 passed in 7.45s
```

### 集成测试
```
28/28 通过
- 登录认证
- 创建知识库
- 上传 7 个文档
- 分块向量化
- 相似检索
- 引用计数
- RAG 问答
```

---

## 启动命令

### 启动 Docker 服务
```bash
cd D:\11111111111\AAAworkAAA\ragent
docker-compose up -d
```

### 启动 ragent
```bash
cd D:\11111111111\AAAworkAAA\ragent
./mvnw spring-boot:run -pl bootstrap
```

### 运行 MCP Gateway 测试
```bash
cd D:\11111111111\AAAworkAAA\mcp-gateway
python -m pytest tests/ -v
```

### 运行集成测试
```bash
cd D:\11111111111\AAAworkAAA\mcp-gateway
bash test_final.sh
```

---

## Git 仓库

- **地址**：git@github.com:wxsh-hub/Code-Mind.git
- **分支**：main
- **结构**：
  ```
  Code-Mind/
  ├── mcp_gateway/    # Python MCP 网关
  ├── rag/            # Java RAG 模块
  ├── agent/          # Java Agent 模块
  ├── docs/           # 文档
  └── ...
  ```

---

## 已知问题

1. **中文 LIKE 检索不准确**：KnowledgeChunkApiController 使用 LIKE 检索中文内容时可能不准确，建议使用向量检索
2. **RocketMQ 编码问题**：通过 RocketMQ 传输的中文内容可能乱码
3. **Milvus 未启动**：当前使用 pgvector，Milvus 容器未启动

---

## 下一步计划

1. **向量检索优化**：将 LIKE 检索改为真正的向量检索
2. **知识快照功能**：按功能生成本地知识快照，减少网络请求
3. **前端管理界面**：添加模块/功能/向量的管理界面
4. **GitLab/GitHub 集成**：自动采集仓库中的文档

---

## 重要提醒

### AI 开发规范
1. **先读记忆**：开发前先读取 `docs/memory/` 下的记忆文件
2. **更新记忆**：完成开发后更新相关记忆文件
3. **运行测试**：每次改动后运行测试确认
4. **提交规范**：使用 `feat:`, `fix:`, `docs:` 等前缀

### 测试要求
1. 单元测试必须全部通过
2. 集成测试必须全部通过
3. 新功能必须有对应测试

### 文件位置
- ragent 记忆：`D:\11111111111\AAAworkAAA\ragent\docs\memory\`
- mcp-gateway 测试：`D:\11111111111\AAAworkAAA\mcp-gateway\tests\`
- 数据库迁移：`D:\11111111111\AAAworkAAA\ragent\resources\database\upgrades\`
