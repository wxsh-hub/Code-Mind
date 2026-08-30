# Code-Mind 测试指南

## 测试文件清单

### 测试数据（仿造的企业知识文件）

| 文件 | 内容 | 分类 |
|------|------|------|
| `test_data/编码规范_Java.md` | Java 命名、格式、异常、注释规范 | 编码规范 |
| `test_data/编码规范_数据库.md` | 表设计、索引、SQL、MyBatis 规范 | 编码规范 |
| `test_data/编码规范_Git.md` | 分支管理、Commit 规范、代码审查 | 编码规范 |
| `test_data/项目经验_分页实现.md` | 深分页、游标分页、MyBatis Plus 分页 | 项目经验 |
| `test_data/项目经验_缓存设计.md` | 缓存穿透、击穿、雪崩、一致性 | 项目经验 |
| `test_data/架构设计_微服务.md` | Spring Cloud、服务通信、分布式事务 | 架构设计 |
| `test_data/架构设计_数据库.md` | 读写分离、分库分表、分布式 ID | 架构设计 |

### 测试脚本

| 脚本 | 用途 | 依赖 |
|------|------|------|
| `test_mcp_gateway.bat` | MCP Gateway 单元测试（Windows） | 无 |
| `test_mcp_gateway.sh` | MCP Gateway 单元测试（Linux/Mac） | 无 |
| `test_integration.sh` | 全链路集成测试 | ragent 运行中 |

### 单元测试文件

| 文件 | 测试数 | 测试内容 |
|------|--------|----------|
| `tests/test_rag_client.py` | 4 | RAG HTTP 客户端 |
| `tests/test_rag_tools.py` | 4 | search_experience MCP Tool |
| `tests/test_collector.py` | 9 | 内容瘦身、元数据提取 |
| `tests/test_conflict.py` | 16 | 矛盾检测、冲突解决、投票 |
| **总计** | **33** | **全部通过** |

---

## 测试流程

### 1. 独立测试（不需要 ragent）

```bash
# Windows
test_mcp_gateway.bat

# Linux/Mac
chmod +x test_mcp_gateway.sh
./test_mcp_gateway.sh
```

**预期结果**：33 个测试全部通过

### 2. 集成测试（需要 ragent 运行）

#### 前置条件
1. 启动 ragent 服务（`http://localhost:9090`）
2. 确保 PostgreSQL + pgvector 运行中
3. 确保 embedding 模型可用

#### 运行测试
```bash
# Linux/Mac/Git Bash
chmod +x test_integration.sh
./test_integration.sh
```

**预期结果**：
- 创建知识库成功
- 上传 7 个知识文件成功
- 分块和向量化成功
- 相似检索返回相关结果
- 引用计数正常工作
- RAG 问答返回正确答案
- 矛盾文档可被检索

---

## 测试覆盖的关键节点

### 1. 文档上传和分块
- ✅ 创建知识库
- ✅ 上传 Markdown 文件
- ✅ 触发分块
- ✅ 验证分块状态

### 2. 向量检索
- ✅ 相似 chunk 搜索
- ✅ 关键词匹配
- ✅ 元数据返回

### 3. 投票机制
- ✅ 记录引用（vote_count + 1）
- ✅ 查询投票分数
- ✅ 批量引用

### 4. 矛盾检测
- ✅ 否定模式检测（应该 vs 不应该）
- ✅ 跳过已废弃 chunk
- ✅ 跳过自身
- ✅ 冲突解决策略

### 5. RAG 问答
- ✅ Java 编码规范问答
- ✅ 分页优化问答
- ✅ 缓存设计问答

### 6. MCP Tool
- ✅ search_experience 工具注册
- ✅ 搜索结果格式化
- ✅ 自动记录引用
- ✅ 错误处理

---

## 仿造知识文件说明

### 编码规范类
- **Java 规范**：命名、格式、异常处理、注释规范
- **数据库规范**：表设计、索引、SQL 优化、MyBatis
- **Git 规范**：分支管理、Commit 格式、代码审查

### 项目经验类
- **分页实现**：深分页问题、游标分页、延迟关联
- **缓存设计**：缓存穿透、击穿、雪崩、一致性

### 架构设计类
- **微服务架构**：Spring Cloud、服务通信、分布式事务
- **数据库架构**：读写分离、分库分表、分布式 ID

这些文件模拟了企业内部的知识库内容，覆盖了：
- 编码规范（长期有效）
- 项目经验（可更新）
- 架构设计（参考价值）

---

## 测试场景示例

### 场景 1：新员工查询编码规范
```
Agent 调用 search_experience("Java 类名应该怎么命名")
→ 返回：使用 PascalCase，如 UserService、OrderController
```

### 场景 2：查询分页优化方案
```
Agent 调用 search_experience("深分页怎么优化")
→ 返回：游标分页、延迟关联、缓存总数等方案
```

### 场景 3：查询缓存设计
```
Agent 调用 search_experience("缓存穿透怎么解决")
→ 返回：缓存空值、布隆过滤器等方案
```

### 场景 4：矛盾内容检测
```
上传新文档："不应该使用缓存空值"
→ 检测到与已有文档矛盾
→ 标记矛盾对，保留两个版本
```

---

## 常见问题

### Q: 测试失败怎么办？
A: 检查：
1. Python 版本 >= 3.10
2. 依赖已安装：`pip install -e ".[dev]"`
3. ragent 服务运行中（集成测试）

### Q: 如何添加新的测试知识文件？
A: 在 `test_data/` 目录下创建 `.md` 文件，重新运行集成测试

### Q: 如何测试 MCP Gateway 启动？
A: 需要创建 `mcp.json` 配置文件，然后运行：
```bash
mcp-gateway --mcp-json-path mcp.json
```

---

## 下一步

1. **运行独立测试**：`test_mcp_gateway.bat` 验证 33 个单元测试
2. **启动 ragent**：确保服务运行在 `http://localhost:9090`
3. **运行集成测试**：`test_integration.sh` 验证全链路
4. **验证 RAG 效果**：检查问答结果是否准确
