# 测试指南

## 测试矩阵

| 测试脚本 | 覆盖范围 | 依赖 | 运行命令 |
|----------|----------|------|----------|
| `test_rag_flow.sh` | 登录→知识库→文档→分块→问答 | ragent 运行中 | `bash test_rag_flow.sh` |
| `test_chunk_api.sh` | 相似检索→引用计数→矛盾标记→废弃 | ragent 运行中 | `bash test_chunk_api.sh` |
| `mcp-gateway/tests/` | MCP Gateway 全模块 | Python 环境 | `cd mcp-gateway && pytest tests/ -v` |

## 运行测试

### 前置条件

```bash
# 1. Docker 服务运行
docker ps  # 确认 postgres、redis、rocketmq、rustfs 正常

# 2. ragent 应用运行
java -jar bootstrap/target/bootstrap-0.0.1-SNAPSHOT.jar --spring.profiles.active=local

# 3. 等待启动完成
curl http://localhost:9090/api/ragent/actuator/health
# 返回 {"code":"A000001","message":"未登录或登录已过期"} 表示正常
```

### 执行测试

```bash
cd D:/11111111111/AAAworkAAA/ragent

# RAG 全流程测试
bash test_rag_flow.sh
# 预期：8 通过, 0 失败

# Chunk API 测试
bash test_chunk_api.sh
# 预期：12 通过, 0 失败
```

## 测试覆盖清单

### RAG 全流程 (`test_rag_flow.sh`)

| # | 测试项 | 说明 |
|---|--------|------|
| 1 | 登录获取 Token | admin/admin 登录 |
| 2 | 创建知识库 | embeddingModel=qwen-emb-8b |
| 3 | 上传文档 | Markdown 文件上传 |
| 4 | 触发分块 | 调用 chunk 接口 |
| 5 | 分块状态 | status=success |
| 6 | 分块数量 | chunkCount > 0 |
| 7 | RAG 问答 | SSE 流式返回答案 |
| 8 | 来源引用 | 返回 finish 事件 |

### Chunk API (`test_chunk_api.sh`)

| # | 测试项 | 说明 |
|---|--------|------|
| 1 | 登录获取 Token | admin/admin 登录 |
| 2 | 创建知识库 | 唯一名称 |
| 3 | 上传文档 | Markdown 文件 |
| 4 | 触发分块 | chunk 接口 |
| 5 | 查询分块列表 | 获取 ChunkID |
| 6 | 相似检索成功 | POST /search/similar |
| 7 | 相似检索数据 | 返回 chunkId |
| 8 | 初始投票分数 | vote=0 |
| 9 | 引用3次后 | vote=3 |
| 10 | 设置矛盾对 | conflict-pair 接口 |
| 11 | 标记废弃 | deprecate 接口 |
| 12 | 验证废弃状态 | deprecated=true |

## 验收标准

**所有测试必须 100% 通过才能提交代码。**

```bash
# 验收命令
bash test_rag_flow.sh && bash test_chunk_api.sh && echo "✅ 验收通过"
```
