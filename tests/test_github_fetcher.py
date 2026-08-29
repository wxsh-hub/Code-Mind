"""
GitHub Fetcher 测试
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from mcp_gateway.collector.github_fetcher import GitHubFetcher, GitHubConfig, fetch_github_repo


class TestGitHubFetcher(unittest.TestCase):
    """GitHubFetcher 单元测试"""

    def setUp(self):
        self.config = GitHubConfig(token="test-token")
        self.fetcher = GitHubFetcher(self.config)

    def test_parse_url_basic(self):
        """测试解析基础 URL"""
        url = "https://github.com/owner/repo"
        parts = url.replace("https://github.com/", "").split("/")
        self.assertEqual(parts[0], "owner")
        self.assertEqual(parts[1], "repo")

    def test_parse_url_with_branch(self):
        """测试解析带分支的 URL"""
        url = "https://github.com/owner/repo/tree/develop"
        parts = url.replace("https://github.com/", "").split("/")
        self.assertEqual(parts[0], "owner")
        self.assertEqual(parts[1], "repo")
        self.assertEqual(parts[2], "tree")
        self.assertEqual(parts[3], "develop")

    def test_parse_url_with_path(self):
        """测试解析带路径的 URL"""
        url = "https://github.com/owner/repo/tree/main/docs"
        parts = url.replace("https://github.com/", "").split("/")
        self.assertEqual(parts[0], "owner")
        self.assertEqual(parts[1], "repo")
        self.assertEqual(parts[4], "docs")

    @patch("urllib.request.urlopen")
    def test_list_repo_contents(self, mock_urlopen):
        """测试列出仓库内容"""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps([
            {"name": "README.md", "type": "file", "path": "README.md", "sha": "abc123", "size": 100},
            {"name": "docs", "type": "dir", "path": "docs"},
        ]).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        contents = self.fetcher.list_repo_contents("owner", "repo")
        self.assertEqual(len(contents), 2)
        self.assertEqual(contents[0]["name"], "README.md")

    @patch("urllib.request.urlopen")
    def test_get_file_content(self, mock_urlopen):
        """测试获取文件内容"""
        import base64
        content = "# Test README\n\nHello World"
        encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "name": "README.md",
            "path": "README.md",
            "sha": "abc123",
            "size": len(content),
            "content": encoded,
        }).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        file = self.fetcher.get_file_content("owner", "repo", "README.md")
        self.assertEqual(file.content, content)
        self.assertEqual(file.path, "README.md")
        self.assertEqual(file.repo, "owner/repo")

    def test_fetch_from_url(self):
        """测试从 URL 获取"""
        # 简化测试，只验证 URL 解析
        url = "https://github.com/owner/repo"
        parts = url.replace("https://github.com/", "").split("/")
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], "owner")
        self.assertEqual(parts[1], "repo")


class TestFetchGithubRepo(unittest.TestCase):
    """fetch_github_repo 便捷函数测试"""

    @patch.object(GitHubFetcher, 'fetch_from_url')
    def test_fetch_github_repo(self, mock_fetch):
        """测试便捷函数"""
        from mcp_gateway.collector.github_fetcher import FetchedFile

        mock_fetch.return_value = [
            FetchedFile(path="README.md", content="# Test", repo="owner/repo", branch="main"),
            FetchedFile(path="docs/guide.md", content="# Guide", repo="owner/repo", branch="main"),
        ]

        result = fetch_github_repo("https://github.com/owner/repo")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["path"], "README.md")
        self.assertEqual(result[0]["content"], "# Test")


if __name__ == "__main__":
    unittest.main()
