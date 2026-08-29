"""
Conflict 模块测试
"""

import unittest
from unittest.mock import MagicMock
from mcp_gateway.rag_client import RAGClient
from mcp_gateway.conflict.detector import ContradictionDetector
from mcp_gateway.conflict.resolver import ConflictResolver
from mcp_gateway.conflict.voter import VotingMechanism
from mcp_gateway.conflict.aware_search import ConflictAwareSearch


class TestContradictionDetector(unittest.TestCase):
    """ContradictionDetector 单元测试"""

    def setUp(self):
        self.mock_client = MagicMock(spec=RAGClient)
        self.detector = ContradictionDetector(self.mock_client, similarity_threshold=0.3)

    def test_detect_negation_contradiction(self):
        """测试检测否定矛盾"""
        self.mock_client.search_similar.return_value = [
            {
                "chunkId": "456",
                "content": "应该使用 Redis 缓存来提高性能",
                "metadata": {"deprecated": False},
            },
        ]

        results = self.detector.detect(
            new_content="不应该使用 Redis 缓存，会影响数据一致性",
            new_chunk_id="123",
        )

        self.assertGreater(len(results), 0)
        self.assertTrue(results[0].has_contradiction)
        self.assertIn("否定矛盾", results[0].reason)

    def test_detect_no_contradiction(self):
        """测试无矛盾"""
        self.mock_client.search_similar.return_value = [
            {
                "chunkId": "456",
                "content": "Spring Boot 是一个框架",
                "metadata": {"deprecated": False},
            },
        ]

        results = self.detector.detect(
            new_content="Redis 是一个缓存数据库",
            new_chunk_id="123",
        )

        self.assertEqual(len(results), 0)

    def test_detect_skips_deprecated(self):
        """测试跳过已废弃的 chunk"""
        self.mock_client.search_similar.return_value = [
            {
                "chunkId": "456",
                "content": "应该使用 Redis 缓存",
                "metadata": {"deprecated": True},
            },
        ]

        results = self.detector.detect(
            new_content="不应该使用 Redis 缓存",
            new_chunk_id="123",
        )

        self.assertEqual(len(results), 0)

    def test_detect_skips_self(self):
        """测试跳过自身"""
        self.mock_client.search_similar.return_value = [
            {
                "chunkId": "123",  # 同一个 ID
                "content": "测试内容",
                "metadata": {"deprecated": False},
            },
        ]

        results = self.detector.detect(
            new_content="测试内容",
            new_chunk_id="123",
        )

        self.assertEqual(len(results), 0)


class TestConflictResolver(unittest.TestCase):
    """ConflictResolver 单元测试"""

    def setUp(self):
        self.mock_client = MagicMock(spec=RAGClient)
        self.resolver = ConflictResolver(self.mock_client, vote_threshold=3)

    def test_resolve_same_file_takes_newer(self):
        """测试同文件冲突保留新版本"""
        from mcp_gateway.conflict.detector import ContradictionResult

        contradiction = ContradictionResult(
            has_contradiction=True,
            new_chunk_id="123",
            conflicting_chunk_id="456",
            confidence=0.8,
        )

        new_metadata = {"sourceRef": "docs/规范.md"}
        existing_metadata = {"sourceRef": "docs/规范.md"}

        action = self.resolver.resolve(contradiction, new_metadata, existing_metadata)

        self.assertEqual(action.action, "deprecate")
        self.assertEqual(action.chunk_id, "456")  # 旧版本被废弃

    def test_resolve_different_files_set_conflict_pair(self):
        """测试不同文件冲突设置矛盾对"""
        from mcp_gateway.conflict.detector import ContradictionResult

        contradiction = ContradictionResult(
            has_contradiction=True,
            new_chunk_id="123",
            conflicting_chunk_id="789",
            confidence=0.8,
        )

        new_metadata = {"sourceRef": "docs/团队A规范.md"}
        existing_metadata = {"sourceRef": "docs/团队B规范.md"}

        action = self.resolver.resolve(contradiction, new_metadata, existing_metadata)

        self.assertEqual(action.action, "set_conflict_pair")
        self.mock_client.set_conflict_pair.assert_called_once_with("123", "789")

    def test_resolve_by_voting_threshold_reached(self):
        """测试投票达到阈值"""
        self.mock_client.get_vote_score.side_effect = lambda cid: 10 if cid == "123" else 2

        action = self.resolver.resolve_by_voting("123", "456")

        self.assertEqual(action.action, "deprecate")
        self.assertEqual(action.chunk_id, "456")  # 低票方被废弃
        self.mock_client.deprecate_chunk.assert_called_once_with("456")

    def test_resolve_by_voting_threshold_not_reached(self):
        """测试投票未达阈值"""
        self.mock_client.get_vote_score.side_effect = lambda cid: 3 if cid == "123" else 2

        action = self.resolver.resolve_by_voting("123", "456")

        self.assertEqual(action.action, "keep_both")


