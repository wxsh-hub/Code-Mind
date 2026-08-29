"""
RAG Tools 测试
"""

import unittest
from unittest.mock import patch, MagicMock
from mcp_gateway.rag_tools import search_experience_impl, set_rag_client
from mcp_gateway.rag_client import RAGClient


class TestRAGTools(unittest.TestCase):
    """RAG Tools 单元测试"""

    def setUp(self):
        self.mock_client = MagicMock(spec=RAGClient)
        set_rag_client(self.mock_client)

    def test_search_experience_success(self):
        """测试 search_experience 成功场景"""
        self.mock_client.search_similar.return_value = [
            {
                "chunkId": "123",
                "content": "Spring Boot 分页使用 PageHelper",
                "docId": "1",
                "kbId": "10",
                "metadata": {"voteCount": 5, "deprecated": False},
            },
            {
                "chunkId": "456",
                "content": "MyBatis Plus 分页配置",
                "docId": "2",
                "kbId": "10",
                "metadata": {"voteCount": 3, "deprecated": False},
            },
        ]

        result = search_experience_impl(query="分页实现", top_k=5)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result_count"], 2)
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["chunk_id"], "123")

        # 验证记录引用被调用
        self.assertEqual(self.mock_client.record_reference.call_count, 2)

    def test_search_experience_error(self):
        """测试 search_experience 错误场景"""
        self.mock_client.search_similar.side_effect = RuntimeError("Connection failed")

        result = search_experience_impl(query="test")

        self.assertEqual(result["status"], "error")
        self.assertIn("Connection failed", result["error"])
        self.assertEqual(result["result_count"], 0)

    def test_search_experience_with_kb_id(self):
        """测试限定知识库搜索"""
        self.mock_client.search_similar.return_value = []

        search_experience_impl(query="test", kb_id="10", top_k=3)

        self.mock_client.search_similar.assert_called_once_with(
            query="test", kb_id="10", top_k=3,
        )

    def test_search_experience_records_references(self):
        """测试搜索后记录引用"""
        self.mock_client.search_similar.return_value = [
            {
                "chunkId": "789",
                "content": "test content",
                "docId": "1",
                "kbId": "10",
                "metadata": {},
            },
        ]

        search_experience_impl(query="test")

        self.mock_client.record_reference.assert_called_once_with("789")


if __name__ == "__main__":
    unittest.main()
