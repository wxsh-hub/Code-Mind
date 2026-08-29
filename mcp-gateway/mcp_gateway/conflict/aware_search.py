"""
Conflict-Aware Search - 矛盾感知搜索

在搜索结果中标记矛盾关系，帮助 Agent 理解知识冲突
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from mcp_gateway.rag_client import RAGClient

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    vote_count: int = 0
    has_conflict: bool = False
    conflict_pair_id: Optional[str] = None
    deprecated: bool = False
    warning: Optional[str] = None


class ConflictAwareSearch:
    """矛盾感知搜索"""

    def __init__(self, rag_client: RAGClient):
        self.rag_client = rag_client

    def search(self, query: str, kb_id: Optional[str] = None,
               top_k: int = 10, exclude_deprecated: bool = True) -> List[SearchResult]:
        """
        搜索并标记矛盾关系

        Args:
            query: 搜索内容
            kb_id: 限定知识库
            top_k: 返回数量
            exclude_deprecated: 是否排除已废弃的 chunk

        Returns:
            List[SearchResult] 带矛盾标记的搜索结果
        """
        results = []

        try:
            chunks = self.rag_client.search_similar(
                query=query, kb_id=kb_id, top_k=top_k,
            )

            for chunk in chunks:
                metadata = chunk.get("metadata", {})
                deprecated = metadata.get("deprecated", False)
                conflict_pair_id = metadata.get("conflictPairId")

                # 排除已废弃
                if exclude_deprecated and deprecated:
                    continue

                result = SearchResult(
                    chunk_id=chunk.get("chunkId"),
                    content=chunk.get("content", ""),
                    metadata=metadata,
                    vote_count=metadata.get("voteCount", 0),
                    has_conflict=bool(conflict_pair_id),
                    conflict_pair_id=conflict_pair_id,
                    deprecated=deprecated,
                )

                # 添加警告信息
                if deprecated:
                    result.warning = "⚠️ 此内容已被标记为废弃"
                elif conflict_pair_id:
                    result.warning = "⚠️ 此内容存在矛盾版本，请谨慎参考"

                results.append(result)

            # 记录引用
            for result in results:
                if not result.deprecated:
                    try:
                        self.rag_client.record_reference(result.chunk_id)
                    except Exception:
                        pass

        except Exception as e:
            logger.error(f"Conflict-aware search failed: {e}")

        return results

    def search_with_conflict_context(self, query: str, kb_id: Optional[str] = None,
                                      top_k: int = 5) -> Dict[str, Any]:
        """
        搜索并返回带矛盾上下文的结果

        Returns:
            {
                "results": [...],
                "conflicts": [{"chunk_a": ..., "chunk_b": ..., "reason": ...}],
                "warnings": [...]
            }
        """
        results = self.search(query, kb_id, top_k, exclude_deprecated=True)

        # 收集矛盾对
        conflicts = []
        conflict_ids = set()
        for result in results:
            if result.has_conflict and result.conflict_pair_id not in conflict_ids:
                conflict_ids.add(result.chunk_id)
                conflict_ids.add(result.conflict_pair_id)
                conflicts.append({
                    "chunk_a": result.chunk_id,
                    "chunk_b": result.conflict_pair_id,
                    "reason": "内容存在矛盾",
                })

        # 收集警告
        warnings = [r.warning for r in results if r.warning]

        return {
            "results": [
                {
                    "chunk_id": r.chunk_id,
                    "content": r.content,
                    "vote_count": r.vote_count,
                    "has_conflict": r.has_conflict,
                    "warning": r.warning,
                }
                for r in results
            ],
            "conflicts": conflicts,
            "warnings": warnings,
        }
