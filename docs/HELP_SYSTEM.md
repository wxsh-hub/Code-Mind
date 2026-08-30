# Code-Mind 使用指南

## 系统简介

Code-Mind 是企业级 AI 知识管理平台，支持：
- **项目记忆管理**：状态、经验、决策
- **技能存储**：代码规范、操作指南
- **知识检索**：向量检索 + AI 回答
- **矛盾检测**：自动检测反义向量，人工审核
- **智能删除**：AI 判断过时/错误知识并删除

## 核心流程

### AI 智能知识管理流程

```
用户提问
    ↓
AI 调用 search_experience（向量检索 + AI 回答）
    ↓
AI 分析回答和 sources
    ↓
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  情况1: 确认错误/过时                                   │
│  → 调用 deprecate_chunk 删除向量                        │
│                                                         │
│  情况2: 不确定但有矛盾                                  │
│  → 调用 submit_conflict_for_review 提交后台审核         │
│                                                         │
│  情况3: 正确/最适合                                     │
│  → 直接返回给用户                                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 可用工具

### 知识检索（核心）
| 工具 | 说明 | 调用方 |
|------|------|--------|
| search_experience | 向量检索 + AI 回答（推荐） | AI Agent |
| ask_project | 逐级降级检索（精确匹配） | AI Agent |

### 记忆管理
| 工具 | 说明 |
|------|------|
| upload_memory | 上传记忆（支持 feature_codes、module） |
| ask_project | 逐级降级检索（功能→模块→全库） |
| list_projects | 列出项目 |
| delete_memory | 删除记忆 |
| batch_upload_memories | 批量上传记忆 |
| batch_delete_memories | 批量删除记忆 |

### 技能管理
| 工具 | 说明 |
|------|------|
| upload_skill | 上传技能 |
| search_skill | 搜索技能 |
| list_skills | 列出技能 |
| get_skill | 获取技能详情 |
| delete_skill | 删除技能 |

### 向量管理（AI 智能删除）
| 工具 | 说明 | 调用方 |
|------|------|--------|
| deprecate_chunk | 标记向量为废弃（确认过时/错误时） | AI Agent |
| delete_vector | 删除单个向量及相似向量 | AI Agent |
| delete_vectors | 批量删除向量 | AI Agent |

### 矛盾审核
| 工具 | 说明 | 调用方 |
|------|------|--------|
| submit_conflict_for_review | AI 提交矛盾对到后台（无法判断时） | AI Agent |
| list_conflicts | 列出待审核矛盾对 | 后台 |
| review_conflict | 审核矛盾对（选择 a/b/both） | 后台 |

### 模块/功能管理
| 工具 | 说明 |
|------|------|
| create_module | 创建模块 |
| list_modules | 列出模块 |
| delete_module | 删除模块（级联删除） |
| create_feature | 创建功能 |
| list_features | 列出功能 |
| delete_feature | 删除功能（级联删除） |

### 系统信息
| 工具 | 说明 |
|------|------|
| list_mcp_tools | 列出所有可用工具 |

## 使用流程

### 1. 初始化项目

```python
# 创建模块
create_module(project="Code-Mind", name="user", description="用户管理模块")

# 创建功能
create_feature(
    project="Code-Mind",
    code="2437",
    name="人员管理",
    module="user",
    description="新增、编辑、删除人员"
)
```

### 2. 上传知识

```python
# 上传记忆
upload_memory(
    project="Code-Mind",
    filename="2437_人员管理.md",
    content="...",
    feature_codes=["2437"],
    module="user"
)

# 批量上传
batch_upload_memories(
    project="Code-Mind",
    files=[
        {"filename": "doc1.md", "content": "..."},
        {"filename": "doc2.md", "content": "..."},
    ]
)
```

### 3. 查询知识（推荐方式）

```python
# 使用 search_experience（向量检索 + AI 回答）
result = search_experience(
    query="如何添加用户",
    kb_id=None,  # 可选，限定知识库
    top_k=5      # 可选，返回数量
)

