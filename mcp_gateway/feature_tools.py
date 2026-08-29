"""
Feature MCP Tools - 模块和功能管理工具

支持：
- create_module: 创建模块
- list_modules: 列出模块
- delete_module: 删除模块（级联删除功能和向量）
- create_feature: 创建功能
- list_features: 列出功能
- delete_feature: 删除功能（级联删除向量）
"""

import logging
import json
from typing import Any, Dict, List, Optional
from mcp_gateway.rag_client import RAGClient, RAGConfig

logger = logging.getLogger(__name__)

# 全局客户端实例
_client: Optional[RAGClient] = None


def get_client() -> RAGClient:
    """获取全局客户端"""
    global _client
    if _client is None:
        _client = RAGClient()
    return _client


def set_client(client: RAGClient):
    """设置全局客户端（用于测试）"""
    global _client
    _client = client


# ========== MCP Tool 实现 ==========

def create_module_impl(project: str, name: str, description: str = "") -> Dict[str, Any]:
    """创建模块

    Args:
        project: 项目名称
        name: 模块名称，如 user、order、payment
        description: 模块描述
    """
    client = get_client()
    client.ensure_logged_in()

    try:
        result = client.create_module(name, description)
        return {
            "status": "success",
            "project": project,
            "module": name,
            "data": result,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def list_modules_impl(project: str) -> Dict[str, Any]:
    """列出所有模块"""
    client = get_client()
    client.ensure_logged_in()

    try:
        modules = client.list_modules()
        return {
            "status": "success",
            "project": project,
            "modules": modules,
            "count": len(modules),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def delete_module_impl(project: str, name: str) -> Dict[str, Any]:
    """删除模块（级联删除功能和向量）

    Args:
        project: 项目名称
        name: 模块名称
    """
    client = get_client()
    client.ensure_logged_in()

    try:
        result = client.delete_module(name)
        return {
            "status": "success",
            "project": project,
            "module": name,
            "deleted_chunks": result.get("deleted_chunks", 0),
            "deleted_features": result.get("deleted_features", 0),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def create_feature_impl(project: str, code: str, name: str, module: str,
                        description: str = "") -> Dict[str, Any]:
    """创建功能

    Args:
        project: 项目名称
        code: 功能编号，如 2437
        name: 功能名称
        module: 所属模块名称（必填）
        description: 功能描述
    """
    client = get_client()
    client.ensure_logged_in()

    try:
        result = client.create_feature(code, name, module, description)
        return {
            "status": "success",
            "project": project,
            "feature_code": code,
            "feature_name": name,
            "module": module,
            "data": result,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def list_features_impl(project: str, module: Optional[str] = None) -> Dict[str, Any]:
    """列出功能

    Args:
        project: 项目名称
        module: 按模块过滤（可选）
    """
    client = get_client()
    client.ensure_logged_in()

    try:
        features = client.list_features(module)
        return {
            "status": "success",
            "project": project,
            "features": features,
            "count": len(features),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def delete_feature_impl(project: str, code: str) -> Dict[str, Any]:
    """删除功能（级联删除向量）

    Args:
        project: 项目名称
        code: 功能编号
    """
    client = get_client()
    client.ensure_logged_in()

    try:
        result = client.delete_feature(code)
        return {
            "status": "success",
            "project": project,
            "feature_code": code,
            "deleted_chunks": result.get("deleted_chunks", 0),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ========== MCP Tool 元数据 ==========

CREATE_MODULE_TOOL = {
    "name": "create_module",
    "description": "创建模块。模块是功能的集合，如 user、order、payment。",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {"type": "string", "description": "项目名称"},
            "name": {"type": "string", "description": "模块名称，如 user、order"},
            "description": {"type": "string", "description": "模块描述"},
        },
        "required": ["project", "name"],
    },
}

LIST_MODULES_TOOL = {
    "name": "list_modules",
    "description": "列出所有模块",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {"type": "string", "description": "项目名称"},
        },
        "required": ["project"],
    },
}

DELETE_MODULE_TOOL = {
    "name": "delete_module",
    "description": "删除模块（级联删除该模块下的所有功能和向量）",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {"type": "string", "description": "项目名称"},
            "name": {"type": "string", "description": "模块名称"},
        },
        "required": ["project", "name"],
    },
}

