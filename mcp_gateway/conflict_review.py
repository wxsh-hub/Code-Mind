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

# 技术选型对比（用于检测技术矛盾）
TECH_CONFLICTS = [
    ("MySQL", "PostgreSQL"), ("MySQL", "pgvector"),
    ("Hibernate", "MyBatis"), ("Hibernate", "MyBatis-Plus"),
    ("jQuery", "React"), ("jQuery", "Vue"),
    ("Memcached", "Redis"),
    ("Kafka", "RocketMQ"),
    ("JWT", "Sa-Token"), ("JWT", "Session"),
    ("SOAP", "REST"), ("SOAP", "RESTful"),
    ("XML", "JSON"),
    ("JDK 8", "JDK 17"), ("JDK 8", "JDK 21"),
    ("Spring Boot 2", "Spring Boot 4"),
    ("Grunt", "Vite"), ("Grunt", "Webpack"),
]


def detect_negation(text_a: str, text_b: str) -> bool:
    """检测两段文本是否包含否定关系"""
    text_a_lower = text_a.lower()
    text_b_lower = text_b.lower()

    # 检测否定词对
    for pos, neg in NEGATION_PAIRS:
        if (pos in text_a_lower and neg in text_b_lower) or \
           (neg in text_a_lower and pos in text_b_lower):
            return True

    # 检测技术选型矛盾
    for tech_a, tech_b in TECH_CONFLICTS:
        if (tech_a in text_a and tech_b in text_b) or \
           (tech_b in text_a and tech_a in text_b):
            # 进一步检查是否在同一上下文中（如对比、推荐）
            context_keywords = ["推荐", "使用", "选择", "采用", "迁移到", "替换"]
            has_context = any(kw in text_a or kw in text_b for kw in context_keywords)
            if has_context:
                return True

    return False


