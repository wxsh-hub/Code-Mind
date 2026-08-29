# F1 向量删除功能

## 目标
支持删除知识库、文档、单个向量，解决废弃功能无法删除的问题。

## 实现思路

### 1. ragent 侧 API（Java）

需要在 KnowledgeChunkApiController 中新增：

```java
// 删除整个知识库
DELETE /knowledge-base/{kbId}

// 删除文档及其所有向量
DELETE /knowledge-base/docs/{docId}

// 删除单个向量
DELETE /knowledge-base/chunks/{chunkId}

// 按条件批量删除
POST /knowledge-base/chunks/batch-delete
Body: {"kbId": "...", "sourceRef": "...", "tags": ["..."]}
```

### 2. MCP Gateway 侧（Python）

在 rag_client.py 中新增：

```python
def delete_knowledge_base(self, kb_id: str) -> bool
def delete_document(self, doc_id: str) -> bool
def delete_chunk(self, chunk_id: str) -> bool
def batch_delete_chunks(self, kb_id: str, source_ref: str = None) -> int
```

在 memory_tools.py 中新增 MCP Tool：

```python
def delete_memory_impl(project: str, filename: str = None) -> dict
# filename 为空时删除整个项目，否则删除指定文件
```

在 skill_tools.py 中新增 MCP Tool：

```python
def delete_skill_impl(project: str, skill_name: str, category: str = None) -> dict
```

### 3. MCP Tool 注册

```python
# 新增工具
delete_memory(project, filename=None)  # 删除记忆
delete_skill(project, skill_name, category=None)  # 删除技能
delete_project(project)  # 删除整个项目（含 skills 和 memory）
```

## 测试脚本思路

### test_vector_delete.sh

```
1. 创建知识库
2. 上传 3 个文档
3. 验证分块成功
4. 删除单个 chunk → 验证数量减少
5. 删除整个文档 → 验证文档和 chunk 都删除
6. 删除知识库 → 验证知识库不存在
7. 测试删除不存在的资源（应返回成功或友好错误）
```

### 单元测试 test_vector_delete.py

```python
class TestVectorDelete:
    def test_delete_chunk(self):
        # mock 删除接口
        # 验证调用正确

    def test_delete_document(self):
        # mock 删除接口
        # 验证调用正确

    def test_delete_nonexistent(self):
        # 删除不存在的资源
        # 验证不报错
```

## 依赖
- ragent 需要先实现删除 API
- MCP Gateway 调用 ragent API
