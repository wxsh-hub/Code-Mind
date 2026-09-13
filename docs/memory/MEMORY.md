# Code-Mind 项目记忆

## 项目概述

Code-Mind 是企业级 AI 知识管理平台，融合 RAG 检索与 MCP 协议，将项目经验沉淀为可复用的知识资产。

### 核心功能
- **知识存储**：按项目/模块/功能三级结构管理知识
- **语义检索**：向量检索 + 关键词检索 + 混合检索（先 LIKE 后向量）
- **矛盾检测**：自动检测反义向量，人工审核
- **置信度评分**：基于上传次数和时间的可信度评估
- **MCP 集成**：通过 MCP 协议让 AI 直接访问知识库
- **智能删除**：AI 回答时自动识别并删除过时知识

### 技术栈
- **后端**：Java 17 + Spring Boot 4.1 + MyBatis Plus
- **向量库**：PostgreSQL 16 + pgvector
- **缓存**：Redis 7
- **消息队列**：RocketMQ 5.2
- **MCP Gateway**：Python 3.10+ + FastMCP
- **前端**：React 18 + TypeScript

---

## 项目目录结构

### ragent（Java 后端 + Python MCP Gateway）
```
D:\11111111111\AAAworkAAA\ragent\
├── rag\src\main\java\com\nageoffer\ai\ragent\
│   ├── knowledge\
│   │   ├── controller\          # API 控制器
│   │   │   ├── KnowledgeChunkApiController.java  # Chunk API
│   │   │   ├── ModuleApiController.java          # 模块 CRUD
│   │   │   └── FeatureMetadataApiController.java # 功能 CRUD + 搜索
│   │   ├── dao\entity\          # 实体类
│   │   │   ├── KnowledgeChunkDO.java  # Chunk 实体（含 metadata JSONB）
│   │   │   ├── ModuleDO.java          # 模块实体
│   │   │   └── FeatureMetadataDO.java # 功能实体
│   │   └── dao\mapper\          # Mapper 接口
│   └── ...
├── mcp_gateway\                 # Python MCP Gateway
│   ├── gateway.py               # FastMCP 网关主入口
│   ├── rag_client.py            # RAG HTTP 客户端（含重试机制）
│   ├── rag_tools.py             # search_experience（向量检索+AI回答）
│   ├── memory_tools.py          # 记忆管理（含自动识别功能）
│   ├── conflict_review.py       # 矛盾审核（含智能提交）
│   ├── feature_tools.py         # 模块/功能管理
│   └── ...
├── tests\                       # 测试文件（172 个单元测试）
├── tests\scripts\               # 测试脚本
├── frontend\                    # React 前端
├── docs\memory\                 # 项目记忆文件
└── resources\database\          # 数据库脚本
```

---

## 本地服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| ragent API | http://localhost:9090/api/ragent | Java 后端 API |
| 前端 | http://localhost:5173 | React 前端 |
| PostgreSQL | localhost:5432 | 向量数据库（pgvector） |
| Redis | localhost:6379 | 缓存 |
| RocketMQ | localhost:9876 | 消息队列 |
| RustFS | localhost:9000 | 对象存储 |
| Milvus | localhost:19530 | 向量数据库（可选） |

### Docker 容器
```
ragent-postgres          # PostgreSQL + pgvector
ragent-redis             # Redis
ragent-rocketmq-namesrv  # RocketMQ Name Server
ragent-rocketmq-broker   # RocketMQ Broker
ragent-rustfs            # RustFS 对象存储
milvus-standalone        # Milvus（可选）
```

---

## 已实现功能

### F1: 向量删除 ✅
- deprecate_chunk: 标记单个向量为废弃
- batch_deprecate_chunks: 批量标记向量为废弃
- delete_by_feature_code: 按功能编号删除
- delete_by_module: 按模块删除

### F2: MCP 接口发现 ✅
- list_mcp_tools: 列出所有可用 MCP 工具

### F3: 智能检索 ✅
- search_experience: 向量检索 + AI 回答 + 自动废弃过时知识
- 混合检索：先 LIKE 后向量，兼顾速度和准确性
- 自动识别功能：根据问题自动识别相关功能和模块

### F4: 矛盾审核 ✅
- submit_conflict_for_review: AI 提交矛盾对到后台
- list_conflicts: 列出待审核矛盾对
- review_conflict: 人工审核矛盾对

### F5: 模块/功能管理 ✅
- 模块 CRUD：create_module, list_modules, delete_module
- 功能 CRUD：create_feature, list_features, delete_feature
- 功能搜索：支持分词搜索

### F6: 记忆管理 ✅
- upload_memory: 上传记忆（支持元数据）
- ask_project: 逐级降级检索（功能级→模块级→全库→向量）
- batch_upload_memories: 批量上传
- batch_delete_memories: 批量删除

### F7: 前端管理界面 ✅
- 模块管理页面
- 功能元数据标记页面
- 矛盾审核页面
- 知识库上传支持元数据

---

## MCP 工具清单（30+ 个）

### 知识检索
- search_experience(query, kb_id, top_k) - 向量检索 + AI 回答

