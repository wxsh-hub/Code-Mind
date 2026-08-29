---
name: metadata-status
description: 元数据扩展状态
metadata:
  type: project
---

# 元数据扩展状态

## 状态
- 完成度：100%
- 最后更新：2026-08-29

## 数据库扩展

### t_knowledge_chunk 新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| metadata | JSONB | 元数据（feature_codes, module） |
| upload_count | INT | 上传次数 |
| last_upload_at | DATETIME | 最后上传时间 |
| confidence | INT | 置信度 |

### metadata JSONB 结构

```json
{
    "feature_codes": ["2437", "2438"],
    "module": "user",
    "type": "api",
    "version": "1.0"
}
```

## 新增表

### t_module（模块表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(64) | 主键 |
| name | VARCHAR(64) | 模块名称（唯一） |
| description | TEXT | 模块描述 |
| created_by | VARCHAR(64) | 创建人 |
| created_at | DATETIME | 创建时间 |

### t_feature_metadata（功能元数据表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(64) | 主键 |
| feature_code | VARCHAR(32) | 功能编号（唯一） |
| feature_name | VARCHAR(128) | 功能名称 |
| module_name | VARCHAR(64) | 所属模块 |
| description | TEXT | 功能描述 |
| status | VARCHAR(16) | 状态（active/deprecated） |

## 索引

```sql
CREATE INDEX idx_kc_metadata ON t_knowledge_chunk USING GIN (metadata);
CREATE INDEX idx_kc_upload_count ON t_knowledge_chunk(upload_count);
CREATE INDEX idx_kc_last_upload ON t_knowledge_chunk(last_upload_at);
CREATE INDEX idx_module_name ON t_module(name);
CREATE INDEX idx_fm_feature_code ON t_feature_metadata(feature_code);
CREATE INDEX idx_fm_module_name ON t_feature_metadata(module_name);
```

## 迁移脚本

- `resources/database/upgrades/v2.1.0/260829_chunk_metadata.sql`
- `resources/database/upgrades/v2.1.0/260829_chunk_confidence.sql`
- `resources/database/upgrades/v2.1.0/260829_module_feature.sql`
