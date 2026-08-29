# F7 向量元数据标记系统

## 目标

为向量添加元数据标记（功能编号 + 模块），支持：
- 按功能编号查询向量
- 按模块查询向量
- 按功能编号批量删除向量
- 一个向量可以有多个编号
- 逐级降级检索：功能级 → 模块级 → 全库

---

## 数据模型

### 1. 模块表（新表）

```sql
CREATE TABLE t_module (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(64) NOT NULL UNIQUE COMMENT '模块名称，如 user、order、payment',
    description TEXT COMMENT '模块描述',
    created_by VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0
);

CREATE INDEX idx_module_name ON t_module(name);
```

### 2. 功能元数据表（新表）

```sql
CREATE TABLE t_feature_metadata (
    id VARCHAR(64) PRIMARY KEY,
    feature_code VARCHAR(32) NOT NULL UNIQUE COMMENT '功能编号，如 2437',
    feature_name VARCHAR(128) NOT NULL COMMENT '功能名称',
    module_name VARCHAR(64) COMMENT '所属模块名称，如 user、order',
    description TEXT COMMENT '功能描述',
    status VARCHAR(16) DEFAULT 'active' COMMENT '状态：active/deprecated',
    created_by VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0
);

CREATE INDEX idx_fm_feature_code ON t_feature_metadata(feature_code);
CREATE INDEX idx_fm_module_name ON t_feature_metadata(module_name);
```

### 3. 向量元数据字段（扩展现有表）

在 `t_knowledge_chunk` 表添加 JSONB 字段：

```sql
ALTER TABLE t_knowledge_chunk
    ADD COLUMN metadata JSONB DEFAULT '{}';

CREATE INDEX idx_kc_metadata ON t_knowledge_chunk USING GIN (metadata);
```

**存储格式示例**：
```json
{
    "feature_codes": ["2437", "2438"],
    "module": "user",
    "type": "api",
    "version": "1.0"
}
```

---

## 逐级降级检索策略

```
用户提问
    ↓
[1] 按功能编号检索（feature_codes）
    ↓ 无结果
[2] 按模块检索（module）
    ↓ 无结果
[3] 全库检索（不限条件）
    ↓
返回结果（标记检索级别）
```

### 检索逻辑

```python
def ask_project_with_fallback(project, question, feature_codes=None, module=None):
    # [1] 按功能编号检索
    if feature_codes:
        results = search(question, metadata={"feature_codes": feature_codes})
        if results:
            return {"results": results, "level": "feature"}
    
    # [2] 按模块检索
    if module:
        results = search(question, metadata={"module": module})
        if results:
            return {"results": results, "level": "module"}
    
    # [3] 全库检索
    results = search(question)
    return {"results": results, "level": "global"}
```

---

## API 设计

### 1. 模块 CRUD

```
POST   /api/ragent/modules                    # 创建模块
GET    /api/ragent/modules                    # 列出所有模块
GET    /api/ragent/modules/{id}               # 查询模块
PUT    /api/ragent/modules/{id}               # 更新模块
DELETE /api/ragent/modules/{id}               # 删除模块（级联删除功能和向量）
```

### 2. 功能元数据 CRUD

```
POST   /api/ragent/feature-metadata           # 创建功能
GET    /api/ragent/feature-metadata           # 列出所有功能（可按模块过滤）
GET    /api/ragent/feature-metadata/{code}    # 查询功能
PUT    /api/ragent/feature-metadata/{code}    # 更新功能
DELETE /api/ragent/feature-metadata/{code}    # 删除功能（级联删除向量）
```

#### 创建功能（必须带模块名）
```json
POST /api/ragent/feature-metadata
{
    "featureCode": "2437",
    "featureName": "人员管理",
    "moduleName": "user",
    "description": "新增、编辑、删除人员的功能"
}
```

#### 查询功能（返回包含模块名）
```json
GET /api/ragent/feature-metadata/2437

响应：
{
    "code": "0",
    "data": {
        "featureCode": "2437",
        "featureName": "人员管理",
        "moduleName": "user",
        "description": "...",
        "status": "active"
    }
}
```

#### 按模块列出功能
```json
GET /api/ragent/feature-metadata?module=user
```

### 3. 向量上传（带元数据）

```
POST /api/ragent/knowledge-base/{kbId}/docs/upload
```

新增参数：
- `featureCodes`：功能编号列表（逗号分隔）
- `module`：模块名称

### 4. 向量查询（带降级）

```
POST /api/ragent/knowledge-base/search/similar
```

新增参数：
- `featureCodes`：功能编号过滤
- `module`：模块过滤

返回新增字段：
- `level`：检索级别（feature/module/global）

### 5. 按编号删除向量

```
DELETE /api/ragent/knowledge-base/chunks/by-feature/{code}
DELETE /api/ragent/knowledge-base/chunks/by-module/{module}
```

---

## MCP 工具设计

### 1. 模块管理

