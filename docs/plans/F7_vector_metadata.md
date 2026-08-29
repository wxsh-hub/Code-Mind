# F7 向量元数据标记系统

## 目标

为向量添加元数据标记（功能编号），支持：
- 按功能编号查询向量
- 按功能编号批量删除向量
- 一个向量可以有多个编号
- 反义词检测限定在同一功能内

---

## 数据模型

### 1. 功能元数据表（新表）

```sql
CREATE TABLE t_feature_metadata (
    id VARCHAR(64) PRIMARY KEY,
    feature_code VARCHAR(32) NOT NULL UNIQUE COMMENT '功能编号，如 2437',
    feature_name VARCHAR(128) NOT NULL COMMENT '功能名称',
    module VARCHAR(64) COMMENT '所属模块',
    description TEXT COMMENT '功能描述',
    status VARCHAR(16) DEFAULT 'active' COMMENT '状态：active/deprecated',
    created_by VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0
);

CREATE INDEX idx_fm_feature_code ON t_feature_metadata(feature_code);
CREATE INDEX idx_fm_module ON t_feature_metadata(module);
```

### 2. 向量元数据字段（扩展现有表）

在 `t_knowledge_chunk` 表添加：

```sql
ALTER TABLE t_knowledge_chunk
    ADD COLUMN feature_codes VARCHAR(512) COMMENT '功能编号列表，逗号分隔，如 2437,2438';

CREATE INDEX idx_kc_feature_codes ON t_knowledge_chunk(feature_codes);
```

**存储格式**：`"2437,2438,2439"`（逗号分隔的编号列表）

---

## API 设计

### 1. 功能元数据 CRUD

```
POST   /api/ragent/feature-metadata              # 创建功能
GET    /api/ragent/feature-metadata              # 列出所有功能
GET    /api/ragent/feature-metadata/{code}       # 查询单个功能
PUT    /api/ragent/feature-metadata/{code}       # 更新功能
DELETE /api/ragent/feature-metadata/{code}       # 删除功能（级联删除向量）
```

#### 创建功能
```json
POST /api/ragent/feature-metadata
{
    "featureCode": "2437",
    "featureName": "管理人员管理",
    "module": "user",
    "description": "新增、编辑、删除人员的功能"
}
```

#### 删除功能（级联）
```json
DELETE /api/ragent/feature-metadata/2437

响应：
{
    "code": "0",
    "data": {
        "deleted_feature": true,
        "deleted_chunks": 15
    }
}
```

### 2. 向量上传时带元数据

```
POST /api/ragent/knowledge-base/{kbId}/docs/upload
```

新增参数 `featureCodes`（可选，逗号分隔）：

```bash
curl -X POST "/api/ragent/knowledge-base/123/docs/upload" \
  -F "file=@doc.md" \
  -F "sourceType=file" \
  -F "processMode=chunk" \
  -F "featureCodes=2437,2438"
```

### 3. 向量查询时过滤

```
POST /api/ragent/knowledge-base/search/similar
```

新增参数 `featureCodes`（可选）：

```json
{
    "query": "如何添加用户",
    "kbId": "123",
    "topK": 5,
    "featureCodes": "2437"  // 只查2437功能的向量
}
```

### 4. 按功能编号删除向量

```
DELETE /api/ragent/knowledge-base/chunks/by-feature/{code}
```

---

## MCP 工具设计

### 1. 功能元数据管理

```python
# 创建功能
create_feature(
    project="Code-Mind",
    code="2437",
    name="管理人员管理",
    module="user",
    description="新增、编辑、删除人员的功能"
)

# 列出功能
list_features(project="Code-Mind", module=None)

# 查询功能
get_feature(project="Code-Mind", code="2437")

# 删除功能（级联删除向量）
delete_feature(project="Code-Mind", code="2437")
# 返回：{"deleted_chunks": 15}
```

### 2. 带元数据上传

```python
# 上传记忆（带功能编号）
upload_memory(
    project="Code-Mind",
    filename="user_management.md",
    content="...",
    feature_codes=["2437", "2438"]  # 多个编号
)

# 上传技能（带功能编号）
upload_skill(
    project="Code-Mind",
    skill_name="用户管理指南",
    content="...",
    feature_codes=["2437"]
)
```

### 3. 带元数据查询

```python
# 按功能查询
ask_project(
    project="Code-Mind",
    question="如何添加用户",
    feature_codes=["2437"]  # 只查2437功能
)

# 搜索技能（按功能）
search_skill(
    project="Code-Mind",
    task_description="用户管理",
    feature_codes=["2437"]
)
```

---

## 实现步骤

### 第一阶段：数据库改造

1. 创建 `t_feature_metadata` 表
2. 扩展 `t_knowledge_chunk` 表添加 `feature_codes` 字段
3. 实现 FeatureMetadata 实体和 Mapper

### 第二阶段：API 实现

1. FeatureMetadataApiController（CRUD）
2. 修改文档上传接口（支持 featureCodes）
3. 修改向量查询接口（支持过滤）
4. 实现级联删除

### 第三阶段：MCP 工具

1. feature_tools.py（功能元数据管理）
2. 修改 memory_tools.py（支持 feature_codes）
3. 修改 skill_tools.py（支持 feature_codes）
4. 注册到 gateway.py

### 第四阶段：测试

1. 单元测试
2. 集成测试
3. 测试脚本

---

## 测试脚本思路

### test_feature_metadata.sh

```
1. 创建功能 2437（管理人员管理）
2. 创建功能 2438（权限管理）
3. 上传文档到 2437
4. 上传文档到 2438
5. 上传文档到 2437,2438（多编号）
6. 查询 2437 → 返回相关向量
7. 查询 2438 → 返回相关向量
8. 删除功能 2437 → 验证向量被删除
9. 验证 2438 的向量还在
```

### 单元测试

```python
class TestFeatureMetadata:
    def test_create_feature(self)
    def test_list_features(self)
    def test_delete_feature_cascade(self)

class TestVectorWithFeatureCodes:
    def test_upload_with_feature_codes(self)
    def test_search_with_feature_codes(self)
    def test_multi_feature_vector(self)
    def test_delete_by_feature_code(self)
```

---

## 查询示例

### 场景 1：查特定功能的知识
```
问："如何添加用户？" + feature_codes=["2437"]
答：只返回 2437 功能相关的知识
```

### 场景 2：查所有功能的知识
```
问："如何添加用户？"
答：返回所有功能的相关知识
```

### 场景 3：删除功能时清理
```
删除功能 2437
→ 自动删除所有 feature_codes 包含 2437 的向量
→ 返回删除了 15 条向量
```

### 场景 4：反义词检测（限定功能内）
```
检测 2437 功能内的反义向量
→ 只在 feature_codes 包含 2437 的向量中检测
→ 避免跨功能误判
```
