# Code-Mind 功能清单

> 最后更新：2026-08-29

## 核心功能

| 编号 | 功能 | 状态 | 说明 |
|------|------|------|------|
| F1 | 向量删除 | ✅ 已实现 | 删除单个/批量向量，自动删除相似向量 |
| F2 | MCP 接口发现 | ✅ 已实现 | list_mcp_tools 列出所有可用工具 |
| F3 | 提交规范文档 | ✅ 已实现 | Skills 和记忆的提交格式规范 |
| F4 | Skills 粒度优化 | ❌ 不需要 | 直接用技能名作为向量索引 |
| F5 | 矛盾审核后台 | ✅ 已实现 | 检测反义向量，人工审核 |
| F6 | 帮助文档系统 | ✅ 已实现 | AI 使用指南 |
| F7 | 元数据标记系统 | ✅ 已实现 | 模块/功能/向量三级管理 |

## MCP 工具（28 个）

### 模块管理
| 工具 | 功能 | 状态 |
|------|------|------|
| create_module | 创建模块 | ✅ |
| list_modules | 列出模块 | ✅ |
| delete_module | 删除模块（级联删除） | ✅ |

### 功能管理
| 工具 | 功能 | 状态 |
|------|------|------|
| create_feature | 创建功能（关联模块） | ✅ |
| list_features | 列出功能 | ✅ |
| delete_feature | 删除功能（级联删除） | ✅ |

### 记忆管理
| 工具 | 功能 | 状态 |
|------|------|------|
| upload_memory | 上传记忆（支持元数据） | ✅ |
| ask_project | 逐级降级检索 | ✅ |
| list_projects | 列出项目 | ✅ |
| delete_memory | 删除记忆 | ✅ |

### 技能管理
| 工具 | 功能 | 状态 |
|------|------|------|
| upload_skill | 上传技能 | ✅ |
| search_skill | 搜索技能 | ✅ |
| list_skills | 列出技能 | ✅ |
| get_skill | 获取技能详情 | ✅ |
| delete_skill | 删除技能 | ✅ |

### 知识检索
| 工具 | 功能 | 状态 |
|------|------|------|
| search_experience | 搜索企业知识库（向量检索 + AI 回答） | ✅ |

### 向量管理
| 工具 | 功能 | 状态 |
|------|------|------|
| delete_vector | 删除单个向量及相似向量 | ✅ |
| delete_vectors | 批量删除向量 | ✅ |

### 矛盾审核
| 工具 | 功能 | 状态 |
|------|------|------|
| list_conflicts | 列出待审核矛盾对 | ✅ |
| review_conflict | 审核矛盾对 | ✅ |

### 系统信息
| 工具 | 功能 | 状态 |
|------|------|------|
| list_mcp_tools | 列出所有可用工具 | ✅ |

## ragent API

### 模块 API
| 接口 | 方法 | 路径 | 状态 |
|------|------|------|------|
| 创建模块 | POST | /modules | ✅ |
| 列出模块 | GET | /modules | ✅ |
| 获取模块 | GET | /modules/{name} | ✅ |
| 删除模块 | DELETE | /modules/{name} | ✅ |

### 功能 API
| 接口 | 方法 | 路径 | 状态 |
|------|------|------|------|
| 创建功能 | POST | /feature-metadata | ✅ |
| 列出功能 | GET | /feature-metadata | ✅ |
| 获取功能 | GET | /feature-metadata/{code} | ✅ |
| 删除功能 | DELETE | /feature-metadata/{code} | ✅ |

