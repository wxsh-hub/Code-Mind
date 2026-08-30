# Code-Mind AI 使用指南

## 系统概述

Code-Mind 是企业级知识管理平台，提供 MCP 工具让 AI Agent 访问知识库。

## MCP 工具清单

### 1. 知识检索

#### search_experience
搜索企业知识库（向量检索 + AI 回答）

```python
search_experience(
    query: str,           # 搜索内容
    kb_id: str = None,    # 知识库ID（可选）
    top_k: int = 5        # 返回数量
)
```

**返回格式**：
```json
{
    "status": "success",
    "query": "用户注册",
    "ai_answer": "根据知识库，用户注册的步骤是...",
    "result_count": 3,
    "results": [
        {
            "chunk_id": "xxx",
            "content": "文档内容",
            "doc_id": "xxx",
            "doc_name": "文件名.md",
            "score": 0.95
        }
    ]
}
```

**使用场景**：
- 用户提问时调用
- 检索项目经验、编码规范、技术文档

---

### 2. 记忆管理

#### upload_memory
上传记忆文件到知识库

```python
upload_memory(
    project: str,              # 项目名称
    filename: str,             # 文件名
    content: str,              # 文件内容
    feature_codes: List[str] = None,  # 功能编号列表
    module: str = None         # 模块名称
)
```

**使用场景**：
- 上传项目文档
- 保存项目经验
- 记录技术决策

#### ask_project
向项目知识库提问（逐级降级检索）

```python
ask_project(
    project: str,              # 项目名称
    question: str,             # 问题
    top_k: int = 5,            # 返回数量
    feature_codes: List[str] = None,  # 功能编号（优先级最高）
    module: str = None         # 模块名称（次优先级）
)
```

**检索流程**：
1. 功能级检索（指定 feature_codes）
2. 模块级检索（指定 module）
3. 全库检索（无过滤）
4. 向量检索（LIKE 无结果时降级）

**返回格式**：
```json
{
    "project": "Code-Mind",
    "question": "用户注册功能怎么实现",
    "results": [...],
    "count": 3,
    "level": "feature",
    "feature_codes": ["F001"],
    "module": "user",
    "auto_detected": {
        "feature_codes": ["F001"],
        "module": "user"
    }
}
```

#### list_projects
列出所有项目

```python
list_projects()
```

#### delete_memory
删除记忆文件

```python
delete_memory(
    project: str,              # 项目名称
    filename: str = None       # 文件名（为空删除整个项目）
)
```

#### batch_upload_memories
批量上传记忆文件

```python
batch_upload_memories(
    project: str,              # 项目名称
    files: List[Dict],         # 文件列表 [{"filename": "...", "content": "..."}]
    feature_codes: List[str] = None,
    module: str = None
)
```

#### batch_delete_memories
批量删除记忆文件

```python
batch_delete_memories(
    project: str,              # 项目名称
    filenames: List[str]       # 文件名列表
)
```

---

### 3. 模块管理

#### create_module
创建模块

```python
create_module(
    project: str,              # 项目名称
    name: str,                 # 模块名称（如 user、order）
    description: str = ""      # 模块描述
)
```

#### list_modules
列出所有模块

```python
list_modules(project: str)
```

#### delete_module
删除模块（级联删除功能和向量）

```python
delete_module(
    project: str,
    name: str                  # 模块名称
)
```

---

### 4. 功能管理

#### create_feature
创建功能（关联模块）

```python
create_feature(
    project: str,
    code: str,                 # 功能编号（如 F001）
    name: str,                 # 功能名称（如 用户注册）
    module: str,               # 所属模块
    description: str = ""      # 功能描述
)
```

#### list_features
列出功能

```python
list_features(
    project: str,
    module: str = None         # 按模块过滤
)
```

#### delete_feature
删除功能（级联删除向量）

```python
delete_feature(
    project: str,
    code: str                  # 功能编号
)
```

---

### 5. 向量管理

#### deprecate_chunk
标记向量为废弃（AI 确认过时/错误时调用）

```python
deprecate_chunk(chunk_id: str)
```

#### batch_deprecate_chunks
批量标记向量为废弃