### 记忆管理
- upload_memory(project, filename, content, feature_codes, module)
- ask_project(project, question, top_k, feature_codes, module)
- list_projects(project)
- delete_memory(project, filename)
- batch_upload_memories(project, files, feature_codes, module)
- batch_delete_memories(project, filenames)

### 模块管理
- create_module(project, name, description)
- list_modules(project)
- delete_module(project, name)

### 功能管理
- create_feature(project, code, name, module, description)
- list_features(project, module)
- delete_feature(project, code)

### 矛盾审核
- submit_conflict_for_review(project, chunk_a_id, chunk_b_id, reason, ai_analysis)
- list_conflicts(project, kb_id, page, page_size)
- review_conflict(project, chunk_a_id, chunk_b_id, winner, reason)

### 向量管理
- deprecate_chunk(chunk_id)
- batch_deprecate_chunks(chunk_ids)

---

## 检索流程

### search_experience（推荐）
```
用户提问
    ↓
rag_chat_with_sources（向量检索 + AI 回答）
    ↓
AI 判断是否过时
    ↓
┌─────────────────────────────────────┐
│ 包含过时信息？→ 自动废弃           │
│ 正常？       → 返回 AI 回答        │
└─────────────────────────────────────┘
```

### ask_project（逐级降级）
```
用户提问
    ↓
自动识别功能（搜索功能元数据）
    ↓
功能级检索（LIKE）→ 有结果？→ 返回
    ↓ 无结果
模块级检索（LIKE）→ 有结果？→ 返回
    ↓ 无结果
全库检索（LIKE）→ 有结果？→ 返回
    ↓ 无结果
向量检索（rag_chat）→ 返回
```

---

## 测试状态

### 单元测试（172 个）
```
172 passed in 8.39s
```

### 混合检索测试（19 个）
```
自动识别功能: 5/5 通过
LIKE 检索: 5/5 通过
向量检索: 5/5 通过
混合检索: 4/4 通过
总计: 19/19 通过 (100%)
```

### Playwright 前端测试（6 个）
```
登录: PASS
页面导航: PASS (16/16)
模块管理: PASS
功能元数据: PASS
矛盾审核: PASS
知识库: PASS
总计: 6/6 通过
```

---

## 重要修复记录

### 2026-08-30: JSONB 存储修复
- KnowledgeChunkDO 添加 @TableField(typeHandler = JsonbTypeHandler.class)
- KnowledgeChunkMapper 添加 updateByNativeSql 原生 SQL 方法
- 修复 chunk metadata 无法存储的问题

### 2026-08-30: 搜索接口修复
- 修复 JSONB 查询语法（featureCodes 过滤）
- 添加功能元数据搜索接口（分词搜索）

### 2026-08-30: 混合检索实现
- ask_project 支持先 LIKE 后向量的混合检索
- LIKE 无结果时自动降级到向量检索

### 2026-08-30: 智能删除过时知识
- search_experience 自动检测过时知识
- AI 回答中提到"过时"时自动废弃对应 chunk

### 2026-08-30: 前端功能完善
- 添加模块管理页面
- 添加功能元数据标记页面
- 添加矛盾审核页面
- 知识库上传支持元数据（下拉框选择）

---

## 已知问题

1. **模块/功能 API 返回格式不一致**：部分接口返回 B000001 错误码
2. **SSE 认证失败时错误格式**：已修复，SSE 请求返回正确的错误事件
3. **Milvus 未启动**：当前使用 pgvector，Milvus 可选

---

## 启动命令

### 启动 Docker 服务
```bash
cd D:\11111111111\AAAworkAAA\ragent
docker-compose up -d
```

### 启动 ragent
```bash
cd D:\11111111111\AAAworkAAA\ragent\bootstrap
java -jar target/bootstrap-0.0.1-SNAPSHOT.jar --spring.profiles.active=local
```

### 启动前端
```bash
cd D:\11111111111\AAAworkAAA\ragent\frontend
npm install
npm run dev
```

### 运行测试
```bash
cd D:\11111111111\AAAworkAAA\ragent
python -m pytest tests/test_memory_tools.py tests/test_conflict_review.py tests/test_rag_tools.py -v
```

---

## Git 仓库

- **地址**：git@github.com:wxsh-hub/Code-Mind.git
- **分支**：main
- **最新提交**：feat: 智能删除过时知识、前端功能完善

---

## 重要提醒

### AI 开发规范
1. **先读记忆**：开发前先读取 `docs/memory/` 下的记忆文件
2. **更新记忆**：完成开发后更新相关记忆文件
3. **运行测试**：每次改动后运行测试确认
4. **提交规范**：使用 `feat:`, `fix:`, `docs:` 等前缀

### 测试要求
1. 单元测试必须全部通过（172 个）
2. 混合检索测试必须全部通过（19 个）
3. 新功能必须有对应测试

### 文件位置
- 项目根目录：`D:\11111111111\AAAworkAAA\ragent\`
- MCP Gateway：`D:\11111111111\AAAworkAAA\ragent\mcp_gateway\`
- 测试文件：`D:\11111111111\AAAworkAAA\ragent\tests\`
- 前端：`D:\11111111111\AAAworkAAA\ragent\frontend\`
- 数据库迁移：`D:\11111111111\AAAworkAAA\ragent\resources\database\`