### Chunk API
| 接口 | 方法 | 路径 | 状态 |
|------|------|------|------|
| 相似检索 | POST | /knowledge-base/search/similar | ✅ |
| 记录引用 | POST | /knowledge-base/chunks/{id}/reference | ✅ |
| 查询投票 | GET | /knowledge-base/chunks/{id}/vote | ✅ |
| 设置矛盾对 | POST | /knowledge-base/chunks/{id}/conflict-pair | ✅ |
| 标记废弃 | POST | /knowledge-base/chunks/{id}/deprecate | ✅ |
| 计算置信度 | POST | /knowledge-base/chunks/{id}/calculate-confidence | ✅ |
| 查询置信度 | GET | /knowledge-base/chunks/{id}/confidence | ✅ |
| 归一化置信度 | POST | /knowledge-base/chunks/normalize-confidence | ✅ |

## 数据库表

| 表名 | 说明 | 状态 |
|------|------|------|
| t_knowledge_chunk | 知识分块表 | ✅ |
| t_module | 模块表 | ✅ |
| t_feature_metadata | 功能元数据表 | ✅ |

### t_knowledge_chunk 扩展字段
| 字段 | 类型 | 说明 | 状态 |
|------|------|------|------|
| metadata | JSONB | 元数据（feature_codes, module） | ✅ |
| upload_count | INT | 上传次数 | ✅ |
| last_upload_at | DATETIME | 最后上传时间 | ✅ |
| confidence | INT | 置信度 | ✅ |

## 采集模块

| 模块 | 功能 | 状态 |
|------|------|------|
| gitlab_fetcher | GitLab 文件获取 | ✅ |
| github_fetcher | GitHub 文件获取 | ✅ |
| slimmer | 内容瘦身 | ✅ |
| metadata_extractor | 元数据提取 | ✅ |
| ingest_client | 文档摄入 | ✅ |
| scheduler | 采集调度 | ✅ |

## 矛盾检测模块

| 模块 | 功能 | 状态 |
|------|------|------|
| detector | 矛盾检测器 | ✅ |
| resolver | 冲突解决器 | ✅ |
| voter | 投票机制 | ✅ |
| aware_search | 矛盾感知搜索 | ✅ |

## 其他功能

| 功能 | 说明 | 状态 |
|------|------|------|
| 路径引用解析 | 上传时自动匹配路径引用 | ✅ |
| 逐级降级检索 | 功能级→模块级→全库 | ✅ |
| 置信度评分 | 基于上传次数和时间 | ✅ |
| AI 自动清理 | 查询后自动删除错误向量 | ✅ |

## 测试状态

| 测试类型 | 数量 | 状态 |
|----------|------|------|
| 单元测试 | 172 | ✅ 通过 |
| 集成测试 | 28 | ✅ 通过 |
| 综合测试 | 7 | ⚠️ 部分通过 |
| 问题修复测试 | 4 | ⚠️ 部分通过 |

### 测试脚本

| 脚本 | 覆盖内容 |
|------|---------|
| test_comprehensive.py | 中文编码、中文搜索、Module/Feature CRUD、置信度计算、逐级降级检索、元数据存储、删除操作 |
| test_issues_fix.py | 中文编码问题、中文LIKE搜索问题、Module/Feature API问题、置信度API问题 |

### 测试脚本

| 脚本 | 覆盖内容 |
|------|---------|
| test_comprehensive.py | 中文编码、中文搜索、Module/Feature CRUD、置信度计算、逐级降级检索、元数据存储、删除操作 |
| test_issues_fix.py | 中文编码问题、中文LIKE搜索问题、Module/Feature API问题、置信度API问题 |

## 已知问题

| 问题 | 说明 | 状态 |
|------|------|------|
| 中文 LIKE 检索不准确 | 使用向量检索替代 | ⚠️ 已知 |
| RocketMQ 编码问题 | 中文内容可能乱码 | ⚠️ 已知 |

## 待实现功能

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 向量检索优化 | P0 | 将 LIKE 检索改为向量检索 |
| 知识快照 | P1 | 按功能生成本地快照 |
| 前端管理界面 | P2 | 模块/功能/向量管理 |
| GitLab/GitHub 集成 | P2 | 自动采集文档 |
