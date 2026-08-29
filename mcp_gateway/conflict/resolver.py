"""
Conflict Resolver - 冲突解决器

根据冲突类型和元数据自动决定解决策略
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from mcp_gateway.rag_client import RAGClient
from mcp_gateway.conflict.detector import ContradictionResult

logger = logging.getLogger(__name__)


@dataclass
class ResolutionAction:
    """解决动作"""
    action: str  # "deprecate", "update_vote", "set_conflict_pair", "keep_both"
    chunk_id: str
    target_chunk_id: Optional[str] = None
    reason: str = ""


class ConflictResolver:
    """冲突解决器"""

    def __init__(self, rag_client: RAGClient,
                 vote_threshold: int = 3,
                 same_file_take_newer: bool = True):
        """
        Args:
            rag_client: RAG 客户端
            vote_threshold: 投票阈值（达到此值自动废弃低票方）
            same_file_take_newer: 同文件冲突是否保留较新版本
        """
        self.rag_client = rag_client
        self.vote_threshold = vote_threshold
        self.same_file_take_newer = same_file_take_newer

    def resolve(self, contradiction: ContradictionResult,
                new_metadata: Optional[Dict] = None,
                existing_metadata: Optional[Dict] = None) -> ResolutionAction:
        """
        根据矛盾类型决定解决策略

        Args:
            contradiction: 矛盾检测结果
            new_metadata: 新 chunk 的元数据
            existing_metadata: 已有 chunk 的元数据

        Returns:
            ResolutionAction 解决动作
        """
        new_id = contradiction.new_chunk_id
        existing_id = contradiction.conflicting_chunk_id

        if not existing_id:
            return ResolutionAction(
                action="keep_both",
                chunk_id=new_id,
                reason="无冲突 chunk",
            )

        # 策略 1: 同一文件的冲突 → 保留较新版本
        if self._is_same_file(new_metadata, existing_metadata):
            if self.same_file_take_newer:
                # 标记旧版本为废弃
                return ResolutionAction(
                    action="deprecate",
                    chunk_id=existing_id,
                    target_chunk_id=new_id,
                    reason="同一文件的新版本覆盖旧版本",
                )

        # 策略 2: 不同文件的冲突 → 设置矛盾对，保留两者
        self.rag_client.set_conflict_pair(new_id, existing_id)

        return ResolutionAction(
            action="set_conflict_pair",
            chunk_id=new_id,
            target_chunk_id=existing_id,
            reason="不同来源的矛盾内容，保留两者并标记矛盾对",
        )

    def resolve_by_voting(self, chunk_id: str, conflicting_id: str) -> ResolutionAction:
        """
        通过投票机制解决冲突

        Args:
            chunk_id: chunk ID
            conflicting_id: 冲突 chunk ID

        Returns:
            ResolutionAction
        """
        vote_a = self.rag_client.get_vote_score(chunk_id)
        vote_b = self.rag_client.get_vote_score(conflicting_id)

        # 投票差异达到阈值时自动废弃低票方
        diff = abs(vote_a - vote_b)
        if diff >= self.vote_threshold:
            loser = chunk_id if vote_a < vote_b else conflicting_id
            winner = conflicting_id if vote_a < vote_b else chunk_id

            self.rag_client.deprecate_chunk(loser)
            return ResolutionAction(
                action="deprecate",
                chunk_id=loser,
                target_chunk_id=winner,
                reason=f"投票淘汰：{winner}({max(vote_a, vote_b)}票) vs {loser}({min(vote_a, vote_b)}票)",
            )

        return ResolutionAction(
            action="keep_both",
            chunk_id=chunk_id,
            target_chunk_id=conflicting_id,
            reason=f"投票未达阈值：{vote_a} vs {vote_b}（阈值={self.vote_threshold}）",
        )

    def _is_same_file(self, new_metadata: Optional[Dict],
                      existing_metadata: Optional[Dict]) -> bool:
        """判断是否来自同一文件"""
        if not new_metadata or not existing_metadata:
            return False
        return new_metadata.get("sourceRef") == existing_metadata.get("sourceRef")
