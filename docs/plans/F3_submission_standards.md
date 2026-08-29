# F3 提交规范文档

## 目标
统一 Skills 和记忆的提交格式，告诉 AI 什么该提交、什么不该提交。

## 实现思路

### 1. 规范文档内容

创建 `docs/SUBMISSION_STANDARDS.md`：

```markdown
# 提交规范

## Skills 提交规范

### 格式要求
- 文件必须是 Markdown 格式
- 必须包含标题（# 开头）
- 必须包含分类（category）
- 建议包含标签（tags）

### 分类标准
- coding: 编码规范、代码模板
- testing: 测试指南、测试模板
- deployment: 部署流程、配置模板
- architecture: 架构设计、技术选型
- workflow: 工作流程、协作规范

### 示例
```markdown
# Java 单元测试规范

## Description
Java 项目单元测试编写规范

## Metadata
- Category: testing
- Tags: java, junit, testing

## Content
具体的测试规范内容...
```

## 记忆提交规范

### 应该提交
- 项目状态（模块完成度、已知问题）
- 架构决策（技术选型、设计方案）
- 经验总结（踩坑记录、最佳实践）
- 模块关系（依赖关系、接口说明）

### 不应该提交
- 临时调试日志
- 个人笔记（未验证的内容）
- 敏感信息（密码、密钥、Token）
- 过期内容（已废弃的功能）
- 临时代码片段

### 格式要求
- 文件必须是 Markdown 格式
- 建议包含元数据（frontmatter）
- 内容应该简洁明了
- 避免冗余描述

## 提交顺序

1. 先提交 Skills（代码、规范、指南）
2. 再提交记忆（状态、经验、总结）

原因：记忆中可能引用 skills 的路径，先提交 skills 可以让路径引用匹配成功。
```

### 2. 上传到帮助文档系统

使用 upload_memory 将规范文档上传：

```python
upload_memory(
    project="system",
    filename="SUBMISSION_STANDARDS.md",
    content=规范文档内容
)
```

### 3. list_mcp_tools 集成

在 list_mcp_tools 返回中包含规范摘要：

```json
{
  "tools": [...],
  "guidelines": {
    "skills": "先提交 skills，格式为 Markdown，包含分类和标签",
    "memory": "再提交记忆，避免敏感信息和临时内容",
    "order": "先 skills 后 memory"
  }
}
```

## 测试脚本思路

### test_submission_standards.sh

```
1. 上传规范文档到 system 项目
2. 搜索 "提交规范" → 返回规范内容
3. 搜索 "什么不该提交" → 返回禁止列表
4. 验证 list_mcp_tools 包含 guidelines
```

### 单元测试

```python
class TestSubmissionStandards:
    def test_upload_standards(self):
        # 上传规范文档
        # 验证上传成功

    def test_search_standards(self):
        # 搜索规范内容
        # 验证返回正确
```

## 依赖
- F2 MCP 接口发现（用于集成 guidelines）
