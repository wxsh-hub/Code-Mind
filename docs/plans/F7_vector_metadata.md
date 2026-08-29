# F7 向量元数据标记系统

## 目标

为向量添加元数据标记（功能编号 + 模块），支持：
- 按功能编号查询向量
- 按模块查询向量
- 按功能编号批量删除向量
- 一个向量可以有多个编号
- 逐级降级检索：功能级 → 模块级 → 全库

---

## 置信度方案

### 问题

当前置信度 = 上传次数，有问题：
- 旧内容上传多次 → 置信度高（但可能过时）
- 新内容上传一次 → 置信度低（但可能更准确）

### 方案：返回原始数据，AI 判断

返回字段：
```json
{
    "content": "...",
    "metadata": {
        "upload_count": 10,        // 上传次数
        "last_upload": "2026-08-29", // 最后上传时间
        "days_old": 5,             // 天数
        "confidence": 10           // 原始置信度
    }
}
```

AI 判断逻辑：
```
问"怎么做" → 优先最新的（last_upload）
问"最佳实践" → 优先最频繁的（upload_count）
问"历史" → 优先最老的
```

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

在 `t_knowledge_chunk` 表添加字段：

```sql
-- JSONB 元数据
ALTER TABLE t_knowledge_chunk
    ADD COLUMN metadata JSONB DEFAULT '{}';

CREATE INDEX idx_kc_metadata ON t_knowledge_chunk USING GIN (metadata);

-- 上传统计字段
ALTER TABLE t_knowledge_chunk
    ADD COLUMN upload_count INT DEFAULT 1 COMMENT '上传次数',
    ADD COLUMN last_upload_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '最后上传时间';

CREATE INDEX idx_kc_upload_count ON t_knowledge_chunk(upload_count);
CREATE INDEX idx_kc_last_upload ON t_knowledge_chunk(last_upload_at);
```

**存储格式示例**：
```json
{
    "feature_codes": ["2437", "2438"],
    "module": "user",
    "type": "api",
    "version": "1.0",
    "upload_count": 10,
    "last_upload": "2026-08-29",
    "days_old": 5
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
```json
{
    "level": "feature",
    "results": [
        {
            "chunkId": "123",
            "content": "...",
            "metadata": {
                "feature_codes": ["2437"],
                "module": "user"
            },
            "upload_count": 10,
            "last_upload": "2026-08-29",
            "days_old": 5,
            "confidence": 10
        }
    ]
}
```

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

## 本地知识快照

### 目标

按功能编号生成本地知识快照，减少网络请求和 Token 消耗。

### 流程

```
AI 开始处理 2437 功能
    ↓
[1] 查询知识库：feature_codes=["2437"] 的所有向量
    ↓
[2] 过滤过期内容
    - deprecated = true → 排除
    - confidence < 3 → 排除
    - 更新时间 > 30天 → 标记过期
    ↓
[3] 按置信度排序
    ↓
[4] 简单拼接成 MD（不调用 AI）
    ↓
[5] 保存到本地：.cache/{project}/{feature_code}.md
    ↓
AI 后续问题先查本地快照
```

### 快照格式

```markdown
# 2437: 人员管理 - 知识快照

> 生成时间：2026-08-29 18:00
> 向量数量：5
> 过滤掉：2 个过期、1 个低置信度

---

**置信度：8**

实现了用户增删改查功能：
- 新增用户接口：POST /api/user
- 编辑用户接口：PUT /api/user/{id}

---

**置信度：5**

⚠️ 内容可能过期（30天前更新）

删除用户时需要级联删除关联数据
```

### 过滤逻辑

```python
def filter_vectors(vectors):
    """过滤过期内容"""
    filtered = []
    for v in vectors:
        # 排除已废弃
        if v.metadata.get("deprecated"):
            continue
        # 排除低置信度
        if v.metadata.get("confidence", 1) < 3:
            continue
        # 标记可能过期
        if v.metadata.get("days_old", 0) > 30:
            v.metadata["stale_warning"] = "⚠️ 内容可能过期"
        filtered.append(v)
    return filtered
```

### 性能对比

| 方案 | 耗时 | Token 消耗 |
|------|------|-----------|
| 每次查知识库 | 10 次 = 10-30 秒 | 1000-2000 |
| 本地快照 | 1 次 = 1 秒 | 0 |

### 使用方式

```python
# 生成快照（首次）
snapshot = generate_feature_snapshot("Code-Mind", "2437")

# AI 问问题（先查本地）
result = local_search(snapshot, "如何添加用户")
if result:
    return result  # 本地命中

# 本地没有，查知识库
result = ask_project("如何添加用户", feature_codes=["2437"])
```

### MCP 工具

```python
# 生成功能知识快照
generate_snapshot(
    project="Code-Mind",
    feature_code="2437"
)

# 预加载多个功能快照
preload_snapshots(
    project="Code-Mind",
    feature_codes=["2437", "2438", "2439"]
)
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
