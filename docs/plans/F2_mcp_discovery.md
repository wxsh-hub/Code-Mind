# F2 MCP 接口动态发现

## 目标
暴露 `/mcp/tools` 接口，让 AI 知道有哪些 MCP 工具可用，包括名称、描述、参数。

## 实现思路

### 1. MCP Gateway 侧（Python）

在 gateway.py 中新增内置工具：

```python
@mcp.tool()
async def list_mcp_tools(ctx: Context) -> dict:
    """列出所有可用的 MCP 工具"""
    # 返回所有注册的工具列表
```

### 2. 工具元数据格式

```json
{
  "tools": [
    {
      "name": "search_experience",
      "description": "搜索企业项目经验和编码规范",
      "parameters": {
        "query": {"type": "string", "required": true, "description": "搜索内容"},
        "kb_id": {"type": "string", "required": false, "description": "限定知识库"},
        "top_k": {"type": "integer", "required": false, "description": "返回数量"}
      }
    },
    {
      "name": "upload_memory",
      "description": "上传项目记忆文件",
      "parameters": {
        "project": {"type": "string", "required": true},
        "filename": {"type": "string", "required": true},
        "content": {"type": "string", "required": true}
      }
    }
  ]
}
```

### 3. 分类展示

按类别分组：
- **记忆管理**: upload_memory, ask_project, list_projects
- **技能管理**: upload_skill, search_skill, list_skills, get_skill
- **知识检索**: search_experience
- **系统信息**: list_mcp_tools, get_metadata

### 4. 帮助文档集成

list_mcp_tools 返回结果中包含：
- 工具列表
- 使用示例
- 提交规范摘要

## 测试脚本思路

### test_mcp_discovery.sh

```
1. 启动 MCP Gateway
2. 调用 list_mcp_tools
3. 验证返回格式正确
4. 验证包含所有已注册工具
5. 验证每个工具有 name、description、parameters
6. 验证 parameters 包含 required 字段
```

### 单元测试 test_mcp_discovery.py

```python
class TestMCPDiscovery:
    def test_list_tools_returns_all(self):
        # 验证返回所有注册的工具

    def test_tool_has_metadata(self):
        # 验证每个工具有 name、description

    def test_tool_parameters(self):
        # 验证参数格式正确

    def test_categories(self):
        # 验证分类正确
```

## 依赖
- 无外部依赖，纯 MCP Gateway 实现
