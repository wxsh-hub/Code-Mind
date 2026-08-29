"""
Memory Tools 测试
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from mcp_gateway.memory_tools import (
    MemoryManager, MemoryConfig,
    upload_memory_impl, ask_project_impl, list_projects_impl,
    set_manager,
)


class TestMemoryManager(unittest.TestCase):
    """MemoryManager 单元测试"""

    def setUp(self):
        self.manager = MemoryManager(MemoryConfig())
        self.manager._token = "test-token"

    @patch("urllib.request.urlopen")
    def test_get_or_create_project_kb_existing(self, mock_urlopen):
        """测试获取已存在的项目知识库"""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {
                "records": [
                    {"id": 123, "name": "memory_Code-Mind"},
                    {"id": 456, "name": "memory_MyApp"},
                ],
            },
        }).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        kb_id = self.manager.get_or_create_project_kb("Code-Mind")
        self.assertEqual(kb_id, "123")

    @patch("urllib.request.urlopen")
    def test_get_or_create_project_kb_new(self, mock_urlopen):
        """测试创建新项目知识库"""
        # Mock list (empty)
        list_resp = MagicMock()
        list_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {
                "records": [],
            },
        }).encode("utf-8")
        list_resp.__enter__ = lambda s: s
        list_resp.__exit__ = MagicMock(return_value=False)

        # Mock create
        create_resp = MagicMock()
        create_resp.read.return_value = json.dumps({
            "code": "0",
            "data": 789,
        }).encode("utf-8")
        create_resp.__enter__ = lambda s: s
        create_resp.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [list_resp, create_resp]

        kb_id = self.manager.get_or_create_project_kb("NewProject")
        self.assertEqual(kb_id, "789")

    @patch("urllib.request.urlopen")
    @patch("time.sleep")
    def test_upload_memory(self, mock_sleep, mock_urlopen):
        """测试上传记忆文件"""
        # Mock login
        login_resp = MagicMock()
        login_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {"token": "test-token"},
        }).encode("utf-8")
        login_resp.__enter__ = lambda s: s
        login_resp.__exit__ = MagicMock(return_value=False)

        # Mock list KB
        list_resp = MagicMock()
        list_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {
                "records": [{"id": 100, "name": "memory_TestProject"}],
            },
        }).encode("utf-8")
        list_resp.__enter__ = lambda s: s
        list_resp.__exit__ = MagicMock(return_value=False)

        # Mock upload
        upload_resp = MagicMock()
        upload_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {"id": 200},
        }).encode("utf-8")
        upload_resp.__enter__ = lambda s: s
        upload_resp.__exit__ = MagicMock(return_value=False)

        # Mock chunk
        chunk_resp = MagicMock()
        chunk_resp.read.return_value = json.dumps({
            "code": "0",
            "data": None,
        }).encode("utf-8")
        chunk_resp.__enter__ = lambda s: s
        chunk_resp.__exit__ = MagicMock(return_value=False)

        # Mock get chunks (for confidence calculation)
        chunks_resp = MagicMock()
        chunks_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {"records": [{"id": "300"}, {"id": "301"}]},
        }).encode("utf-8")
        chunks_resp.__enter__ = lambda s: s
        chunks_resp.__exit__ = MagicMock(return_value=False)

        # Mock calculate confidence (for each chunk)
        conf_resp = MagicMock()
        conf_resp.read.return_value = json.dumps({
            "code": "0",
            "data": 5,
        }).encode("utf-8")
        conf_resp.__enter__ = lambda s: s
        conf_resp.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [
            login_resp, list_resp, upload_resp, chunk_resp,
            chunks_resp, conf_resp, conf_resp  # chunks + 2x confidence
        ]

        manager = MemoryManager(MemoryConfig())
        result = manager.upload_memory("TestProject", "test.md", "# Test Content")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["project"], "TestProject")

    @patch("urllib.request.urlopen")
    def test_ask_project(self, mock_urlopen):
        """测试项目问答"""
        # Mock login
        login_resp = MagicMock()
        login_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {"token": "test-token"},
        }).encode("utf-8")
        login_resp.__enter__ = lambda s: s
        login_resp.__exit__ = MagicMock(return_value=False)

        # Mock list KB
        list_resp = MagicMock()
        list_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {
                "records": [{"id": 100, "name": "memory_TestProject"}],
            },
        }).encode("utf-8")
        list_resp.__enter__ = lambda s: s
        list_resp.__exit__ = MagicMock(return_value=False)

        # Mock search
        search_resp = MagicMock()
        search_resp.read.return_value = json.dumps({
            "code": "0",
            "data": [
                {"chunkId": "1", "content": "RAG 模块完成度 90%", "metadata": {}},
            ],
        }).encode("utf-8")
        search_resp.__enter__ = lambda s: s
        search_resp.__exit__ = MagicMock(return_value=False)

        # Mock reference
        ref_resp = MagicMock()
        ref_resp.read.return_value = json.dumps({"code": "0"}).encode("utf-8")
        ref_resp.__enter__ = lambda s: s
        ref_resp.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [login_resp, list_resp, search_resp, ref_resp]

        manager = MemoryManager(MemoryConfig())
        result = manager.ask_project("TestProject", "RAG 完成度")

        self.assertEqual(result["project"], "TestProject")
        self.assertEqual(result["count"], 1)

    @patch("urllib.request.urlopen")
    def test_list_projects(self, mock_urlopen):
        """测试列出项目"""
        # Mock login
        login_resp = MagicMock()
        login_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {"token": "test-token"},
        }).encode("utf-8")
        login_resp.__enter__ = lambda s: s
        login_resp.__exit__ = MagicMock(return_value=False)

        # Mock list KB
        list_resp = MagicMock()
        list_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {
                "records": [
                    {"id": 100, "name": "memory_ProjectA"},
                    {"id": 200, "name": "memory_ProjectB"},
                    {"id": 300, "name": "other_kb"},
                ],
            },
        }).encode("utf-8")
        list_resp.__enter__ = lambda s: s
        list_resp.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [login_resp, list_resp]

        manager = MemoryManager(MemoryConfig())
        result = manager.list_projects()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["project"], "ProjectA")


class TestMemoryToolsImpl(unittest.TestCase):
    """Memory Tools 实现测试"""

    def setUp(self):
        self.mock_manager = MagicMock(spec=MemoryManager)
        set_manager(self.mock_manager)

    def test_upload_memory_impl(self):
        """测试 upload_memory_impl"""
        self.mock_manager.upload_memory.return_value = {
            "status": "success",
            "project": "TestProject",
            "kb_id": "100",
            "doc_id": "200",
            "filename": "test.md",
        }

        result = upload_memory_impl("TestProject", "test.md", "# Test")

        self.assertEqual(result["status"], "success")
        self.mock_manager.upload_memory.assert_called_once()

    def test_ask_project_impl(self):
        """测试 ask_project_impl"""
        self.mock_manager.ask_project.return_value = {
            "project": "TestProject",
            "question": "RAG 完成度",
            "results": [{"chunkId": "1", "content": "90%"}],
            "count": 1,
        }

        result = ask_project_impl("TestProject", "RAG 完成度")

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["project"], "TestProject")

    def test_list_projects_impl(self):
        """测试 list_projects_impl"""
        self.mock_manager.list_projects.return_value = [
            {"project": "ProjectA", "kb_id": "100"},
            {"project": "ProjectB", "kb_id": "200"},
        ]

        result = list_projects_impl()

        self.assertEqual(result["count"], 2)


if __name__ == "__main__":
    unittest.main()
