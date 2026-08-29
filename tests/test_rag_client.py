"""
RAG Client 测试
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from mcp_gateway.rag_client import RAGClient, RAGConfig


class TestRAGClient(unittest.TestCase):
    """RAG Client 单元测试"""

    def setUp(self):
        self.config = RAGConfig(
            base_url="http://localhost:9090/api/ragent",
            username="admin",
            password="admin",
        )
        self.client = RAGClient(self.config)

    @patch("urllib.request.urlopen")
    def test_login(self, mock_urlopen):
        """测试登录获取 token"""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {"token": "test-token-123"},
        }).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        token = self.client.login()
        self.assertEqual(token, "test-token-123")
        self.assertEqual(self.client._token, "test-token-123")

    @patch("urllib.request.urlopen")
    def test_search_similar(self, mock_urlopen):
        """测试相似检索"""
        # Mock login
        login_resp = MagicMock()
        login_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {"token": "test-token"},
        }).encode("utf-8")
        login_resp.__enter__ = lambda s: s
        login_resp.__exit__ = MagicMock(return_value=False)

        # Mock search
        search_resp = MagicMock()
        search_resp.read.return_value = json.dumps({
            "code": "0",
            "data": [
                {
                    "chunkId": "123",
                    "content": "Spring Boot 分页实现",
                    "docId": "1",
                    "kbId": "10",
                    "metadata": {"voteCount": 5},
                }
            ],
        }).encode("utf-8")
        search_resp.__enter__ = lambda s: s
        search_resp.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [login_resp, search_resp]

        results = self.client.search_similar("分页", top_k=5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chunkId"], "123")

    @patch("urllib.request.urlopen")
    def test_record_reference(self, mock_urlopen):
        """测试记录引用"""
        # Mock login
        login_resp = MagicMock()
        login_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {"token": "test-token"},
        }).encode("utf-8")
        login_resp.__enter__ = lambda s: s
        login_resp.__exit__ = MagicMock(return_value=False)

        # Mock reference
        ref_resp = MagicMock()
        ref_resp.read.return_value = json.dumps({
            "code": "0",
            "data": None,
        }).encode("utf-8")
        ref_resp.__enter__ = lambda s: s
        ref_resp.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [login_resp, ref_resp]

        # 应该不抛异常
        self.client.record_reference("123")

    @patch("urllib.request.urlopen")
    def test_get_vote_score(self, mock_urlopen):
        """测试查询投票分数"""
        # Mock login
        login_resp = MagicMock()
        login_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {"token": "test-token"},
        }).encode("utf-8")
        login_resp.__enter__ = lambda s: s
        login_resp.__exit__ = MagicMock(return_value=False)

        # Mock vote
        vote_resp = MagicMock()
        vote_resp.read.return_value = json.dumps({
            "code": "0",
            "data": 7,
        }).encode("utf-8")
        vote_resp.__enter__ = lambda s: s
        vote_resp.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [login_resp, vote_resp]

        score = self.client.get_vote_score("123")
        self.assertEqual(score, 7)


if __name__ == "__main__":
    unittest.main()
