-- 添加置信度字段到知识分块表
-- 置信度基于语义相似向量的提交次数，用于衡量知识的可信度

ALTER TABLE t_knowledge_chunk
    ADD COLUMN IF NOT EXISTS confidence INT DEFAULT 1 COMMENT '置信度分数（相似向量提交次数）';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_kc_confidence ON t_knowledge_chunk(confidence);
