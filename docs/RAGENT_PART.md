# Ragent 端改造任务

> 本文档描述 ragent 项目需要完成的工作。
> mcp-gateway 端的改造见 mcp-gateway 项目的 `MCP_GATEWAY_PART.md`。

## 功能清单

| 编号 | 功能 | 描述 |
|------|------|------|
| F2 | 连接 MCP Gateway | 配置 MCP client 连接 mcp-gateway，Agent 自动调用经验检索 |
| F5 | 元数据扩展 | 知识库文档表增加元数据字段（来源、版本、投票计数等） |
| F6 | 向量检索接口 | 暴露 HTTP 接口供 mcp-gateway 做相似 chunk 检索（矛盾检测用） |
| F7 | 引用计数接口 | 暴露 HTTP 接口供 mcp-gateway 记录 chunk 被引用次数 |

## 阶段 1：配置 MCP Gateway 连接（F2）

**目标**：ragent 的 Agent 能调用 mcp-gateway 的 `search_experience` 工具。

### 1.1 配置 MCP 连接

修改文件：`bootstrap/src/main/resources/application-local.yaml`

在已有配置基础上追加：

```yaml
rag:
  mcp:
    servers:
      - name: experience-gateway
        url: http://localhost:8000  # mcp-gateway 的地址
```

> mcp-gateway 默认端口是 8000，根据实际部署调整。

### 1.2 Agent Prompt 指引

在 Agent Profile 的主提示词中加入经验检索指引：

```
你有一个 search_experience 工具，用于检索企业项目经验和开发规范。
当遇到以下情况时，优先调用此工具：
- 需要了解项目的编码规范
- 需要查找类似功能的实现经验
- 需要确认技术选型是否有先例
- 需要避免已知的踩坑点
```

修改方式：
1. 通过管理后台的 Agent Profile 页面编辑
2. 或直接在数据库 `t_agent_profile` 表中更新提示词

### 测试

启动 mcp-gateway 和 ragent 后，在 Agent 对话中提问：
- "我们项目的接口返回格式规范是什么？"
- 验证 Agent 是否调用了 `search_experience` 工具

### 验收标准

Agent 对话中能看到 `search_experience` 工具被调用，返回企业经验内容。

---

## 阶段 2：元数据扩展（F5）

**目标**：知识库文档和 chunk 增加元数据字段，支持来源追踪、版本管理和矛盾标记。

### 2.1 数据库表扩展

新增 SQL 升级脚本：`resources/database/upgrades/v2.1.0/260829_chunk_metadata.sql`

```sql
-- chunk 元数据扩展
ALTER TABLE t_knowledge_document_chunk_log
    ADD COLUMN IF NOT EXISTS source_type VARCHAR(32) DEFAULT 'upload',
    ADD COLUMN IF NOT EXISTS source_ref VARCHAR(512),
    ADD COLUMN IF NOT EXISTS chunk_version INT DEFAULT 1,
    ADD COLUMN IF NOT EXISTS vote_count INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS conflict_pair_id VARCHAR(64),
    ADD COLUMN IF NOT EXISTS deprecated BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN t_knowledge_document_chunk_log.source_type IS '来源类型：upload/gitlab/api';
COMMENT ON COLUMN t_knowledge_document_chunk_log.source_ref IS '来源引用，如 gitlab://project/path/file.md';
COMMENT ON COLUMN t_knowledge_document_chunk_log.chunk_version IS 'chunk 版本号，同文件更新时递增';
COMMENT ON COLUMN t_knowledge_document_chunk_log.vote_count IS '被引用/检索命中次数';
COMMENT ON COLUMN t_knowledge_document_chunk_log.conflict_pair_id IS '矛盾对的另一个 chunk ID';
COMMENT ON COLUMN t_knowledge_document_chunk_log.deprecated IS '是否已废弃';
```

### 2.2 实体类扩展

修改文件：`rag/src/main/java/com/nageoffer/ai/ragent/knowledge/dao/entity/KnowledgeDocumentChunkLogDO.java`

```java
// 新增字段
private String sourceType;
private String sourceRef;
private Integer chunkVersion;
private Integer voteCount;
private String conflictPairId;
private Boolean deprecated;
```

### 2.3 文档上传时写入元数据

修改文件：`rag/src/main/java/com/nageoffer/ai/ragent/knowledge/service/impl/KnowledgeDocumentServiceImpl.java`

在 `upload` 方法中，从请求参数读取元数据并保存：

```java
// 在构建 KnowledgeDocumentDO 时
documentDO.setSourceType(requestParam.getSourceType());
documentDO.setSourceRef(requestParam.getSourceLocation());
```

### 测试

```bash
# 上传文档时带上元数据
curl -X POST "http://localhost:9090/api/ragent/knowledge-base/{kb_id}/docs/upload" \
  -H "Authorization: $TOKEN" \
  -F "file=@test.md" \
  -F "sourceType=gitlab" \
  -F "sourceLocation=gitlab://project/docs/test.md"

# 查询 chunk 日志，验证元数据字段
curl "http://localhost:9090/api/ragent/knowledge-base/docs/{doc_id}/chunk-logs" \
  -H "Authorization: $TOKEN"
```

