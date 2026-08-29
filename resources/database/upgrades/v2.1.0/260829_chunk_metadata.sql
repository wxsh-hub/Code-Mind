-- chunk 元数据扩展：支持来源追踪、版本管理和矛盾标记
-- 用于 MCP Gateway 的矛盾检测和投票机制

ALTER TABLE t_knowledge_chunk
    ADD COLUMN IF NOT EXISTS source_type VARCHAR(32) DEFAULT 'upload',
    ADD COLUMN IF NOT EXISTS source_ref VARCHAR(512),
    ADD COLUMN IF NOT EXISTS chunk_version INT DEFAULT 1,
    ADD COLUMN IF NOT EXISTS vote_count INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS conflict_pair_id VARCHAR(64),
    ADD COLUMN IF NOT EXISTS deprecated BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN t_knowledge_chunk.source_type IS '来源类型：upload/gitlab/api';
COMMENT ON COLUMN t_knowledge_chunk.source_ref IS '来源引用，如 gitlab://project/path/file.md';
COMMENT ON COLUMN t_knowledge_chunk.chunk_version IS 'chunk 版本号，同文件更新时递增';
COMMENT ON COLUMN t_knowledge_chunk.vote_count IS '被引用/检索命中次数';
COMMENT ON COLUMN t_knowledge_chunk.conflict_pair_id IS '矛盾对的另一个 chunk ID';
COMMENT ON COLUMN t_knowledge_chunk.deprecated IS '是否已废弃';

-- 索引：加速按来源和矛盾对查询
CREATE INDEX IF NOT EXISTS idx_kc_source_ref ON t_knowledge_chunk(source_ref);
CREATE INDEX IF NOT EXISTS idx_kc_conflict_pair ON t_knowledge_chunk(conflict_pair_id);
