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


def _is_outdated_content(ai_answer: str, source_excerpt: str) -> bool:
    """
    判断源内容是否被 AI 标记为过时/错误

    通过分析 AI 回答，判断对应的源内容是否被标记为过时。
    只有当 AI 明确指出某个来源是过时的，才会返回 True。
    """
    # AI 回答中明确指出过时的表述
    outdated_patterns = [
        "已过时", "过时的", "过时版本",
        "错误的", "错误版本",
        "已弃用", "已废弃",
        "已迁移", "已替换",
        "已被", "不再使用",
        "请勿参考", "请勿使用",
    ]

    # 检查 AI 回答是否提到过时
    answer_has_outdated = any(pattern in ai_answer for pattern in outdated_patterns)

    if not answer_has_outdated:
        return False

    # 检查源内容是否包含过时标记
    source_patterns = [
        "过时", "错误", "已弃用", "已迁移", "已替换",
        "请勿参考", "请勿使用", "旧版本", "不再使用",
    ]

    return any(pattern in source_excerpt for pattern in source_patterns)


def search_experience_impl(
    query: str,
    kb_id: Optional[str] = None,
    top_k: int = 5,
    auto_deprecate: bool = True,
) -> Dict[str, Any]:
    """
    搜索企业项目经验和编码规范（使用向量检索 + AI 回答）

    Args:
        query: 搜索内容，如"Spring Boot 分页实现"、"Git 提交规范"
        kb_id: 限定知识库 ID（可选，默认搜索所有）
        top_k: 返回结果数量，默认 5
        auto_deprecate: 是否自动标记过时知识（默认 True）

    Returns:
        包含 AI 回答和原始搜索结果的字典
    """
    client = get_rag_client()

    try:
        # 使用向量检索 + AI 回答（返回 AI 回答 + sources）
        result = client.rag_chat_with_sources(query)
        ai_answer = result.get("answer", "")
        sources = result.get("sources", [])

        # 记录引用（投票机制）
        formatted_results = []
        deprecated_chunks = []

        for source in sources[:top_k]:
            doc_id = source.get("docId")
            doc_name = source.get("docName", "")
            excerpt = source.get("excerpt", "")

            # 尝试获取 chunk_id
            chunk_id = None
            if doc_id:
                try:
                    chunks = client.get_chunks(doc_id)
                    if chunks:
                        records = chunks.get("records", []) if isinstance(chunks, dict) else chunks
                        if records and len(records) > 0:
                            first_chunk = records[0] if isinstance(records, list) else None
                            if first_chunk and isinstance(first_chunk, dict):
                                chunk_id = first_chunk.get("id")
                except Exception:
                    pass

            # 记录引用
            if chunk_id:
                try:
                    client.record_reference(chunk_id)
                except Exception as e:
                    logger.warning(f"Failed to record reference for {chunk_id}: {e}")

                # 检查是否包含过时信息（AI 回答中提到的）
                if auto_deprecate and _is_outdated_content(ai_answer, excerpt):
                    try:
                        client.deprecate_chunk(chunk_id)
                        deprecated_chunks.append({
                            "chunk_id": chunk_id,
                            "doc_name": doc_name,
                            "reason": "AI 判断为过时/错误知识",
                        })
                        logger.info(f"Auto-deprecated chunk {chunk_id} from {doc_name}")
                    except Exception as e:
                        logger.warning(f"Failed to deprecate chunk {chunk_id}: {e}")

            formatted_results.append({
                "chunk_id": chunk_id,
                "content": excerpt,
                "doc_id": doc_id,
                "doc_name": doc_name,
            })

        return {
            "status": "success",
            "query": query,
            "ai_answer": ai_answer,
            "result_count": len(formatted_results),
            "results": formatted_results,
            "deprecated_chunks": deprecated_chunks,
            "deprecated_count": len(deprecated_chunks),
        }

    except Exception as e:
        logger.error(f"search_experience failed: {e}")
        return {
            "status": "error",
            "query": query,
            "error": str(e),
            "ai_answer": "",
            "result_count": 0,
            "results": [],
            "deprecated_chunks": [],
            "deprecated_count": 0,
        }


# MCP Tool 元数据（用于动态注册）
SEARCH_EXPERIENCE_TOOL = {
    "name": "search_experience",
    "description": (
        "搜索企业项目经验和编码规范。使用向量检索和 AI 回答，"
        "当用户询问技术实现、最佳实践、编码规范、项目经验等问题时，"
        "使用此工具从企业知识库中检索相关信息。"
        "返回 AI 生成的回答和原始搜索结果。"
        "如果 AI 判断某些知识已过时，会自动标记为废弃。"
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
