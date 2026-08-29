# F6 帮助文档系统

## 目标

上传帮助文档告诉 AI 怎么使用 Code-Mind 系统。

## 帮助文档内容

### 1. 系统简介

```markdown
# Code-Mind 使用指南

## 系统简介
Code-Mind 是企业级 AI 知识管理平台，支持：
- 项目记忆管理（状态、经验、决策）
- 技能存储（代码规范、操作指南）
- 知识检索（语义搜索、置信度评分）
- 功能元数据标记（按功能/模块管理知识）
```

### 2. MCP 工具清单

```markdown
## 可用工具

### 模块管理
- create_module: 创建模块
- list_modules: 列出模块
- delete_module: 删除模块（级联删除）

### 功能管理
- create_feature: 创建功能（必须关联模块）
- list_features: 列出功能
- delete_feature: 删除功能（级联删除）

### 记忆管理
- upload_memory: 上传记忆（支持 feature_codes、module）
- ask_project: 逐级降级检索（功能→模块→全库）
- list_projects: 列出项目
- delete_memory: 删除记忆

### 技能管理
- upload_skill: 上传技能
- search_skill: 搜索技能
- list_skills: 列出技能
- get_skill: 获取技能详情
- delete_skill: 删除技能

### 知识快照
- generate_snapshot: 生成功能知识快照
- preload_snapshots: 预加载多个功能快照

### 系统信息
- list_mcp_tools: 列出所有可用工具
```

### 3. 使用流程

```markdown
## 使用流程

### 1. 初始化项目
1. 创建模块：create_module(name="user")
2. 创建功能：create_feature(code="2437", name="人员管理", module="user")
3. 上传技能：upload_skill(feature_codes=["2437"])
4. 上传记忆：upload_memory(feature_codes=["2437"])

### 2. 查询知识
- 逐级降级：ask_project(feature_codes=["2437"], module="user")
- 本地快照：generate_snapshot(feature_code="2437")

### 3. 维护知识
- 更新记忆：upload_memory（自动增量更新）
- 删除功能：delete_feature(code="2437")
- 删除模块：delete_module(name="user")
```

### 4. 提交规范

```markdown
## 提交规范

### 记忆文件格式
# 2437: 人员管理

## 实现内容
- 新增用户接口
- 编辑用户接口

## 已知问题
- 删除用户时需要级联删除关联数据

### Skills 文件格式
# 用户管理指南

## Description
用户管理操作指南

## Metadata
- Category: coding
- Tags: user, management

## Content
具体内容...
```

## 实现方式

### 上传到知识库

```python
# 上传到 system 项目
upload_memory(
    project="system",
    filename="HELP_SYSTEM.md",
    content=帮助文档内容
)
```

### AI 查询

```python
# AI 问怎么使用
ask_project(
    project="system",
    question="怎么使用 Code-Mind"
)
```

### MCP 工具集成

```python
# list_mcp_tools 返回帮助摘要
{
    "tools": [...],
    "help": {
        "overview": "Code-Mind 企业级 AI 知识管理平台",
        "quick_start": "先创建模块和功能，再上传技能和记忆",
        "docs": "详细文档请查询 '怎么使用这个系统'"
    }
}
```

## 测试脚本

### test_help_docs.sh

```
1. 上传帮助文档到 system 项目
2. 搜索 "怎么使用" → 返回帮助内容
3. 搜索 "有哪些工具" → 返回工具列表
4. 搜索 "提交规范" → 返回规范说明
5. 验证 list_mcp_tools 包含 help 字段
```

## 依赖

- F2 MCP 接口发现
- F7 元数据系统
