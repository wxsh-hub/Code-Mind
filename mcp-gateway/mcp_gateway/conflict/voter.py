"""
Voting Mechanism - 投票机制

管理 chunk 的投票分数，支持引用计数和冲突投票
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from mcp_gateway.rag_client import RAGClient

logger = logging.getLogger(__name__)


@dataclass
class VoteResult:
    """投票结果"""
    chunk_id: str
    vote_count: int
    is_winner: bool
    opponent_id: Optional[str] = None
    opponent_votes: Optional[int] = None


class VotingMechanism:
    """投票机制"""

    def __init__(self, rag_client: RAGClient, reference_weight: float = 1.0):
        """
        Args:
            rag_client: RAG 客户端
            reference_weight: 引用计数权重（每次被引用增加的分数）
        """
        self.rag_client = rag_client
        self.reference_weight = reference_weight

    def record_reference(self, chunk_id: str) -> int:
        """
        记录 chunk 被引用（投票 +1）

        Args:
            chunk_id: chunk ID

        Returns:
            更新后的投票分数
        """
        self.rag_client.record_reference(chunk_id)
        return self.rag_client.get_vote_score(chunk_id)

    def get_vote_score(self, chunk_id: str) -> int:
        """获取 chunk 投票分数"""
        return self.rag_client.get_vote_score(chunk_id)

    def compare_votes(self, chunk_id_a: str, chunk_id_b: str) -> Tuple[VoteResult, VoteResult]:
        """
        比较两个 chunk 的投票

        Args:
            chunk_id_a: chunk A
            chunk_id_b: chunk B

        Returns:
            Tuple[VoteResult, VoteResult] 两个 chunk 的投票结果
        """
        vote_a = self.rag_client.get_vote_score(chunk_id_a)
        vote_b = self.rag_client.get_vote_score(chunk_id_b)

        result_a = VoteResult(
            chunk_id=chunk_id_a,
            vote_count=vote_a,
            is_winner=vote_a > vote_b,
            opponent_id=chunk_id_b,
            opponent_votes=vote_b,
        )

        result_b = VoteResult(
            chunk_id=chunk_id_b,
            vote_count=vote_b,
            is_winner=vote_b > vote_a,
            opponent_id=chunk_id_a,
            opponent_votes=vote_a,
        )

        return result_a, result_b

    def vote_and_resolve(self, chunk_id_a: str, chunk_id_b: str,
                          threshold: int = 3) -> Optional[str]:
        """
        投票并解决冲突

        Args:
            chunk_id_a: chunk A
            chunk_id_b: chunk B
            threshold: 投票阈值

        Returns:
            被废弃的 chunk ID，或 None（未达阈值）
        """
        result_a, result_b = self.compare_votes(chunk_id_a, chunk_id_b)

        # 投票差异达到阈值
        diff = abs(result_a.vote_count - result_b.vote_count)
        if diff >= threshold:
            loser = result_a.chunk_id if result_a.vote_count < result_b.vote_count else result_b.chunk_id
            self.rag_client.deprecate_chunk(loser)
            logger.info(f"Voting resolved: {loser} deprecated (votes: {result_a.vote_count} vs {result_b.vote_count})")
            return loser

        logger.info(f"Voting inconclusive: {result_a.vote_count} vs {result_b.vote_count} (threshold={threshold})")
        return None

    def batch_record_references(self, chunk_ids: List[str]) -> Dict[str, int]:
        """
        批量记录引用

        Args:
            chunk_ids: chunk ID 列表

        Returns:
            {chunk_id: vote_count}
        """
        results = {}
        for chunk_id in chunk_ids:
            try:
                vote = self.record_reference(chunk_id)
                results[chunk_id] = vote
            except Exception as e:
                logger.warning(f"Failed to record reference for {chunk_id}: {e}")
        return results