```python
# 创建模块
create_module(
    project="Code-Mind",
    name="user",
    description="用户管理模块"
)

# 列出模块
list_modules(project="Code-Mind")

# 删除模块（级联删除功能和向量）
delete_module(project="Code-Mind", name="user")
```

### 2. 功能管理

```python
# 创建功能
create_feature(
    project="Code-Mind",
    code="2437",
    name="人员管理",
    module="user",  # 所属模块
    description="新增、编辑、删除人员"
)

# 列出功能
list_features(project="Code-Mind", module=None)

# 删除功能（级联删除向量）
delete_feature(project="Code-Mind", code="2437")
```

### 3. 带元数据上传

```python
# 上传记忆（带元数据）
upload_memory(
    project="Code-Mind",
    filename="user_mgmt.md",
    content="...",
    feature_codes=["2437"],
    module="user"
)

# 上传技能（带元数据）
upload_skill(
    project="Code-Mind",
    skill_name="用户管理指南",
    content="...",
    feature_codes=["2437"],
    module="user"
)
```

### 4. 逐级降级检索

```python
# 按功能 → 模块 → 全库 降级检索
result = ask_project(
    project="Code-Mind",
    question="如何添加用户",
    feature_codes=["2437"],  # 优先按功能查
    module="user"            # 其次按模块查
)

# 返回
{
    "results": [...],
    "level": "feature",  # 实际检索级别
    "feature_codes": ["2437"],
    "module": "user"
}
```

---

## 实现步骤

### 第一阶段：数据库改造（ragent）

1. 创建 `t_module` 表
2. 创建 `t_feature_metadata` 表
3. 扩展 `t_knowledge_chunk` 添加 `metadata` JSONB 字段
4. 实现实体类和 Mapper

### 第二阶段：API 实现（ragent）

1. ModuleApiController（CRUD）
2. FeatureMetadataApiController（CRUD）
3. 修改文档上传接口（支持 featureCodes、module）
4. 修改向量查询接口（支持 JSONB 过滤）
5. 实现级联删除

### 第三阶段：MCP 工具（mcp_gateway）

1. feature_tools.py（模块和功能管理）
2. 修改 memory_tools.py（支持 metadata）
3. 修改 skill_tools.py（支持 metadata）
4. 实现逐级降级检索逻辑
5. 注册到 gateway.py

### 第四阶段：测试

1. 单元测试
2. 集成测试
3. 测试脚本

---

## 测试脚本思路

### test_feature_metadata.sh

```
1. 创建模块 user
2. 创建模块 order
3. 创建功能 2437（人员管理）→ 模块 user
4. 创建功能 2438（权限管理）→ 模块 user
5. 创建功能 3001（订单查询）→ 模块 order

6. 上传文档到 2437
7. 上传文档到 2438
8. 上传文档到 3001
9. 上传文档到 user 模块（无具体功能）

10. 查询 feature_codes=2437 → 返回相关向量
11. 查询 feature_codes=9999 + module=user → 降级到模块级
12. 查询 feature_codes=9999 + module=xxx → 降级到全库

13. 删除功能 2437 → 验证向量被删除
14. 验证 2438 的向量还在
15. 删除模块 order → 验证 3001 的向量也被删除
```

### 单元测试

```python
class TestModule:
    def test_create_module(self)
    def test_list_modules(self)
    def test_delete_module_cascade(self)

class TestFeatureMetadata:
    def test_create_feature(self)
    def test_list_features_by_module(self)
    def test_delete_feature_cascade(self)

class TestVectorMetadata:
    def test_upload_with_metadata(self)
    def test_search_by_feature_code(self)
    def test_search_by_module(self)
    def test_hierarchical_search(self)  # 逐级降级
    def test_delete_by_feature_code(self)
    def test_delete_by_module(self)
```

---

## 查询示例

### 场景 1：精确查询（功能级）

```
问："如何添加用户？"
元数据：feature_codes=["2437"], module="user"

检索：
1. 查 feature_codes 包含 2437 → 找到 3 条 ✓
返回：level=feature
```

### 场景 2：降级到模块级

```
问："如何处理异常？"
元数据：feature_codes=["9999"], module="user"

检索：
1. 查 feature_codes 包含 9999 → 0 条
2. 查 module=user → 找到 8 条 ✓
返回：level=module
```

### 场景 3：降级到全库

```
问："项目架构是什么？"
元数据：feature_codes=["9999"], module="unknown"

检索：
1. 查 feature_codes 包含 9999 → 0 条
2. 查 module=unknown → 0 条
3. 全库检索 → 找到 10 条 ✓
返回：level=global
```

### 场景 4：删除功能时清理

```
删除功能 2437
→ 自动删除 metadata.feature_codes 包含 "2437" 的向量
→ 返回删除了 15 条向量
```

### 场景 5：删除模块时清理

```
删除模块 user
→ 自动删除 metadata.module = "user" 的向量
→ 同时删除该模块下的所有功能
→ 返回删除了 50 条向量、3 个功能
```
