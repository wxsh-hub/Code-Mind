-- 补齐升级脚本遗漏的列
--
-- 背景：以下 5 列此前只存在于开发者的本地库中（由手工 ALTER 添加），
-- 既没有写进 schema_pg.sql，也没有对应的升级脚本。后果是按文档用
-- schema_pg.sql + init_data_pg.sql 初始化的新环境会缺这些列，
-- 表现为运行时 BadSqlGrammarException（如 t_knowledge_document.feature_codes）。
-- 本脚本把它们固化下来，使新环境与既有环境结构一致。
--
-- 对已存在的环境执行本脚本是幂等的（IF NOT EXISTS）。

-- 文档表：模块与功能编号归属，用于按元数据检索
ALTER TABLE t_knowledge_document
    ADD COLUMN IF NOT EXISTS feature_codes VARCHAR(256),
    ADD COLUMN IF NOT EXISTS module VARCHAR(128);

COMMENT ON COLUMN t_knowledge_document.feature_codes IS '关联的功能编号，逗号分隔，如 2437,2438';
COMMENT ON COLUMN t_knowledge_document.module IS '所属模块名称';

-- 向量表：置信度与上传统计，与 t_knowledge_chunk 的同名列保持一致
ALTER TABLE t_knowledge_vector
    ADD COLUMN IF NOT EXISTS confidence INT DEFAULT 1,
    ADD COLUMN IF NOT EXISTS upload_count INT DEFAULT 1,
    ADD COLUMN IF NOT EXISTS last_upload_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

COMMENT ON COLUMN t_knowledge_vector.confidence IS '置信度分数（相似向量提交次数）';
COMMENT ON COLUMN t_knowledge_vector.upload_count IS '上传次数';
COMMENT ON COLUMN t_knowledge_vector.last_upload_at IS '最后上传时间';
