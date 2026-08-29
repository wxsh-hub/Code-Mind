# Code-Mind 项目规范

## 一、文件组织

### 1.1 目录结构

```
Code-Mind/
├── rag/                          # RAG 核心（Java）
├── agent/                        # Agent 执行架构
├── framework/                    # 通用基础能力
├── infra-ai/                     # AI 模型客户端
├── system/                       # 用户认证
├── mcp-server/                   # MCP 工具服务
├── mcp-gateway/                  # MCP 安全网关（Python）
├── frontend/                     # React 前端
├── resources/
│   ├── database/
│   │   ├── schema_pg.sql         # 主表结构
│   │   ├── init_data_pg.sql      # 初始数据
│   │   └── upgrades/             # 增量迁移脚本（按版本号）
│   │       └── v2.1.0/
│   │           └── 260829_xxx.sql
│   └── docker/                   # Docker Compose 文件
├── docs/
│   ├── conventions/              # 项目规范（本目录）
│   │   ├── PROJECT_RULES.md      # 项目规范
│   │   └── TEST_GUIDE.md         # 测试指南
│   ├── memory/                   # 项目长期记忆
│   │   └── MEMORY.md             # 项目记忆索引
│   ├── design/                   # 设计文档
│   │   ├── RAGENT_PART.md        # rag 端改造方案
│   │   └── MCP_GATEWAY_PART.md   # mcp-gateway 端改造方案
│   └── releases/                 # 版本发布说明
├── test_rag_flow.sh              # RAG 全流程测试
└── test_chunk_api.sh             # Chunk API 测试
```

### 1.2 测试脚本位置

| 项目 | 测试位置 | 说明 |
|------|----------|------|
| rag (Java) | `rag/src/test/java/...` | JUnit 单元测试 |
| rag (集成) | 项目根目录 `test_*.sh` | Shell 集成测试脚本 |
| mcp-gateway (Python) | `mcp-gateway/tests/` | pytest 测试 |
| mcp-gateway (集成) | `mcp-gateway/tests/test_*_integration.py` | 集成测试 |

### 1.3 文件行数限制

**单个文件不超过 1000 行。** 超过时按以下规则拆分：

| 文件类型 | 拆分策略 |
|----------|----------|
| Java Controller | 按资源拆分（如 `KnowledgeChunkController` + `KnowledgeChunkApiController`） |
| Java Service | 按职责拆分（如 `KnowledgeBaseService` + `KnowledgeDocumentService`） |
| Java Entity | 不拆分，保持单一实体 |
| Python 模块 | 按功能拆分（如 `collector/`、`conflict/`、`plugins/`） |
| SQL 脚本 | 按版本号拆分（`upgrades/v2.1.0/`） |
| 前端组件 | 按页面/功能拆分 |
| 测试文件 | 按模块拆分，每个测试文件对应一个源文件 |

---

## 二、开发流程

### 2.1 开发节奏

```
需求分析 → 设计 → 编码 → 写测试 → 运行测试 → 更新记忆 → 提交
```

**每完成一个功能模块：**
1. ✅ 编写对应测试脚本
2. ✅ 运行该模块测试，确保通过
3. ✅ 运行已有测试，确保不破坏现有功能
4. ✅ 更新 `docs/memory/MEMORY.md`
5. ✅ 提交代码

### 2.2 测试验收标准

**所有测试必须通过才能验收：**

```bash
# rag 端测试
bash test_rag_flow.sh       # RAG 全流程：8 项
bash test_chunk_api.sh      # Chunk API：12 项

# mcp-gateway 端测试
cd mcp-gateway && pytest tests/ -v
```

### 2.3 测试脚本编写规范

每个测试脚本必须包含：

```bash
#!/bin/bash
# 测试 XXX 模块
# 依赖：ragent 服务运行中

BASE_URL="http://localhost:9090/api/ragent"
PASS=0
FAIL=0

check() {
    local name="$1"
    local actual="$2"
    local expected="$3"
    if echo "$actual" | grep -q "$expected"; then
        echo "  ✅ $name"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $name (expected: $expected)"
        echo "     got: $actual"
        FAIL=$((FAIL + 1))
    fi
}

# 测试逻辑...

echo "=========================================="
echo "  结果: $PASS 通过, $FAIL 失败"
echo "=========================================="
exit $FAIL
```

---

## 三、记忆管理

### 3.1 记忆文件位置

- **索引文件**：`docs/memory/MEMORY.md`
- **详细记忆**：`docs/memory/` 下按主题分文件

### 3.2 记忆更新规则

每完成一个功能模块，必须更新记忆：

1. 更新 `MEMORY.md` 索引（添加一行摘要）
2. 如有重大设计决策，创建详细记忆文件

### 3.3 记忆文件格式

```markdown
# [主题名称]

## 状态
- 完成度：XX%
- 最后更新：YYYY-MM-DD

## 关键决策
- 决策1：原因
- 决策2：原因

## 已知问题
- 问题1：解决方案
- 问题2：待解决

## 相关文件
- `path/to/file1.java`
- `path/to/file2.py`
```

---

## 四、提交规范

### 4.1 Commit 消息格式

```
<类型>(<范围>): <简短描述>

<详细描述（可选）>
```

### 4.2 类型

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 4.3 范围

- `rag`: RAG 核心模块
- `agent`: Agent 模块
- `mcp-gateway`: MCP 网关
- `frontend`: 前端
- `infra`: 基础设施

### 4.4 示例

```
feat(rag): 新增相似检索 API
test(chunk-api): 添加引用计数测试
docs(memory): 更新项目记忆
```
