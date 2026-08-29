# F4 Skills 粒度优化

## 目标
上传 Skills 时按章节/段落拆分，每个段落独立向量化，检索时返回最相关的段落。

## 实现思路

### 1. 智能拆分策略

在 skill_tools.py 中新增拆分逻辑：

```python
def split_skill_content(content: str) -> List[dict]:
    """按章节拆分技能内容

    返回:
    [
        {"title": "类命名", "content": "...", "level": 2},
        {"title": "方法命名", "content": "...", "level": 2},
        ...
    ]
    """
```

拆分规则：
- 按 ## 标题拆分（二级标题）
- 每个段落包含标题 + 内容
- 保留元数据（category, tags）
- 段落过短（< 50 字）时合并到上一个段落

### 2. 上传流程改造

```python
def upload_skill(self, project, skill_name, content, ...):
    # 1. 拆分内容
    sections = split_skill_content(content)

    # 2. 为每个段落创建单独的文档
    for section in sections:
        section_content = f"# {skill_name} - {section['title']}\n\n{section['content']}"
        # 上传到 RAG

    # 3. 本地存储完整文件（不拆分）
```

### 3. 检索结果增强

```python
def search_skill(self, project, task_description, ...):
    results = ...

    # 后处理：合并同一 skill 的多个段落
    merged = merge_skill_sections(results)

    return merged
```

### 4. 元数据标记

拆分后的段落添加元数据：
```json
{
    "parent_skill": "Java_Naming",
    "section_title": "类命名",
    "section_index": 0,
    "total_sections": 5
}
```

## 测试脚本思路

### test_skill_granularity.sh

```
1. 创建一个包含 5 个章节的 skill 文件
2. 上传到项目
3. 验证生成了 5 个独立的向量（而不是 1 个）
4. 搜索 "类命名" → 只返回相关段落
5. 搜索 "方法命名" → 只返回相关段落
6. 验证返回内容不包含其他段落
```

### 单元测试

```python
class TestSkillGranularity:
    def test_split_by_sections(self):
        content = """
        # Java 规范
        ## 类命名
        Use PascalCase
        ## 方法命名
        Use camelCase
        """
        sections = split_skill_content(content)
        assert len(sections) == 2
        assert sections[0]["title"] == "类命名"

    def test_short_section_merge(self):
        # 测试过短段落合并

    def test_search_returns_relevant_section(self):
        # 测试搜索只返回相关段落
```

## 依赖
- 无外部依赖
- 需要改造 upload_skill 和 search_skill
