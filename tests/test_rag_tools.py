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
        # mock rag_chat_with_sources
        self.mock_client.rag_chat_with_sources.return_value = {
            "answer": "Spring Boot 分页使用 PageHelper",
            "sources": [
                {
                    "docId": "1",
                    "docName": "test.md",
                    "excerpt": "Spring Boot 分页使用 PageHelper",
                },
                {
                    "docId": "2",
                    "docName": "test2.md",
                    "excerpt": "MyBatis Plus 分页配置",
                },
            ],
        }
        # mock get_chunks
        self.mock_client.get_chunks.return_value = {
            "records": [{"id": "123"}]
        }

        result = search_experience_impl(query="分页实现", top_k=5)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result_count"], 2)
        self.assertEqual(len(result["results"]), 2)
        self.assertIn("PageHelper", result["ai_answer"])

    def test_search_experience_error(self):
        """测试 search_experience 错误场景"""
        self.mock_client.rag_chat_with_sources.side_effect = RuntimeError("Connection failed")

        result = search_experience_impl(query="test")

        self.assertEqual(result["status"], "error")
        self.assertIn("Connection failed", result["error"])
        self.assertEqual(result["result_count"], 0)

    def test_search_experience_returns_ai_answer(self):
        """测试 search_experience 返回 AI 回答"""
        self.mock_client.rag_chat_with_sources.return_value = {
            "answer": "根据知识库，推荐使用 PostgreSQL",
            "sources": [
                {"docId": "1", "docName": "db.md", "excerpt": "PostgreSQL 是最佳选择"},
            ],
        }
        self.mock_client.get_chunks.return_value = {"records": [{"id": "789"}]}

        result = search_experience_impl(query="推荐什么数据库")

        self.assertEqual(result["status"], "success")
        self.assertIn("PostgreSQL", result["ai_answer"])
        self.assertEqual(result["result_count"], 1)

    def test_search_experience_records_references(self):
        """测试搜索后记录引用"""
        self.mock_client.rag_chat_with_sources.return_value = {
            "answer": "test answer",
            "sources": [
                {"docId": "1", "docName": "test.md", "excerpt": "test content"},
            ],
        }
        self.mock_client.get_chunks.return_value = {"records": [{"id": "789"}]}

        search_experience_impl(query="test")

        self.mock_client.record_reference.assert_called_once_with("789")


if __name__ == "__main__":
    unittest.main()
