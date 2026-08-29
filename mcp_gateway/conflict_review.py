"""
Conflict Review MCP Tools - 矛盾向量审核工具

支持：
- list_conflicts: 列出待审核的矛盾对
- review_conflict: 审核矛盾对
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


# 否定词对
NEGATION_PAIRS = [
    ("应该", "不应该"), ("必须", "不必"), ("需要", "不需要"),
    ("启用", "禁用"), ("开启", "关闭"), ("打开", "关闭"),
    ("使用", "不使用"), ("推荐", "不推荐"),
    ("优点", "缺点"), ("优势", "劣势"),
    ("正确", "错误"), ("成功", "失败"),
]


def detect_negation(text_a: str, text_b: str) -> bool:
    """检测两段文本是否包含否定关系"""
    text_a_lower = text_a.lower()
    text_b_lower = text_b.lower()

    for pos, neg in NEGATION_PAIRS:
        if (pos in text_a_lower and neg in text_b_lower) or \
           (neg in text_a_lower and pos in text_b_lower):
            return True
    return False


def list_conflicts_impl(project: str, kb_id: Optional[str] = None,
                        confidence_threshold: float = 0.2) -> Dict[str, Any]:
    """列出待审核的矛盾对

    Args:
        project: 项目名称
        kb_id: 知识库 ID（可选）
        confidence_threshold: 置信度差异阈值（默认 20%）

    Returns:
        矛盾对列表
    """
    client = get_client()
    client.ensure_logged_in()

    try:
        # 获取所有向量
        search_resp = client._request("POST", "/knowledge-base/search/similar", {
            "query": "",
            "kbId": kb_id or "",
            "topK": 1000,
        })
        chunks = search_resp.get("data", [])

        # 检测矛盾对
        conflicts = []
        checked_pairs = set()

        for i, chunk_a in enumerate(chunks):
            for j, chunk_b in enumerate(chunks):
                if i >= j:
                    continue

                pair_key = f"{chunk_a.get('chunkId')}-{chunk_b.get('chunkId')}"
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)

                # 检测否定关系
                if detect_negation(chunk_a.get("content", ""), chunk_b.get("content", "")):
                    # 计算置信度差异
                    conf_a = chunk_a.get("confidence", 1)
                    conf_b = chunk_b.get("confidence", 1)
                    max_conf = max(conf_a, conf_b)
                    diff = abs(conf_a - conf_b) / max_conf if max_conf > 0 else 0

                    # 只返回置信度相近的矛盾对
                    if diff <= confidence_threshold:
                        conflicts.append({
                            "chunk_a": {
                                "id": chunk_a.get("chunkId"),
                                "content": chunk_a.get("content", "")[:200],
                                "confidence": conf_a,
                            },
                            "chunk_b": {
                                "id": chunk_b.get("chunkId"),
                                "content": chunk_b.get("content", "")[:200],
                                "confidence": conf_b,
                            },
                            "confidence_diff": round(diff, 2),
                            "contradiction_type": "negation",
                        })

        return {
            "status": "success",
            "project": project,
            "conflicts": conflicts,
            "count": len(conflicts),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def review_conflict_impl(project: str, chunk_a_id: str, chunk_b_id: str,
                         winner: str, reason: str = "") -> Dict[str, Any]:
    """审核矛盾对

    Args:
        project: 项目名称
        chunk_a_id: 矛盾对的 chunk A ID
        chunk_b_id: 矛盾对的 chunk B ID
        winner: 胜者（"a" | "b" | "both"）
        reason: 审核原因

    Returns:
        审核结果
    """
    client = get_client()
    client.ensure_logged_in()

    try:
        if winner == "a":
            # 废弃 chunk_b
            client.deprecate_chunk(chunk_b_id)
            return {
                "status": "success",
                "action": "deprecated",
                "deprecated_chunk": chunk_b_id,
                "kept_chunk": chunk_a_id,
                "reason": reason,
            }
        elif winner == "b":
            # 废弃 chunk_a
            client.deprecate_chunk(chunk_a_id)
            return {
                "status": "success",
                "action": "deprecated",
                "deprecated_chunk": chunk_a_id,
                "kept_chunk": chunk_b_id,
                "reason": reason,
            }
        else:  # both
            # 设置矛盾对
            client.set_conflict_pair(chunk_a_id, chunk_b_id)
            return {
                "status": "success",
                "action": "kept_both",
                "chunk_a": chunk_a_id,
                "chunk_b": chunk_b_id,
                "reason": reason,
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# MCP Tool 元数据

LIST_CONFLICTS_TOOL = {
    "name": "list_conflicts",
    "description": "列出待审核的矛盾向量对（置信度相近的反义向量）",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {"type": "string", "description": "项目名称"},
            "kb_id": {"type": "string", "description": "知识库 ID（可选）"},
            "confidence_threshold": {
                "type": "number",
                "description": "置信度差异阈值（默认 0.2，即 20%）",
                "default": 0.2,
            },
        },
        "required": ["project"],
    },
}

REVIEW_CONFLICT_TOOL = {
    "name": "review_conflict",
    "description": "审核矛盾向量对",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {"type": "string", "description": "项目名称"},
            "chunk_a_id": {"type": "string", "description": "矛盾对的 chunk A ID"},
            "chunk_b_id": {"type": "string", "description": "矛盾对的 chunk B ID"},
            "winner": {
                "type": "string",
                "description": "胜者：'a'（保留 A）、'b'（保留 B）、'both'（保留两者）",
                "enum": ["a", "b", "both"],
            },
            "reason": {"type": "string", "description": "审核原因"},
        },
        "required": ["project", "chunk_a_id", "chunk_b_id", "winner"],
    },
}


def register_conflict_review_tools(gateway_mcp):
    """向 FastMCP 注册矛盾审核工具"""
    from mcp import types

    async def list_conflicts(ctx, project: str, kb_id: str = None,
                            confidence_threshold: float = 0.2):
        """列出矛盾对"""
        result = list_conflicts_impl(project, kb_id, confidence_threshold)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def review_conflict(ctx, project: str, chunk_a_id: str, chunk_b_id: str,
                             winner: str, reason: str = ""):
        """审核矛盾对"""
        result = review_conflict_impl(project, chunk_a_id, chunk_b_id, winner, reason)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    # 设置元数据
    list_conflicts.__name__ = "list_conflicts"
    list_conflicts.__doc__ = LIST_CONFLICTS_TOOL["description"]

    review_conflict.__name__ = "review_conflict"
    review_conflict.__doc__ = REVIEW_CONFLICT_TOOL["description"]

    # 注册工具
    gateway_mcp.tool(name="list_conflicts", description=LIST_CONFLICTS_TOOL["description"])(list_conflicts)
    gateway_mcp.tool(name="review_conflict", description=REVIEW_CONFLICT_TOOL["description"])(review_conflict)

    logger.info("Registered conflict review tools: list_conflicts, review_conflict")