CREATE_FEATURE_TOOL = {
    "name": "create_feature",
    "description": "创建功能。功能必须关联模块。",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {"type": "string", "description": "项目名称"},
            "code": {"type": "string", "description": "功能编号，如 2437"},
            "name": {"type": "string", "description": "功能名称"},
            "module": {"type": "string", "description": "所属模块名称（必填）"},
            "description": {"type": "string", "description": "功能描述"},
        },
        "required": ["project", "code", "name", "module"],
    },
}

LIST_FEATURES_TOOL = {
    "name": "list_features",
    "description": "列出功能（可按模块过滤）",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {"type": "string", "description": "项目名称"},
            "module": {"type": "string", "description": "按模块过滤（可选）"},
        },
        "required": ["project"],
    },
}

DELETE_FEATURE_TOOL = {
    "name": "delete_feature",
    "description": "删除功能（级联删除该功能的所有向量）",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {"type": "string", "description": "项目名称"},
            "code": {"type": "string", "description": "功能编号"},
        },
        "required": ["project", "code"],
    },
}


def register_feature_tools(gateway_mcp):
    """向 FastMCP 注册功能管理工具"""
    from mcp import types

    async def create_module(ctx, project: str, name: str, description: str = ""):
        """创建模块"""
        result = create_module_impl(project, name, description)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def list_modules(ctx, project: str):
        """列出模块"""
        result = list_modules_impl(project)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def delete_module(ctx, project: str, name: str):
        """删除模块"""
        result = delete_module_impl(project, name)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def create_feature(ctx, project: str, code: str, name: str, module: str, description: str = ""):
        """创建功能"""
        result = create_feature_impl(project, code, name, module, description)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def list_features(ctx, project: str, module: str = None):
        """列出功能"""
        result = list_features_impl(project, module)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def delete_feature(ctx, project: str, code: str):
        """删除功能"""
        result = delete_feature_impl(project, code)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    # 设置元数据
    create_module.__name__ = "create_module"
    create_module.__doc__ = CREATE_MODULE_TOOL["description"]

    list_modules.__name__ = "list_modules"
    list_modules.__doc__ = LIST_MODULES_TOOL["description"]

    delete_module.__name__ = "delete_module"
    delete_module.__doc__ = DELETE_MODULE_TOOL["description"]

    create_feature.__name__ = "create_feature"
    create_feature.__doc__ = CREATE_FEATURE_TOOL["description"]

    list_features.__name__ = "list_features"
    list_features.__doc__ = LIST_FEATURES_TOOL["description"]

    delete_feature.__name__ = "delete_feature"
    delete_feature.__doc__ = DELETE_FEATURE_TOOL["description"]

    # 注册工具
    gateway_mcp.tool(name="create_module", description=CREATE_MODULE_TOOL["description"])(create_module)
    gateway_mcp.tool(name="list_modules", description=LIST_MODULES_TOOL["description"])(list_modules)
    gateway_mcp.tool(name="delete_module", description=DELETE_MODULE_TOOL["description"])(delete_module)
    gateway_mcp.tool(name="create_feature", description=CREATE_FEATURE_TOOL["description"])(create_feature)
    gateway_mcp.tool(name="list_features", description=LIST_FEATURES_TOOL["description"])(list_features)
    gateway_mcp.tool(name="delete_feature", description=DELETE_FEATURE_TOOL["description"])(delete_feature)

    logger.info("Registered feature tools: create_module, list_modules, delete_module, create_feature, list_features, delete_feature")
