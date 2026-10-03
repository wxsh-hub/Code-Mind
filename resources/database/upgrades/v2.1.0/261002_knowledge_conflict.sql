-- 矛盾审核模块
--
-- 背景：矛盾检测原先只有 t_knowledge_chunk.conflict_pair_id 一个字段，
-- 只写不读——提交上去的矛盾没有任何地方能看到，也没有原因与处置建议的记录，
-- 后台「矛盾审核」页调的是外部 MCP Gateway 的接口，那套没部署到本仓库后端。
-- 本脚本补一张独立的矛盾记录表，并让「废弃」在向量检索侧真正生效。
--
-- 对已存在的环境执行本脚本是幂等的（IF NOT EXISTS）。

-- ============================================
-- 1. 向量表补 deprecated 列
-- ============================================
-- 此前「废弃」只写在 t_knowledge_chunk.deprecated 上，而向量检索查的是
-- t_knowledge_vector（SQL 无任何过滤条件），因此废弃标记对检索毫无影响。
-- 要让它生效，标记必须落到检索真正读的那张表上。
ALTER TABLE t_knowledge_vector
    ADD COLUMN IF NOT EXISTS deprecated BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN t_knowledge_vector.deprecated IS '是否已废弃：为真时不参与向量检索';

-- 检索按 collection_name 过滤后再排除废弃，联合索引覆盖这个组合
CREATE INDEX IF NOT EXISTS idx_kv_collection_deprecated
    ON t_knowledge_vector (collection_name, deprecated);

-- ============================================
-- 2. 矛盾记录表
-- ============================================
CREATE TABLE IF NOT EXISTS t_knowledge_conflict (
    id               VARCHAR(20) NOT NULL PRIMARY KEY,
    kb_id            VARCHAR(20) NOT NULL,
    chunk_id         VARCHAR(20) NOT NULL,
    related_chunk_id VARCHAR(20),
    chunk_content    TEXT,
    reason           TEXT        NOT NULL,
    suggestion       TEXT,
    status           VARCHAR(16) NOT NULL DEFAULT 'PENDING',
    submitted_by     VARCHAR(64),
    reviewed_by      VARCHAR(64),
    review_comment   TEXT,
    review_time      TIMESTAMP,
    create_time      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted          SMALLINT    NOT NULL DEFAULT 0
);

COMMENT ON TABLE  t_knowledge_conflict IS '知识矛盾记录：由 AI 或人工提出，后台审核后处置';
COMMENT ON COLUMN t_knowledge_conflict.kb_id IS '所属知识库';
COMMENT ON COLUMN t_knowledge_conflict.chunk_id IS '被质疑的知识分块 ID';
COMMENT ON COLUMN t_knowledge_conflict.related_chunk_id IS '与哪一条冲突，可为空（仅指出本条有误时）';
COMMENT ON COLUMN t_knowledge_conflict.chunk_content IS '提交时被质疑分块的原文快照，审核时对照用';
COMMENT ON COLUMN t_knowledge_conflict.reason IS '矛盾原因：为什么认为这条不对';
COMMENT ON COLUMN t_knowledge_conflict.suggestion IS '建议改成什么，接受审核时用它替换原文';
COMMENT ON COLUMN t_knowledge_conflict.status IS '审核状态：PENDING 待审核 / ACCEPTED 已接受 / REJECTED 已拒绝';
COMMENT ON COLUMN t_knowledge_conflict.review_comment IS '审核意见';
COMMENT ON COLUMN t_knowledge_conflict.review_time IS '审核时间';

-- 后台默认按「待审核」筛选后按时间倒序翻页
CREATE INDEX IF NOT EXISTS idx_kconflict_status_time
    ON t_knowledge_conflict (status, create_time DESC);
-- 同一条知识重复提交时去重用
CREATE INDEX IF NOT EXISTS idx_kconflict_chunk
    ON t_knowledge_conflict (chunk_id);