def list_conflicts_impl(project: str, kb_id: Optional[str] = None,
                        confidence_threshold: float = 0.2,
                        page: int = 1, page_size: int = 20,
                        min_score: float = 0.0) -> Dict[str, Any]:
    """列出待审核的矛盾对（支持分页和过滤）

    Args:
        project: 项目名称
        kb_id: 知识库 ID（可选）
        confidence_threshold: 置信度差异阈值（默认 20%）
        page: 页码（从1开始）
        page_size: 每页数量（默认20）
        min_score: 最小相似度分数过滤（默认0）

    Returns:
        矛盾对列表（分页）
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

        # 按相似度分数过滤
        if min_score > 0:
            chunks = [c for c in chunks if c.get("score", 0) >= min_score]

        # 检测矛盾对
        all_conflicts = []
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
                        all_conflicts.append({
                            "chunk_a": {
                                "id": chunk_a.get("chunkId"),
                                "content": chunk_a.get("content", "")[:200],
                                "confidence": conf_a,
                                "score": chunk_a.get("score", 0),
                            },
                            "chunk_b": {
                                "id": chunk_b.get("chunkId"),
                                "content": chunk_b.get("content", "")[:200],
                                "confidence": conf_b,
                                "score": chunk_b.get("score", 0),
                            },
                            "confidence_diff": round(diff, 2),
                            "contradiction_type": "negation",
                        })

        # 按置信度差异排序（差异小的排前面）
        all_conflicts.sort(key=lambda x: x["confidence_diff"])

        # 分页
        total = len(all_conflicts)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_conflicts = all_conflicts[start_idx:end_idx]

        return {
            "status": "success",
            "project": project,
            "conflicts": paginated_conflicts,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            },
            "filters": {
                "confidence_threshold": confidence_threshold,
                "min_score": min_score,
            },
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def submit_conflict_for_review_impl(
    project: str,
    chunk_a_id: str,
    chunk_b_id: str,
    reason: str = "",
    ai_analysis: str = "",
) -> Dict[str, Any]:
    """AI 提交矛盾对到后台人工审核

    当 AI 无法判断哪个是正确的知识时，调用此接口将矛盾对提交到后台。

    Args:
        project: 项目名称
        chunk_a_id: 矛盾对的 chunk A ID
        chunk_b_id: 矛盾对的 chunk B ID
        reason: 提交原因（为什么无法判断）
        ai_analysis: AI 的分析（尝试分析但无法确定）

    Returns:
        提交结果
    """
    client = get_client()
    client.ensure_logged_in()

    try:
        # 设置矛盾对
        client.set_conflict_pair(chunk_a_id, chunk_b_id)

        # 获取两个 chunk 的内容
        chunk_a = client._request("GET", f"/knowledge-base/chunks/{chunk_a_id}")
        chunk_b = client._request("GET", f"/knowledge-base/chunks/{chunk_b_id}")

        content_a = chunk_a.get("data", {}).get("content", "")[:200] if isinstance(chunk_a.get("data"), dict) else ""
        content_b = chunk_b.get("data", {}).get("content", "")[:200] if isinstance(chunk_b.get("data"), dict) else ""

        return {
            "status": "success",
            "action": "submitted_for_review",
            "chunk_a": {
                "id": chunk_a_id,
                "content_preview": content_a,
            },
            "chunk_b": {
                "id": chunk_b_id,
                "content_preview": content_b,
            },
            "reason": reason,
            "ai_analysis": ai_analysis,
            "message": "矛盾对已提交到后台，请人工审核",
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
    "description": "列出待审核的矛盾向量对（置信度相近的反义向量，支持分页）",
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
            "page": {
                "type": "integer",
                "description": "页码（从1开始，默认1）",
                "default": 1,
            },
            "page_size": {
                "type": "integer",
                "description": "每页数量（默认20）",
                "default": 20,
            },
            "min_score": {
                "type": "number",
                "description": "最小相似度分数过滤（默认0）",
                "default": 0,
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

SUBMIT_CONFLICT_FOR_REVIEW_TOOL = {
    "name": "submit_conflict_for_review",
    "description": (
        "当 AI 无法判断两个知识哪个是正确时，调用此接口将矛盾对提交到后台人工审核。"
        "适用场景：两个知识给出不同结论，AI 无法确定哪个是过时或错误的。"
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {"type": "string", "description": "项目名称"},
            "chunk_a_id": {"type": "string", "description": "知识 A 的 chunk ID"},
            "chunk_b_id": {"type": "string", "description": "知识 B 的 chunk ID"},
            "reason": {
                "type": "string",
                "description": "提交原因，如：两个知识给出不同结论，无法判断哪个是正确的",
            },
            "ai_analysis": {
                "type": "string",
                "description": "AI 的分析，如：知识A说X，知识B说Y，无法确定哪个是最新版本",
            },
        },
        "required": ["project", "chunk_a_id", "chunk_b_id", "reason"],
    },
}


def register_conflict_review_tools(gateway_mcp):
    """向 FastMCP 注册矛盾审核工具"""
    from mcp import types

    async def list_conflicts(ctx, project: str, kb_id: str = None,
                            confidence_threshold: float = 0.2,
                            page: int = 1, page_size: int = 20,
                            min_score: float = 0):
        """列出矛盾对"""
        result = list_conflicts_impl(project, kb_id, confidence_threshold,
                                     page, page_size, min_score)
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

    async def submit_conflict_for_review(ctx, project: str, chunk_a_id: str, chunk_b_id: str,
                                          reason: str, ai_analysis: str = ""):
        """提交矛盾对到后台人工审核"""
        result = submit_conflict_for_review_impl(project, chunk_a_id, chunk_b_id, reason, ai_analysis)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    # 设置元数据
    list_conflicts.__name__ = "list_conflicts"
    list_conflicts.__doc__ = LIST_CONFLICTS_TOOL["description"]

    review_conflict.__name__ = "review_conflict"
    review_conflict.__doc__ = REVIEW_CONFLICT_TOOL["description"]

    submit_conflict_for_review.__name__ = "submit_conflict_for_review"
    submit_conflict_for_review.__doc__ = SUBMIT_CONFLICT_FOR_REVIEW_TOOL["description"]

    # 注册工具
    gateway_mcp.tool(name="list_conflicts", description=LIST_CONFLICTS_TOOL["description"])(list_conflicts)
    gateway_mcp.tool(name="review_conflict", description=REVIEW_CONFLICT_TOOL["description"])(review_conflict)
    gateway_mcp.tool(name="submit_conflict_for_review", description=SUBMIT_CONFLICT_FOR_REVIEW_TOOL["description"])(submit_conflict_for_review)

    logger.info("Registered conflict review tools: list_conflicts, review_conflict, submit_conflict_for_review")