# 返回格式
{
    "status": "success",
    "query": "如何添加用户",
    "ai_answer": "根据知识库，添加用户的步骤是...",
    "result_count": 5,
    "results": [...]  # 原始搜索结果
}
```

### 4. AI 智能知识管理

```python
# 场景1: AI 确认过时/错误 → 删除
# 从 sources 中找到 docId → chunkId → 调用 deprecate_chunk
deprecate_chunk(chunk_id="xxx")

# 场景2: AI 无法判断 → 提交审核
submit_conflict_for_review(
    project="Code-Mind",
    chunk_a_id="xxx",
    chunk_b_id="yyy",
    reason="两个作者给出不同结论",
    ai_analysis="作者A推荐X，作者B推荐Y"
)

# 场景3: 正确 → 直接返回给用户
```

### 5. 后台审核矛盾对

```python
# 查看待审核
conflicts = list_conflicts(project="Code-Mind")

# 审核矛盾对
review_conflict(
    project="Code-Mind",
    chunk_a_id="xxx",
    chunk_b_id="yyy",
    winner="a",      # a=保留A删除B, b=保留B删除A, both=都保留
    reason="A 是最新版本"
)
```

### 6. 维护知识

```python
# 更新记忆（增量更新）
upload_memory(
    project="Code-Mind",
    filename="2437_人员管理.md",
    content="新增：编辑用户接口...",
    feature_codes=["2437"]
)

# 删除功能（级联删除向量）
delete_feature(project="Code-Mind", code="2437")

# 删除模块（级联删除功能和向量）
delete_module(project="Code-Mind", name="user")
```

## search_experience vs ask_project

| 特性 | search_experience | ask_project |
|------|------------------|-------------|
| 检索方式 | 向量检索（语义理解） | LIKE 搜索（子串匹配） |
| AI 回答 | ✅ 返回 AI 生成的回答 | ❌ 只返回原始内容 |
| 近义词支持 | ✅ 支持 | ❌ 不支持 |
| 过时判断 | ✅ AI 自动判断 | ❌ 需要人工判断 |
| 矛盾检测 | ✅ 自动检测 | ❌ 不支持 |
| 适用场景 | Agent 问答（推荐） | 精确匹配 |

## 提交规范

### Skills 格式
```markdown
# 技能名称

## Description
技能描述

## Metadata
- Category: coding/testing/deployment
- Tags: 标签1, 标签2

## Content
具体内容
```

### 记忆格式
```markdown
# {功能编号}: {功能名称}

## 状态
- 完成度: 100%
- 最后更新: 2026-08-30

## 实现内容
- 功能点1
- 功能点2

## 已知问题
- 问题描述
```

## 常见问题

### Q: 如何选择检索方式？
A: 推荐使用 `search_experience`，它使用向量检索 + AI 回答，支持近义词和语义理解。如果需要精确匹配，可以使用 `ask_project`。

### Q: AI 如何判断过时知识？
A: AI 通过以下方式判断：
1. 检查回答中是否包含"过时"、"错误"、"已迁移"等关键词
2. 检查 sources 中的摘录是否包含警告信息
3. 比较多个 sources 的结论是否一致

### Q: AI 无法判断时怎么办？
A: AI 会调用 `submit_conflict_for_review` 提交矛盾对到后台，然后人工审核。

### Q: 如何删除过期知识？
A: 两种方式：
1. **AI 自动删除**：AI 判断为过时/错误时，调用 `deprecate_chunk` 标记废弃
2. **手动删除**：使用 `delete_feature` 或 `delete_module` 级联删除

### Q: 如何查看系统有哪些工具？
A: 使用 `list_mcp_tools` 列出所有可用工具。

### Q: 向量检索和关键词检索有什么区别？
A: 
- **向量检索**：理解语义，支持近义词（如"数据库"→PostgreSQL）
- **关键词检索**：精确匹配，只找包含完全相同词的内容
