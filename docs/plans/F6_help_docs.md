# F6 帮助文档系统

## 目标
上传帮助文档告诉 AI 怎么使用 Code-Mind 系统，包含使用说明、API 文档、示例。

## 实现思路

### 1. 帮助文档内容

创建 `docs/HELP_SYSTEM.md`：

```markdown
# Code-Mind 使用指南

## 系统简介
Code-Mind 是企业级 AI 知识管理平台，支持：
- 项目记忆管理（状态、经验、决策）
- 技能存储（代码规范、操作指南）
- 知识检索（语义搜索、置信度评分）

## 可用工具

### 记忆管理
- upload_memory: 上传记忆文件
- ask_project: 按项目问答
- list_projects: 列出所有项目
- delete_memory: 删除记忆

### 技能管理
- upload_skill: 上传技能
- search_skill: 搜索技能
- list_skills: 列出技能
- get_skill: 获取技能详情
- delete_skill: 删除技能

### 系统信息
- list_mcp_tools: 列出所有可用工具

## 使用流程

### 1. 初始化项目
先上传 skills（编码规范、操作指南），再上传记忆（项目状态、经验）。

### 2. 查询知识
使用 ask_project 或 search_skill 查询相关知识。

### 3. 维护知识
定期更新记忆，删除过期内容，审核矛盾知识。

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
- 简洁明了
- 包含状态和结论
- 避免敏感信息
```

### 2. 上传到系统

```python
# 上传到 system 项目
upload_memory(
    project="system",
    filename="HELP_SYSTEM.md",
    content=帮助文档内容
)
```

### 3. 动态查询

AI 问 "怎么使用这个系统" 时：

```python
ask_project(project="system", question="怎么使用 Code-Mind")
```

### 4. list_mcp_tools 集成

在 list_mcp_tools 返回中添加帮助摘要：

```json
{
  "tools": [...],
  "help": {
    "overview": "Code-Mind 企业级 AI 知识管理平台",
    "quick_start": "先上传 skills，再上传记忆",
    "docs": "详细文档请查询 '怎么使用这个系统'"
  }
}
```

## 测试脚本思路

### test_help_docs.sh

```
1. 上传帮助文档到 system 项目
2. 搜索 "怎么使用" → 返回帮助内容
3. 搜索 "有哪些工具" → 返回工具列表
4. 搜索 "提交规范" → 返回规范说明
5. 验证 list_mcp_tools 包含 help 字段
```

### 单元测试

```python
class TestHelpDocs:
    def test_upload_help(self):
        # 上传帮助文档
        # 验证成功

    def test_search_how_to_use(self):
        # 搜索使用方法
        # 验证返回正确

    def test_list_tools_with_help(self):
        # 验证 list_mcp_tools 包含帮助信息
```

## 依赖
- F2 MCP 接口发现
- F3 提交规范
