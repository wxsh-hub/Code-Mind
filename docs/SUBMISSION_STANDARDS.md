# Code-Mind 提交规范

## Skills 提交规范

### 格式要求
- 文件必须是 Markdown 格式
- 必须包含标题（# 开头）
- 必须包含分类（category）
- 建议包含标签（tags）

### 分类标准
| 分类 | 说明 | 示例 |
|------|------|------|
| coding | 编码规范、代码模板 | Java 命名规范、Git 提交规范 |
| testing | 测试指南、测试模板 | 单元测试指南、集成测试模板 |
| deployment | 部署流程、配置模板 | Docker 部署、K8s 配置 |
| architecture | 架构设计、技术选型 | 微服务架构、数据库设计 |
| workflow | 工作流程、协作规范 | 代码审查流程、发布流程 |

### 示例格式
```markdown
# Java 单元测试规范

## Description
Java 项目单元测试编写规范

## Metadata
- Category: testing
- Tags: java, junit, testing

## Content
### 测试类命名
- 类名：{ClassName}Test
- 方法名：test_{method}_{scenario}

### 测试结构
```java
@Test
void testGetUserById_found() {
    // Given
    Long userId = 1L;
    when(userMapper.selectById(userId)).thenReturn(new User());

    // When
    User result = userService.getUserById(userId);

    // Then
    assertNotNull(result);
}
```
```

## 记忆提交规范

### 应该提交
| 类型 | 说明 | 示例 |
|------|------|------|
| 项目状态 | 模块完成度、已知问题 | "RAG 模块完成度 90%" |
| 架构决策 | 技术选型、设计方案 | "选择 pgvector 而非 Milvus" |
| 经验总结 | 踩坑记录、最佳实践 | "中文编码需要 UTF-8" |
| 模块关系 | 依赖关系、接口说明 | "MCP Gateway 调用 ragent API" |

### 不应该提交
| 类型 | 说明 | 原因 |
|------|------|------|
| 临时调试日志 | 调试过程中的输出 | 无价值 |
| 个人笔记 | 未验证的内容 | 可能误导 |
| 敏感信息 | 密码、密钥、Token | 安全风险 |
| 过期内容 | 已废弃的功能 | 误导 |
| 临时代码片段 | 测试代码 | 不完整 |

### 格式要求

#### 记忆文件格式
```markdown
# {功能编号}: {功能名称}

## 状态
- 完成度: 100%
- 最后更新: 2026-08-29

## 实现内容
- 新增用户接口
- 编辑用户接口

## 已知问题
- 删除用户时需要级联删除关联数据

## 相关文件
- mcp_gateway/user_module.py
- src/main/java/UserController.java
```

#### 多功能记忆文件格式
```markdown
# 项目记忆

## 2437: 人员管理
实现了用户增删改查功能...

## 2438: 权限管理
实现了基于角色的权限控制...
```

## 提交顺序

### 正确顺序
1. **先提交 Skills**（代码、规范、指南）
2. **再提交记忆**（状态、经验、总结）

### 原因
记忆中可能引用 skills 的路径（如 `mcp_gateway/rag_client.py`），先提交 skills 后提交记忆可以让路径引用匹配成功。

## 功能编号规范

### 编号格式
- 使用数字编号，如 2437、2438
- 每个功能有唯一编号
- 编号由项目管理员分配

### 模块命名
- 使用小写英文，如 user、order、payment
- 模块是功能的集合
- 每个功能必须关联一个模块

## 元数据使用规范

### 上传时添加元数据
```python
# 上传记忆（带元数据）
upload_memory(
    project="Code-Mind",
    filename="2437_人员管理.md",
    content="...",
    feature_codes=["2437"],
    module="user"
)

# 上传技能（带元数据）
upload_skill(
    project="Code-Mind",
    skill_name="用户管理指南",
    content="...",
    feature_codes=["2437"],
    module="user"
)
```

### 查询时使用元数据
```python
# 按功能查询
ask_project(
    project="Code-Mind",
    question="如何添加用户",
    feature_codes=["2437"]
)

# 按模块查询
ask_project(
    project="Code-Mind",
    question="用户相关功能",
    module="user"
)

# 逐级降级检索
ask_project(
    project="Code-Mind",
    question="如何添加用户",
    feature_codes=["2437"],
    module="user"
)
# 检索顺序：功能级 → 模块级 → 全库
```
