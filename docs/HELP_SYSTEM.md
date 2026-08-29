# Code-Mind 使用指南

## 系统简介

Code-Mind 是企业级 AI 知识管理平台，支持：
- **项目记忆管理**：状态、经验、决策
- **技能存储**：代码规范、操作指南
- **知识检索**：语义搜索、置信度评分
- **功能元数据标记**：按功能/模块管理知识

## 可用工具

### 模块管理
| 工具 | 说明 |
|------|------|
| create_module | 创建模块 |
| list_modules | 列出模块 |
| delete_module | 删除模块（级联删除功能和向量） |

### 功能管理
| 工具 | 说明 |
|------|------|
| create_feature | 创建功能（必须关联模块） |
| list_features | 列出功能 |
| delete_feature | 删除功能（级联删除向量） |

### 记忆管理
| 工具 | 说明 |
|------|------|
| upload_memory | 上传记忆（支持 feature_codes、module） |
| ask_project | 逐级降级检索（功能→模块→全库） |
| list_projects | 列出项目 |
| delete_memory | 删除记忆 |

### 技能管理
| 工具 | 说明 |
|------|------|
| upload_skill | 上传技能 |
| search_skill | 搜索技能 |
| list_skills | 列出技能 |
| get_skill | 获取技能详情 |
| delete_skill | 删除技能 |

### 知识检索
| 工具 | 说明 |
|------|------|
| search_experience | 搜索企业知识库 |

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
# 先上传技能
upload_skill(
    project="Code-Mind",
    skill_name="用户管理指南",
    content="...",
    category="coding",
    feature_codes=["2437"],
    module="user"
)

# 再上传记忆
upload_memory(
    project="Code-Mind",
    filename="2437_人员管理.md",
    content="...",
    feature_codes=["2437"],
    module="user"
)
```

### 3. 查询知识

```python
# 逐级降级检索
result = ask_project(
    project="Code-Mind",
    question="如何添加用户",
    feature_codes=["2437"],  # 优先按功能查
    module="user"            # 其次按模块查
)
# 检索顺序：功能级 → 模块级 → 全库

# 搜索技能
result = search_skill(
    project="Code-Mind",
    task_description="用户管理"
)
```

### 4. 维护知识

```python
# 更新记忆（增量更新）
upload_memory(
    project="Code-Mind",
    filename="2437_人员管理.md",
    content="新增：编辑用户接口...",
    feature_codes=["2437"]
)

# 删除功能
delete_feature(project="Code-Mind", code="2437")

# 删除模块
delete_module(project="Code-Mind", name="user")
```

### 5. 矛盾审核

```python
# 列出矛盾对
conflicts = list_conflicts(project="Code-Mind")

# 审核矛盾对
review_conflict(
    project="Code-Mind",
    chunk_a_id="1",
    chunk_b_id="2",
    winner="a",
    reason="A 正确"
)
```

### 6. 查看可用工具

```python
# 列出所有 MCP 工具
tools = list_mcp_tools(categorized=True)
```

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
- 最后更新: 2026-08-29

## 实现内容
- 功能点1
- 功能点2

## 已知问题
- 问题描述
```

## 常见问题

### Q: 如何选择检索方式？
A: 使用 `ask_project` 并指定 `feature_codes` 和 `module`，系统会自动逐级降级检索。

### Q: 如何处理矛盾知识？
A: 使用 `list_conflicts` 列出矛盾对，然后用 `review_conflict` 审核。

### Q: 如何删除过期知识？
A: 使用 `delete_feature` 或 `delete_module` 删除相关向量。

### Q: 如何查看系统有哪些工具？
A: 使用 `list_mcp_tools` 列出所有可用工具。