class TestVotingMechanism(unittest.TestCase):
    """VotingMechanism 单元测试"""

    def setUp(self):
        self.mock_client = MagicMock(spec=RAGClient)
        self.voter = VotingMechanism(self.mock_client)

    def test_record_reference(self):
        """测试记录引用"""
        self.mock_client.get_vote_score.return_value = 5

        score = self.voter.record_reference("123")

        self.mock_client.record_reference.assert_called_once_with("123")
        self.assertEqual(score, 5)

    def test_compare_votes(self):
        """测试比较投票"""
        self.mock_client.get_vote_score.side_effect = lambda cid: 10 if cid == "123" else 3

        result_a, result_b = self.voter.compare_votes("123", "456")

        self.assertTrue(result_a.is_winner)
        self.assertFalse(result_b.is_winner)
        self.assertEqual(result_a.vote_count, 10)
        self.assertEqual(result_b.vote_count, 3)

    def test_vote_and_resolve(self):
        """测试投票解决"""
        self.mock_client.get_vote_score.side_effect = lambda cid: 10 if cid == "123" else 2

        loser = self.voter.vote_and_resolve("123", "456", threshold=5)

        self.assertEqual(loser, "456")
        self.mock_client.deprecate_chunk.assert_called_once_with("456")

    def test_batch_record_references(self):
        """测试批量记录引用"""
        self.mock_client.get_vote_score.return_value = 1

        results = self.voter.batch_record_references(["1", "2", "3"])

        self.assertEqual(len(results), 3)
        self.assertEqual(self.mock_client.record_reference.call_count, 3)


class TestConflictAwareSearch(unittest.TestCase):
    """ConflictAwareSearch 单元测试"""

    def setUp(self):
        self.mock_client = MagicMock(spec=RAGClient)
        self.search = ConflictAwareSearch(self.mock_client)

    def test_search_marks_conflicts(self):
        """测试搜索标记矛盾"""
        self.mock_client.search_similar.return_value = [
            {
                "chunkId": "123",
                "content": "应该使用 Redis",
                "metadata": {"voteCount": 5, "deprecated": False, "conflictPairId": "456"},
            },
            {
                "chunkId": "789",
                "content": "MySQL 索引优化",
                "metadata": {"voteCount": 3, "deprecated": False, "conflictPairId": None},
            },
        ]

        results = self.search.search("数据库优化")

        self.assertEqual(len(results), 2)
        self.assertTrue(results[0].has_conflict)
        self.assertFalse(results[1].has_conflict)

    def test_search_excludes_deprecated(self):
        """测试排除已废弃"""
        self.mock_client.search_similar.return_value = [
            {
                "chunkId": "123",
                "content": "旧内容",
                "metadata": {"voteCount": 0, "deprecated": True, "conflictPairId": None},
            },
            {
                "chunkId": "456",
                "content": "新内容",
                "metadata": {"voteCount": 5, "deprecated": False, "conflictPairId": None},
            },
        ]

        results = self.search.search("test", exclude_deprecated=True)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk_id, "456")

    def test_search_with_conflict_context(self):
        """测试带矛盾上下文的搜索"""
        self.mock_client.search_similar.return_value = [
            {
                "chunkId": "123",
                "content": "应该使用 Redis",
                "metadata": {"voteCount": 5, "deprecated": False, "conflictPairId": "456"},
            },
        ]

        result = self.search.search_with_conflict_context("缓存")

        self.assertIn("conflicts", result)
        self.assertGreater(len(result["conflicts"]), 0)


if __name__ == "__main__":
    unittest.main()
