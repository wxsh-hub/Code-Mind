"""
Conflict Review 测试
"""

import unittest
from unittest.mock import MagicMock
from mcp_gateway.conflict_review import (
    detect_negation, list_conflicts_impl, review_conflict_impl,
    set_client,
)
from mcp_gateway.rag_client import RAGClient


class TestDetectNegation(unittest.TestCase):
    """否定检测测试"""

    def test_detect_should_should_not(self):
        """测试 应该 vs 不应该"""
        self.assertTrue(detect_negation("应该使用 Redis", "不应该使用 Redis"))

    def test_detect_enable_disable(self):
        """测试 启用 vs 禁用"""
        self.assertTrue(detect_negation("启用缓存", "禁用缓存"))

    def test_detect_no_negation(self):
        """测试无否定"""
        self.assertFalse(detect_negation("使用 Redis", "使用 MySQL"))

    def test_detect_symmetric(self):
        """测试对称性"""
        self.assertTrue(detect_negation("不应该使用", "应该使用"))


class TestConflictReviewTools(unittest.TestCase):
    """矛盾审核工具测试"""

    def setUp(self):
        self.mock_client = MagicMock(spec=RAGClient)
        self.mock_client.ensure_logged_in = MagicMock()
        set_client(self.mock_client)

    def test_list_conflicts_empty(self):
        """测试列出矛盾对（空）"""
        self.mock_client._request.return_value = {"data": []}

        result = list_conflicts_impl("TestProject")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["pagination"]["total"], 0)

    def test_list_conflicts_found(self):
        """测试列出矛盾对（找到）"""
        self.mock_client._request.return_value = {
            "data": [
                {
                    "chunkId": "1",
                    "content": "应该使用 Redis 缓存",
                    "confidence": 5,
                    "score": 0.9,
                },
                {
                    "chunkId": "2",
                    "content": "不应该使用 Redis 缓存",
                    "confidence": 4,
                    "score": 0.8,
                },
            ]
        }

        result = list_conflicts_impl("TestProject")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["pagination"]["total"], 1)
        self.assertEqual(result["conflicts"][0]["contradiction_type"], "negation")

    def test_review_conflict_winner_a(self):
        """测试审核选择 A"""
        self.mock_client.deprecate_chunk.return_value = None

        result = review_conflict_impl("TestProject", "1", "2", "a", "A 正确")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["action"], "deprecated")
        self.assertEqual(result["deprecated_chunk"], "2")
        self.mock_client.deprecate_chunk.assert_called_once_with("2")

    def test_review_conflict_winner_b(self):
        """测试审核选择 B"""
        self.mock_client.deprecate_chunk.return_value = None

        result = review_conflict_impl("TestProject", "1", "2", "b", "B 正确")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["deprecated_chunk"], "1")

    def test_review_conflict_winner_both(self):
        """测试审核选择 Both"""
        self.mock_client.set_conflict_pair.return_value = None

        result = review_conflict_impl("TestProject", "1", "2", "both", "两者都有效")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["action"], "kept_both")
        self.mock_client.set_conflict_pair.assert_called_once_with("1", "2")


if __name__ == "__main__":
    unittest.main()
