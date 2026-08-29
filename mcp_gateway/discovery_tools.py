"""
Discovery MCP Tools - MCP 接口发现工具

支持：
- list_mcp_tools: 列出所有可用的 MCP 工具
"""

import logging
import json
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# 工具分类
TOOL_CATEGORIES = {
    "module_management": {
        "name": "模块管理",
        "tools": ["create_module", "list_modules", "delete_module"],
    },
    "feature_management": {
        "name": "功能管理",
        "tools": ["create_feature", "list_features", "delete_feature"],
    },
    "memory_management": {
        "name": "记忆管理",
        "tools": ["upload_memory", "ask_project", "list_projects", "delete_memory"],
    },
    "skill_management": {
        "name": "技能管理",
        "tools": ["upload_skill", "search_skill", "list_skills", "get_skill", "delete_skill"],
    },
    "knowledge_search": {
        "name": "知识检索",
        "tools": ["search_experience"],
    },
    "system": {
        "name": "系统信息",
        "tools": ["list_mcp_tools", "get_metadata"],
    },
}


def list_mcp_tools_impl(categorized: bool = True) -> Dict[str, Any]:
    """列出所有可用的 MCP 工具

    Args:
        categorized: 是否按分类分组（默认 True）

    Returns:
        工具列表
    """
    # 收集所有工具信息
    all_tools = []

    # 模块管理
    all_tools.extend([
        {
            "name": "create_module",
            "description": "创建模块",
            "category": "module_management",
            "parameters": {
                "project": {"type": "string", "required": True, "description": "项目名称"},
                "name": {"type": "string", "required": True, "description": "模块名称"},
                "description": {"type": "string", "required": False, "description": "模块描述"},
            },
        },
        {
            "name": "list_modules",
            "description": "列出所有模块",
            "category": "module_management",
            "parameters": {
                "project": {"type": "string", "required": True, "description": "项目名称"},
            },
        },
        {
            "name": "delete_module",
            "description": "删除模块（级联删除功能和向量）",
            "category": "module_management",
            "parameters": {
                "project": {"type": "string", "required": True, "description": "项目名称"},
                "name": {"type": "string", "required": True, "description": "模块名称"},
            },
        },
    ])

    # 功能管理
    all_tools.extend([
        {
            "name": "create_feature",
            "description": "创建功能（必须关联模块）",
            "category": "feature_management",
            "parameters": {
                "project": {"type": "string", "required": True, "description": "项目名称"},
                "code": {"type": "string", "required": True, "description": "功能编号"},
                "name": {"type": "string", "required": True, "description": "功能名称"},
                "module": {"type": "string", "required": True, "description": "所属模块"},
                "description": {"type": "string", "required": False, "description": "功能描述"},
            },
        },
        {
            "name": "list_features",
            "description": "列出功能（可按模块过滤）",
            "category": "feature_management",
            "parameters": {
                "project": {"type": "string", "required": True, "description": "项目名称"},
                "module": {"type": "string", "required": False, "description": "按模块过滤"},
            },
        },
        {
            "name": "delete_feature",
            "description": "删除功能（级联删除向量）",
            "category": "feature_management",
            "parameters": {
                "project": {"type": "string", "required": True, "description": "项目名称"},
                "code": {"type": "string", "required": True, "description": "功能编号"},
            },
        },
    ])

    # 记忆管理
    all_tools.extend([
        {
            "name": "upload_memory",
            "description": "上传记忆文件到项目知识库",
            "category": "memory_management",
            "parameters": {
                "project": {"type": "string", "required": True, "description": "项目名称"},
                "filename": {"type": "string", "required": True, "description": "文件名"},
                "content": {"type": "string", "required": True, "description": "文件内容"},
                "feature_codes": {"type": "array", "required": False, "description": "功能编号列表"},
                "module": {"type": "string", "required": False, "description": "模块名称"},
            },
        },
        {
            "name": "ask_project",
            "description": "向项目知识库提问（支持逐级降级检索）",
            "category": "memory_management",
            "parameters": {
                "project": {"type": "string", "required": True, "description": "项目名称"},
                "question": {"type": "string", "required": True, "description": "问题内容"},
                "top_k": {"type": "integer", "required": False, "description": "返回数量"},
                "feature_codes": {"type": "array", "required": False, "description": "功能编号过滤"},
                "module": {"type": "string", "required": False, "description": "模块过滤"},
            },
        },
        {
            "name": "list_projects",
            "description": "列出所有项目",
            "category": "memory_management",
            "parameters": {},
        },
        {
            "name": "delete_memory",
            "description": "删除记忆文件或整个项目",
            "category": "memory_management",
            "parameters": {
                "project": {"type": "string", "required": True, "description": "项目名称"},
                "filename": {"type": "string", "required": False, "description": "文件名"},
            },
        },
    ])

    # 技能管理
    all_tools.extend([
        {
            "name": "upload_skill",
            "description": "上传技能到项目技能库",
            "category": "skill_management",
            "parameters": {
                "project": {"type": "string", "required": True, "description": "项目名称"},
                "skill_name": {"type": "string", "required": True, "description": "技能名称"},
                "content": {"type": "string", "required": True, "description": "技能内容"},
                "category": {"type": "string", "required": False, "description": "分类"},
                "tags": {"type": "array", "required": False, "description": "标签列表"},
            },
        },
        {
            "name": "search_skill",
            "description": "搜索技能",
            "category": "skill_management",
            "parameters": {
                "project": {"type": "string", "required": True, "description": "项目名称"},
                "task_description": {"type": "string", "required": True, "description": "任务描述"},
                "top_k": {"type": "integer", "required": False, "description": "返回数量"},
                "category": {"type": "string", "required": False, "description": "限定分类"},
            },
        },
        {
            "name": "list_skills",
            "description": "列出项目所有技能",
            "category": "skill_management",
            "parameters": {
                "project": {"type": "string", "required": True, "description": "项目名称"},
            },
        },
        {
            "name": "get_skill",
            "description": "获取指定技能详情",
            "category": "skill_management",
            "parameters": {
                "project": {"type": "string", "required": True, "description": "项目名称"},
                "skill_name": {"type": "string", "required": True, "description": "技能名称"},
                "category": {"type": "string", "required": False, "description": "分类"},
            },
        },
        {
            "name": "delete_skill",
            "description": "删除技能",
            "category": "skill_management",
            "parameters": {
                "project": {"type": "string", "required": True, "description": "项目名称"},
                "skill_name": {"type": "string", "required": True, "description": "技能名称"},
                "category": {"type": "string", "required": False, "description": "分类"},
            },
        },
    ])

    # 系统信息
    all_tools.extend([
        {
            "name": "search_experience",
            "description": "搜索企业项目经验和编码规范",
            "category": "knowledge_search",
            "parameters": {
                "query": {"type": "string", "required": True, "description": "搜索内容"},
                "kb_id": {"type": "string", "required": False, "description": "限定知识库"},
                "top_k": {"type": "integer", "required": False, "description": "返回数量"},
            },
        },
        {
            "name": "list_mcp_tools",
            "description": "列出所有可用的 MCP 工具",
            "category": "system",
            "parameters": {
                "categorized": {"type": "boolean", "required": False, "description": "是否按分类分组"},
            },
        },
    ])

    if categorized:
        # 按分类分组
        categorized_tools = {}
        for cat_key, cat_info in TOOL_CATEGORIES.items():
            cat_tools = [t for t in all_tools if t["category"] == cat_key]
            if cat_tools:
                categorized_tools[cat_key] = {
                    "name": cat_info["name"],
                    "tools": cat_tools,
                }
        return {
            "tools": all_tools,
            "categories": categorized_tools,
            "total_count": len(all_tools),
        }
    else:
        return {
            "tools": all_tools,
            "total_count": len(all_tools),
        }


# MCP Tool 元数据

LIST_MCP_TOOLS_TOOL = {
    "name": "list_mcp_tools",
    "description": "列出所有可用的 MCP 工具，包含名称、描述、参数说明",
    "inputSchema": {
        "type": "object",
        "properties": {
            "categorized": {
                "type": "boolean",
                "description": "是否按分类分组（默认 true）",
                "default": True,
            },
        },
    },
}


def register_discovery_tools(gateway_mcp):
    """向 FastMCP 注册发现工具"""
    from mcp import types

    async def list_mcp_tools(ctx, categorized: bool = True):
        """列出所有 MCP 工具"""
        result = list_mcp_tools_impl(categorized)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        )

    # 设置元数据
    list_mcp_tools.__name__ = "list_mcp_tools"
    list_mcp_tools.__doc__ = LIST_MCP_TOOLS_TOOL["description"]

    # 注册工具
    gateway_mcp.tool(name="list_mcp_tools", description=LIST_MCP_TOOLS_TOOL["description"])(list_mcp_tools)

    logger.info("Registered discovery tools: list_mcp_tools")
