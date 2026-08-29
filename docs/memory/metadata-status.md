# 元数据扩展状态

## 状态
- 完成度：100%
- 最后更新：2026-08-29

## 数据库变更

### 新增字段（t_knowledge_chunk 表）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| source_type | VARCHAR(32) | 'upload' | 来源类型：upload/gitlab/api |
| source_ref | VARCHAR(512) | NULL | 来源引用，如 gitlab://project/path/file.md |
| chunk_version | INT | 1 | chunk 版本号，同文件更新时递增 |
| vote_count | INT | 0 | 被引用/检索命中次数 |
| conflict_pair_id | VARCHAR(64) | NULL | 矛盾对的另一个 chunk ID |
| deprecated | BOOLEAN | FALSE | 是否已废弃 |

### 新增索引
- `idx_kc_source_ref`：加速按来源查询
- `idx_kc_conflict_pair`：加速按矛盾对查询

## 实体类变更

### KnowledgeChunkDO 新增字段
```java
private String sourceType;
private String sourceRef;
private Integer chunkVersion;
private Integer voteCount;
private String conflictPairId;
private Boolean deprecated;
```

### KnowledgeChunkVO 新增字段
```java
private String sourceType;
private String sourceRef;
private Integer chunkVersion;
private Integer voteCount;
private String conflictPairId;
private Boolean deprecated;
```

## 迁移脚本
- `resources/database/upgrades/v2.1.0/260829_chunk_metadata.sql`

## 测试验证
- SQL 执行成功
- 实体类编译通过
- API 测试通过（12/12）

## 相关文件
- `resources/database/upgrades/v2.1.0/260829_chunk_metadata.sql`
- `rag/src/main/java/.../knowledge/dao/entity/KnowledgeChunkDO.java`
- `rag/src/main/java/.../knowledge/controller/vo/KnowledgeChunkVO.java`