```python
batch_deprecate_chunks(chunk_ids: List[str])
```

---

### 6. 矛盾审核

#### submit_conflict_for_review
提交矛盾对到后台人工审核（AI 无法判断时调用）

```python
submit_conflict_for_review(
    project: str,
    chunk_a_id: str,           # 知识 A 的 chunk ID
    chunk_b_id: str,           # 知识 B 的 chunk ID
    reason: str,               # 提交原因
    ai_analysis: str = ""      # AI 分析
)
```

#### list_conflicts
列出待审核矛盾对

```python
list_conflicts(
    project: str,
    page: int = 1,
    page_size: int = 20
)
```

#### review_conflict
审核矛盾对

```python
review_conflict(
    project: str,
    chunk_a_id: str,
    chunk_b_id: str,
    winner: str,               # "a" | "b" | "both"
    reason: str = ""           # 审核原因
)
```

---

### 7. 技能管理

#### upload_skill
上传技能

```python
upload_skill(
    project: str,
    skill_name: str,
    content: str,
    category: str = None,
    tags: List[str] = None
)
```

#### search_skill
搜索技能

```python
search_skill(
    project: str,
    task_description: str,
    top_k: int = 5
)
```

#### list_skills
列出技能

```python
list_skills(project: str)
```

#### get_skill
获取技能详情

```python
get_skill(
    project: str,
    skill_name: str
)
```

#### delete_skill
删除技能

```python
delete_skill(
    project: str,
    skill_name: str
)
```

---

### 8. 系统信息

#### list_mcp_tools
列出所有可用 MCP 工具

```python
list_mcp_tools(categorized: bool = True)
```

---

## AI 工作流程

### 1. 知识检索流程

```
用户提问
    ↓
AI 调用 search_experience
    ↓
向量检索 + AI 回答
    ↓
AI 分析回答和 sources
    ↓
┌─────────────────────────────────────────┐
│ 确认过时/错误? → deprecate_chunk        │
│ 有矛盾?       → submit_conflict_for_review │
│ 正确?         → 直接返回用户            │
└─────────────────────────────────────────┘
```

### 2. 知识上传流程

```
AI 获取知识
    ↓
AI 调用 upload_memory
    ↓
指定 feature_codes 和 module
    ↓
知识被标记到对应功能和模块
```

### 3. 矛盾处理流程

```
AI 发现矛盾知识
    ↓
AI 尝试判断哪个正确
    ↓
┌─────────────────────────────────────────┐
│ 能判断 → deprecate_chunk 删除错误的     │
│ 不能判断 → submit_conflict_for_review   │
└─────────────────────────────────────────┘
    ↓
后台人工审核
    ↓
review_conflict 决定保留哪个
```

---

## 自动识别功能

当用户未指定 feature_codes 和 module 时，AI 会自动识别：

1. 搜索功能元数据表
2. 找到最相关的功能
3. 用功能编号过滤搜索

**示例**：
```
用户问: "用户注册功能怎么实现"
AI 自动识别: F001 (用户注册), module: user
检索范围: 只在 F001 相关的 chunk 中搜索
```

---

## 检索方式

### LIKE 检索
- 速度：~50ms
- 方式：子串匹配
- 适用：短关键词

### 向量检索
- 速度：~5000ms
- 方式：语义匹配
- 适用：长问题、语义搜索

### 混合检索（推荐）
- 先 LIKE 快速过滤
- LIKE 无结果时降级到向量检索
- 兼顾速度和准确性

---

## 错误处理

### 常见错误

| 错误码 | 说明 | 处理方式 |
|:---|:---|:---|
| A000001 | 未登录 | 调用 login() |
| B000001 | 系统错误 | 重试或联系管理员 |
| 数据访问异常 | 数据库错误 | 重试 |

### 重试机制

所有 API 调用都支持自动重试（3次，间隔1秒）。

---

## 最佳实践

1. **上传知识时指定元数据**：填写 feature_codes 和 module
2. **使用短关键词搜索**：LIKE 检索更准确
3. **长问题用向量检索**：语义搜索更准确
4. **及时审核矛盾**：避免知识冲突
5. **定期清理过时知识**：保持知识库质量
