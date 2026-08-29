"""
Contradiction Detector - 矛盾检测器

检测新导入的知识块是否与已有知识块存在矛盾
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from mcp_gateway.rag_client import RAGClient

logger = logging.getLogger(__name__)


@dataclass
class ContradictionResult:
    """矛盾检测结果"""
    has_contradiction: bool
    new_chunk_id: str
    conflicting_chunk_id: Optional[str] = None
    confidence: float = 0.0
    reason: str = ""
    resolution: str = ""  # 建议的解决方案


class ContradictionDetector:
    """矛盾检测器"""

    def __init__(self, rag_client: RAGClient, similarity_threshold: float = 0.7):
        """
        Args:
            rag_client: RAG 客户端实例
            similarity_threshold: 相似度阈值（超过此值才进行矛盾判断）
        """
        self.rag_client = rag_client
        self.similarity_threshold = similarity_threshold

    def detect(self, new_content: str, new_chunk_id: str,
               kb_id: Optional[str] = None, top_k: int = 5) -> List[ContradictionResult]:
        """
        检测新内容是否与已有内容矛盾

        Args:
            new_content: 新内容
            new_chunk_id: 新内容的 chunk ID
            kb_id: 限定知识库
            top_k: 检索数量

        Returns:
            List[ContradictionResult] 矛盾检测结果列表
        """
        results = []

        try:
            # Step 1: 相似 chunk 检索
            similar_chunks = self.rag_client.search_similar(
                query=new_content[:200],  # 取前 200 字符作为查询
                kb_id=kb_id,
                top_k=top_k,
            )

            # Step 2: 逐个判断是否矛盾
            for chunk in similar_chunks:
                existing_chunk_id = chunk.get("chunkId")
                if existing_chunk_id == new_chunk_id:
                    continue  # 跳过自身

                existing_content = chunk.get("content", "")
                metadata = chunk.get("metadata", {})

                # 如果已废弃，跳过
                if metadata.get("deprecated"):
                    continue

                # 判断是否矛盾
                contradiction = self._check_contradiction(
                    new_content, existing_content,
                    new_chunk_id, existing_chunk_id,
                )

                if contradiction:
                    results.append(contradiction)

        except Exception as e:
            logger.error(f"Contradiction detection failed: {e}")

        return results

    def _check_contradiction(self, new_content: str, existing_content: str,
                              new_chunk_id: str, existing_chunk_id: str) -> Optional[ContradictionResult]:
        """
        检查两段内容是否矛盾

        使用关键词和模式匹配进行初步判断
        """
        # 矛盾模式匹配
        contradiction_patterns = [
            # 数值矛盾
            (r"(\d+)\s*(个|条|种|步)", r"(\d+)\s*(个|条|种|步)"),
            # 否定矛盾
            (r"(应该|必须|需要)", r"(不应该|不能|禁止)"),
            (r"(启用|开启|打开)", r"(禁用|关闭|停用)"),
            # 版本矛盾
            (r"版本\s*(\d+\.\d+)", r"版本\s*(\d+\.\d+)"),
        ]

        new_lower = new_content.lower()
        existing_lower = existing_content.lower()

        # 计算关键词重叠度
        new_keywords = set(self._extract_keywords(new_content))
        existing_keywords = set(self._extract_keywords(existing_content))
        overlap = len(new_keywords & existing_keywords)
        total = len(new_keywords | existing_keywords)

        if total == 0:
            return None

        similarity = overlap / total

        # 检查否定模式（优先检查，不需要相似度阈值）
        negation_pairs = [
            ("应该", "不应该"), ("必须", "不必"), ("需要", "不需要"),
            ("启用", "禁用"), ("开启", "关闭"), ("打开", "关闭"),
            ("可以", "不可以"), ("允许", "禁止"),
        ]

        for pos, neg in negation_pairs:
            if (pos in new_lower and neg in existing_lower) or \
               (neg in new_lower and pos in existing_lower):
                return ContradictionResult(
                    has_contradiction=True,
                    new_chunk_id=new_chunk_id,
                    conflicting_chunk_id=existing_chunk_id,
                    confidence=0.8,
                    reason="检测到否定矛盾：一个说应该，另一个说不应该",
                    resolution="需要人工审核确认正确做法",
                )

        # 如果相似度太低，不认为是矛盾
        if similarity < self.similarity_threshold:
            return None

        # 如果相似度很高但不是否定矛盾，可能是补充关系
        if similarity > 0.9:
            return ContradictionResult(
                has_contradiction=True,
                new_chunk_id=new_chunk_id,
                conflicting_chunk_id=existing_chunk_id,
                confidence=0.5,
                reason="内容高度相似，可能是重复或版本更新",
                resolution="保留较新的版本",
            )

        return None

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（支持中英文）"""
        import re
        # 移除标点符号
        cleaned = re.sub(r"[^\w\s]", " ", text)

        # 英文按空格分割
        words = cleaned.split()

        # 中文按字符分割（2-4 字组合）
        chinese_chars = re.findall(r"[一-鿿]+", text)
        for phrase in chinese_chars:
            # 添加 2 字组合
            for i in range(len(phrase) - 1):
                words.append(phrase[i:i+2])
            # 添加完整短语
            if len(phrase) >= 2:
                words.append(phrase)

        # 过滤停用词和短词
        stop_words = {"的", "了", "是", "在", "和", "与", "或", "不", "有", "这", "那", "我", "你", "他", "使用", "应该", "可以"}
        return [w for w in words if len(w) > 1 and w not in stop_words]
