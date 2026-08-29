# 开发规范

## 功能开发流程

每次完成功能开发后，必须完成以下四步：

### 1. 编写自动化测试

- 每个新功能必须有对应的单元测试
- 测试文件放在 `tests/` 目录下，命名为 `test_*.py`
- 运行测试确认全部通过：`python -m pytest tests/ -v`
- 集成测试脚本放在项目根目录：`test_*.sh`

### 2. 更新持久化记忆

- 更新 `docs/memory/` 下的相关记忆文件
- 新功能需要记录：功能说明、API 清单、测试状态
- 记忆文件格式：
  ```markdown
  ---
  name: feature-name
  description: 功能描述
  metadata:
    type: project
  ---
  
  # 功能名称
  
  ## 状态
  - 完成度：100%
  - 最后更新：2026-08-29
  
  ## 功能说明
  ...
  
  ## API 清单
  ...
  
  ## 测试状态
  ...
  ```

### 3. 更新帮助文档

- 新功能或更改必须更新 `docs/HELP_SYSTEM.md`
- 更新内容：
  - 可用工具表格
  - 使用示例
  - 常见问题（如有新问题）

### 4. 更新功能清单

- 新功能必须在 `docs/FEATURES.md` 中添加
- 删除功能必须在 `docs/FEATURES.md` 中标记或删除
- 更新内容：
  - 功能表格
  - MCP 工具表格
  - API 表格
  - 测试状态

## 测试要求

### 单元测试
- 每个模块必须有对应的测试文件
- 测试覆盖主要功能和边界情况
- 测试必须全部通过才能提交

### 集成测试
- 全流程测试：登录 → 创建 → 操作 → 验证 → 清理
- 测试脚本：`test_final.sh`
- 测试结果：28 个检查点全部通过

## 记忆文件位置

```
D:\11111111111\AAAworkAAA\ragent\docs\memory\
├── MEMORY.md              # 项目总览
├── QUICK_START.md         # 快速入门
├── mcp-gateway-status.md  # MCP Gateway 状态
├── rag-status.md          # RAG 状态
├── chunk-api-status.md    # Chunk API 状态
├── metadata-status.md     # 元数据状态
├── integration-design.md  # 集成设计
└── mcp-gateway-files.md   # 文件位置索引
```

## 帮助文档位置

```
D:\11111111111\AAAworkAAA\mcp-gateway\docs\HELP_SYSTEM.md
```

## 提交规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
test: 测试相关
```

## 检查清单

完成功能开发后，检查以下项目：

- [ ] 单元测试编写完成
- [ ] 单元测试全部通过
- [ ] 集成测试全部通过
- [ ] 持久化记忆已更新
- [ ] 帮助文档已更新
- [ ] 功能清单已更新（docs/FEATURES.md）
- [ ] 代码已提交推送