### 验收标准

chunk 日志中包含 `source_type`、`source_ref`、`vote_count` 等字段。

---

## 阶段 3：向量检索接口（F6）

**目标**：暴露 HTTP 接口供 mcp-gateway 做相似 chunk 检索，用于矛盾检测。

### 3.1 新增 Controller

新增文件：`rag/src/main/java/com/nageoffer/ai/ragent/knowledge/controller/KnowledgeSearchController.java`

```java
@RestController
@RequiredArgsConstructor
public class KnowledgeSearchController {

    private final RetrievalEngine retrievalEngine;

    /**
     * 相似 chunk 检索（供外部系统调用，如矛盾检测）
     */
    @PostMapping("/knowledge-base/search/similar")
    public Result<List<Map<String, Object>>> searchSimilar(
            @RequestBody SimilarSearchRequest request) {
        // 调用向量检索引擎，返回相似 chunk
        // 包含 chunk 内容、元数据、相似度分数
        return Results.success(results);
    }
}
```

### 3.2 请求/响应定义

```java
@Data
public class SimilarSearchRequest {
    private String query;        // 检索文本
    private String kbId;         // 限定知识库（可选）
    private Integer topK = 10;   // 返回条数
    private Double threshold = 0.75; // 相似度阈值
}
```

响应格式：
```json
{
  "code": "0",
  "data": [
    {
      "chunkId": "xxx",
      "content": "chunk 内容",
      "score": 0.85,
      "metadata": {
        "sourceType": "gitlab",
        "sourceRef": "gitlab://project/docs/api.md",
        "chunkVersion": 1,
        "voteCount": 5,
        "conflictPairId": null,
        "deprecated": false
      }
    }
  ]
}
```

### 3.3 鉴权

此接口供 mcp-gateway 内部调用，建议：
1. 使用独立的 API Key 鉴权（非用户 Token）
2. 或在内网环境下开放，不对外暴露

### 测试

```bash
curl -X POST "http://localhost:9090/api/ragent/knowledge-base/search/similar" \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "接口返回格式规范", "topK": 5}'
```

### 验收标准

返回与查询语义相似的 chunk 列表，包含内容、分数和元数据。

---

## 阶段 4：引用计数接口（F7）

**目标**：暴露 HTTP 接口供 mcp-gateway 记录 chunk 被引用次数，用于投票机制。

### 4.1 新增接口

在 `KnowledgeSearchController` 中添加：

```java
/**
 * 记录 chunk 被引用（供外部系统调用，如投票机制）
 */
@PostMapping("/knowledge-base/chunks/{chunkId}/reference")
public Result<Void> recordReference(@PathVariable String chunkId) {
    // vote_count + 1
    return Results.success();
}

/**
 * 查询 chunk 投票分数
 */
@GetMapping("/knowledge-base/chunks/{chunkId}/vote")
public Result<Integer> getVoteScore(@PathVariable String chunkId) {
    return Results.success(voteCount);
}
```

### 4.2 实现

```java
// 在 Service 层
public void recordReference(String chunkId) {
    // UPDATE t_knowledge_document_chunk_log
    // SET vote_count = vote_count + 1
    // WHERE id = chunkId
}
```

### 测试

```bash
# 记录引用
curl -X POST "http://localhost:9090/api/ragent/knowledge-base/chunks/{chunkId}/reference" \
  -H "Authorization: $TOKEN"

# 查询投票分数
curl "http://localhost:9090/api/ragent/knowledge-base/chunks/{chunkId}/vote" \
  -H "Authorization: $TOKEN"
```

### 验收标准

每次调用 reference 接口后，vote 接口返回的分数递增。

---

## 目录结构变更

```
ragent/
├── resources/database/upgrades/v2.1.0/
│   └── 260829_chunk_metadata.sql          # 新增
├── rag/src/main/java/.../knowledge/
│   ├── controller/
│   │   └── KnowledgeSearchController.java  # 新增
│   └── dao/entity/
│       └── KnowledgeDocumentChunkLogDO.java # 修改：增加元数据字段
└── bootstrap/src/main/resources/
    └── application-local.yaml               # 修改：添加 MCP Gateway 配置
```

## 验收命令

```bash
# 1. 启动 ragent
cd ragent
java -jar bootstrap/target/bootstrap-0.0.1-SNAPSHOT.jar --spring.profiles.active=local

# 2. 验证 MCP 连接
curl http://localhost:9090/api/ragent/actuator/health

# 3. 测试相似检索接口
curl -X POST "http://localhost:9090/api/ragent/knowledge-base/search/similar" \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "测试", "topK": 3}'

# 4. 测试引用计数
curl -X POST "http://localhost:9090/api/ragent/knowledge-base/chunks/{chunkId}/reference" \
  -H "Authorization: $TOKEN"
```
