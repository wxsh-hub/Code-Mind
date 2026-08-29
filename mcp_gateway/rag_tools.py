"""
RAG MCP Tools - Agent 经验查询工具

提供 search_experience MCP Tool，Agent 通过此工具查询企业知识库
"""

import logging
from typing import Any, Dict, List, Optional

from mcp_gateway.rag_client import RAGClient, RAGConfig

logger = logging.getLogger(__name__)

# 全局 RAG 客户端实例
_rag_client: Optional[RAGClient] = None


def get_rag_client() -> RAGClient:
    """获取或创建 RAG 客户端"""
    global _rag_client
    if _rag_client is None:
        _rag_client = RAGClient()
    return _rag_client


def set_rag_client(client: RAGClient):
    """设置 RAG 客户端（用于测试）"""
    global _rag_client
    _rag_client = client


def search_experience_impl(
    query: str,
    kb_id: Optional[str] = None,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    搜索企业项目经验和编码规范

    Args:
        query: 搜索内容，如"Spring Boot 分页实现"、"Git 提交规范"
        kb_id: 限定知识库 ID（可选，默认搜索所有）
        top_k: 返回结果数量，默认 5

    Returns:
        包含搜索结果的字典
    """
    client = get_rag_client()

    try:
        results = client.search_similar(query=query, kb_id=kb_id, top_k=top_k)

        # 格式化结果
        formatted_results = []
        for item in results:
            formatted = {
                "chunk_id": item.get("chunkId"),
                "content": item.get("content", ""),
                "doc_id": item.get("docId"),
                "kb_id": item.get("kbId"),
                "metadata": item.get("metadata", {}),
            }
            formatted_results.append(formatted)

            # 记录引用（投票机制）
            chunk_id = item.get("chunkId")
            if chunk_id:
                try:
                    client.record_reference(chunk_id)
                except Exception as e:
                    logger.warning(f"Failed to record reference for {chunk_id}: {e}")

        return {
            "status": "success",
            "query": query,
            "result_count": len(formatted_results),
            "results": formatted_results,
        }

    except Exception as e:
        logger.error(f"search_experience failed: {e}")
        return {
            "status": "error",
            "query": query,
            "error": str(e),
            "result_count": 0,
            "results": [],
        }


# MCP Tool 元数据（用于动态注册）
SEARCH_EXPERIENCE_TOOL = {
    "name": "search_experience",
    "description": (
        "搜索企业项目经验和编码规范。当用户询问技术实现、最佳实践、"
        "编码规范、项目经验等问题时，使用此工具从企业知识库中检索相关信息。"
        "返回的内容包含实际项目中的经验总结和规范文档。"
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索内容，如 'Spring Boot 分页实现'、'Git 提交规范'、'数据库索引优化'",
            },
            "kb_id": {
                "type": "string",
                "description": "限定知识库 ID（可选，默认搜索所有知识库）",
            },
            "top_k": {
                "type": "integer",
                "description": "返回结果数量，默认 5",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}


def register_rag_tools(gateway_mcp):
    """
    向 FastMCP 网关注册 RAG 工具

    Args:
        gateway_mcp: FastMCP 实例
    """
    import inspect
    from mcp import types

    async def search_experience(ctx, query: str, kb_id: str = None, top_k: int = 5):
        """搜索企业项目经验和编码规范"""
        result = search_experience_impl(query=query, kb_id=kb_id, top_k=top_k)
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        )

    # 设置函数元数据
    search_experience.__name__ = "search_experience"
    search_experience.__doc__ = SEARCH_EXPERIENCE_TOOL["description"]

    # 注册到 FastMCP
    tool_decorator = gateway_mcp.tool(
        name="search_experience",
        description=SEARCH_EXPERIENCE_TOOL["description"],
    )
    tool_decorator(search_experience)
    logger.info("Registered RAG tool: search_experience")
