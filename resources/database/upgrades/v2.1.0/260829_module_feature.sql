-- 模块表
CREATE TABLE IF NOT EXISTS t_module (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(64) NOT NULL UNIQUE COMMENT '模块名称，如 user、order、payment',
    description TEXT COMMENT '模块描述',
    created_by VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_module_name ON t_module(name);

-- 功能元数据表
CREATE TABLE IF NOT EXISTS t_feature_metadata (
    id VARCHAR(64) PRIMARY KEY,
    feature_code VARCHAR(32) NOT NULL UNIQUE COMMENT '功能编号，如 2437',
    feature_name VARCHAR(128) NOT NULL COMMENT '功能名称',
    module_name VARCHAR(64) COMMENT '所属模块名称',
    description TEXT COMMENT '功能描述',
    status VARCHAR(16) DEFAULT 'active' COMMENT '状态：active/deprecated',
    created_by VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_fm_feature_code ON t_feature_metadata(feature_code);
CREATE INDEX IF NOT EXISTS idx_fm_module_name ON t_feature_metadata(module_name);

-- 向量元数据字段扩展
ALTER TABLE t_knowledge_chunk
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

ALTER TABLE t_knowledge_chunk
    ADD COLUMN IF NOT EXISTS upload_count INT DEFAULT 1 COMMENT '上传次数',
    ADD COLUMN IF NOT EXISTS last_upload_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '最后上传时间';

CREATE INDEX IF NOT EXISTS idx_kc_metadata ON t_knowledge_chunk USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_kc_upload_count ON t_knowledge_chunk(upload_count);
CREATE INDEX IF NOT EXISTS idx_kc_last_upload ON t_knowledge_chunk(last_upload_at);
