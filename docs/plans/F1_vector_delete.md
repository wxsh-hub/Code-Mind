# F1 向量删除功能

## 目标

支持多种删除方式，与 F7 元数据系统集成。

## 删除方式

| 方式 | 说明 | 实现 |
|------|------|------|
| 按功能编号删除 | 删除某功能的所有向量 | metadata->'feature_codes' @> |
| 按模块删除 | 删除某模块的所有向量 | metadata->>'module' = |
| 按文档删除 | 删除某文档的所有向量 | doc_id = |
| 按 chunk 删除 | 删除单个向量 | chunk_id = |
| 按知识库删除 | 删除整个知识库 | kb_id = |

## API 设计

### ragent 侧

```
DELETE /api/ragent/knowledge-base/{kbId}
DELETE /api/ragent/knowledge-base/docs/{docId}
DELETE /api/ragent/knowledge-base/chunks/{chunkId}
DELETE /api/ragent/knowledge-base/chunks/by-feature/{code}
DELETE /api/ragent/knowledge-base/chunks/by-module/{module}
```

### MCP 工具

```python
# 删除功能（级联删除向量）
delete_feature(project="Code-Mind", code="2437")
# 返回: {"deleted_chunks": 15}

# 删除模块（级联删除功能和向量）
delete_module(project="Code-Mind", name="user")
# 返回: {"deleted_chunks": 50, "deleted_features": 3}

# 删除记忆文件
delete_memory(project="Code-Mind", filename="2437_人员管理.md")
# 返回: {"deleted_chunks": 5}

# 删除技能
delete_skill(project="Code-Mind", skill_name="用户管理指南")
# 返回: {"deleted_chunks": 3}
```

## 实现逻辑

### 按功能编号删除

```python
def delete_by_feature_code(project, feature_code):
    """删除某功能的所有向量"""
    kb_id = get_project_kb(project)
    
    # 查询该功能的所有向量
    chunks = query_chunks(
        kb_id=kb_id,
        where={"metadata->'feature_codes' @>": f'["{feature_code}"]'}
    )
    
    # 批量删除
    deleted_count = delete_chunks([c.id for c in chunks])
    
    return {"deleted_chunks": deleted_count}
```

### 按模块删除

```python
def delete_by_module(project, module):
    """删除某模块的所有向量"""
    kb_id = get_project_kb(project)
    
    # 查询该模块的所有向量
    chunks = query_chunks(
        kb_id=kb_id,
        where={"metadata->>'module'": module}
    )
    
    # 批量删除
    deleted_count = delete_chunks([c.id for c in chunks])
    
    return {"deleted_chunks": deleted_count}
```

## 测试脚本

### test_vector_delete.sh

```
1. 创建模块 user
2. 创建功能 2437（模块 user）
3. 上传文档到 2437
4. 上传文档到 user 模块（无功能编号）
5. 验证向量数量

6. 删除功能 2437
7. 验证 2437 的向量被删除
8. 验证 user 模块的向量还在

9. 删除模块 user
10. 验证 user 的向量被删除
```

### 单元测试

```python
class TestVectorDelete:
    def test_delete_by_feature_code(self):
        # 删除功能 2437
        # 验证该功能的向量被删除
        # 验证其他功能的向量还在

    def test_delete_by_module(self):
        # 删除模块 user
        # 验证该模块的所有向量被删除
        # 验证其他模块的向量还在

    def test_cascade_delete_feature(self):
        # 删除功能时，同时删除功能元数据

    def test_cascade_delete_module(self):
        # 删除模块时，同时删除模块下所有功能和向量
```

## 依赖

- F7 元数据系统（metadata JSONB 字段）
