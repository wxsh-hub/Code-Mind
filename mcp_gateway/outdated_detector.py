# -*- coding: utf-8 -*-
"""
过时知识检测器

基于规则检测过时/错误的知识，不需要 AI 参与，不消耗 token。

检测规则：
1. 包含过时关键词：过时、已弃用、已迁移、已替换、请勿参考
2. 包含错误关键词：错误、警告、不要使用
3. 包含版本对比：旧版本、新版本、已升级
"""

import logging
from typing import Any, Dict, List, Optional
from mcp_gateway.rag_client import RAGClient

logger = logging.getLogger(__name__)

# 过时关键词
OUTDATED_KEYWORDS = [
    "过时", "已弃用", "已迁移", "已替换", "请勿参考",
    "已升级", "旧版本", "不再使用", "已被替代",
]

# 错误关键词
ERROR_KEYWORDS = [
    "错误", "警告", "不要使用", "请勿使用", "已废弃",
    "错误版本", "错误配置",
]

# 版本对比关键词
VERSION_KEYWORDS = [
    "已过时", "当前使用", "实际使用", "已迁移到",
]


def detect_outdated_content(content: str) -> Dict[str, Any]:
    """
    检测内容是否包含过时/错误信息

    Args:
        content: 文档内容

    Returns:
        {
            "is_outdated": bool,
            "reasons": list[str],
            "confidence": float  # 0-1
        }
    """
    if not content:
        return {"is_outdated": False, "reasons": [], "confidence": 0}

    reasons = []

    # 检测过时关键词
    for keyword in OUTDATED_KEYWORDS:
        if keyword in content:
            reasons.append(f"包含过时关键词: {keyword}")

    # 检测错误关键词
    for keyword in ERROR_KEYWORDS:
        if keyword in content:
            reasons.append(f"包含错误关键词: {keyword}")

    # 检测版本对比
    for keyword in VERSION_KEYWORDS:
        if keyword in content:
            reasons.append(f"包含版本对比: {keyword}")

    # 计算置信度
    confidence = min(len(reasons) * 0.3, 1.0)

    return {
        "is_outdated": len(reasons) > 0,
        "reasons": reasons,
        "confidence": confidence,
    }


def scan_knowledge_base(client: RAGClient, kb_id: Optional[str] = None) -> Dict[str, Any]:
    """
    扫描知识库中的过时知识

    Args:
        client: RAG 客户端
        kb_id: 知识库 ID（可选，扫描所有）

    Returns:
        {
            "total_chunks": int,
            "outdated_chunks": list[dict],
            "outdated_count": int,
        }
    """
    # 获取所有 chunk
    search_resp = client._request("POST", "/knowledge-base/search/similar", {
        "query": "",
        "kbId": kb_id or "",
        "topK": 1000,
    })
    chunks = search_resp.get("data", [])

    outdated_chunks = []

    for chunk in chunks:
        content = chunk.get("content", "")
        chunk_id = chunk.get("chunkId")

        # 检测过时内容
        result = detect_outdated_content(content)

        if result["is_outdated"]:
            outdated_chunks.append({
                "chunk_id": chunk_id,
                "content_preview": content[:200],
                "reasons": result["reasons"],
                "confidence": result["confidence"],
            })

    return {
        "total_chunks": len(chunks),
        "outdated_chunks": outdated_chunks,
        "outdated_count": len(outdated_chunks),
    }


def auto_deprecate_outdated(client: RAGClient, kb_id: Optional[str] = None,
                             confidence_threshold: float = 0.6) -> Dict[str, Any]:
    """
    自动标记过时知识为废弃

    Args:
        client: RAG 客户端
        kb_id: 知识库 ID（可选）
        confidence_threshold: 置信度阈值（默认 0.6）

    Returns:
        {
            "total_scanned": int,
            "deprecated_count": int,
            "deprecated_chunks": list[dict],
        }
    """
    scan_result = scan_knowledge_base(client, kb_id)

    deprecated_chunks = []

    for chunk in scan_result["outdated_chunks"]:
        if chunk["confidence"] >= confidence_threshold:
            chunk_id = chunk["chunk_id"]
            try:
                client.deprecate_chunk(chunk_id)
                deprecated_chunks.append(chunk)
                logger.info(f"Deprecated chunk {chunk_id}: {chunk['reasons']}")
            except Exception as e:
                logger.error(f"Failed to deprecate chunk {chunk_id}: {e}")

    return {
        "total_scanned": scan_result["total_chunks"],
        "deprecated_count": len(deprecated_chunks),
        "deprecated_chunks": deprecated_chunks,
    }
