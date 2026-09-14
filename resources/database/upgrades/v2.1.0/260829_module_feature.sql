-- 模块表
CREATE TABLE IF NOT EXISTS t_module (
    id          VARCHAR(64)  NOT NULL PRIMARY KEY,
    name        VARCHAR(64)  NOT NULL,
    description TEXT,
    created_by  VARCHAR(64),
    create_time TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted     SMALLINT     NOT NULL DEFAULT 0,
    CONSTRAINT uk_module_name UNIQUE (name)
);
CREATE INDEX IF NOT EXISTS idx_module_name ON t_module(name);
CREATE INDEX IF NOT EXISTS idx_module_deleted ON t_module(deleted);
COMMENT ON TABLE t_module IS '模块表';
COMMENT ON COLUMN t_module.name IS '模块名称，如 user、order、payment';
COMMENT ON COLUMN t_module.description IS '模块描述';
COMMENT ON COLUMN t_module.created_by IS '创建人';
COMMENT ON COLUMN t_module.update_time IS '更新时间，由应用层 MyMetaObjectHandler 维护';

-- 功能元数据表
CREATE TABLE IF NOT EXISTS t_feature_metadata (
    id           VARCHAR(64)  NOT NULL PRIMARY KEY,
    feature_code VARCHAR(32)  NOT NULL,
    feature_name VARCHAR(128) NOT NULL,
    module_name  VARCHAR(64),
    description  TEXT,
    status       VARCHAR(16)  NOT NULL DEFAULT 'active',
    created_by   VARCHAR(64),
    create_time  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted      SMALLINT     NOT NULL DEFAULT 0,
    CONSTRAINT uk_feature_code UNIQUE (feature_code)
);
CREATE INDEX IF NOT EXISTS idx_fm_feature_code ON t_feature_metadata(feature_code);
CREATE INDEX IF NOT EXISTS idx_fm_module_name ON t_feature_metadata(module_name);
CREATE INDEX IF NOT EXISTS idx_fm_deleted ON t_feature_metadata(deleted);
COMMENT ON TABLE t_feature_metadata IS '功能元数据表';
COMMENT ON COLUMN t_feature_metadata.feature_code IS '功能编号，如 2437';
COMMENT ON COLUMN t_feature_metadata.module_name IS '所属模块名称';
COMMENT ON COLUMN t_feature_metadata.status IS '状态：active/deprecated';
COMMENT ON COLUMN t_feature_metadata.update_time IS '更新时间，由应用层 MyMetaObjectHandler 维护';

-- 向量元数据字段扩展
ALTER TABLE t_knowledge_chunk
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

ALTER TABLE t_knowledge_chunk
    ADD COLUMN IF NOT EXISTS upload_count INT DEFAULT 1,
    ADD COLUMN IF NOT EXISTS last_upload_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

COMMENT ON COLUMN t_knowledge_chunk.metadata IS '扩展元数据，如 {"feature_codes": ["2437"], "module": "user"}';
COMMENT ON COLUMN t_knowledge_chunk.upload_count IS '上传次数';
COMMENT ON COLUMN t_knowledge_chunk.last_upload_at IS '最后上传时间';

CREATE INDEX IF NOT EXISTS idx_kc_metadata ON t_knowledge_chunk USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_kc_upload_count ON t_knowledge_chunk(upload_count);
CREATE INDEX IF NOT EXISTS idx_kc_last_upload ON t_knowledge_chunk(last_upload_at);
