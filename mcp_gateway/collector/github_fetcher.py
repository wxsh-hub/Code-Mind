"""
GitHub Fetcher - 从 GitHub 仓库获取文件

支持按仓库、分支、路径模式批量拉取文件
"""

import logging
import urllib.request
import urllib.error
import json
import base64
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GitHubConfig:
    """GitHub 连接配置"""
    token: str = ""  # GitHub Personal Access Token (可选，提高速率限制)
    api_url: str = "https://api.github.com"


@dataclass
class FetchedFile:
    """获取到的文件"""
    path: str
    content: str
    repo: str
    branch: str
    sha: str = ""
    size: int = 0


class GitHubFetcher:
    """GitHub 文件获取器"""

    def __init__(self, config: Optional[GitHubConfig] = None):
        self.config = config or GitHubConfig()

    def _request(self, path: str) -> Any:
        """发送 GitHub API 请求"""
        url = f"{self.config.api_url}{path}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Code-Mind-MCP-Gateway",
        }
        if self.config.token:
            headers["Authorization"] = f"token {self.config.token}"

        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            logger.error(f"GitHub API error {e.code}: {url}")
            raise
        except urllib.error.URLError as e:
            logger.error(f"GitHub connection error: {e}")
            raise

    def list_repo_contents(self, owner: str, repo: str, path: str = "",
                           ref: str = "main") -> List[Dict]:
        """列出仓库内容"""
        params = f"?ref={ref}" if ref else ""
        return self._request(f"/repos/{owner}/{repo}/contents/{path}{params}")

    def get_file_content(self, owner: str, repo: str, file_path: str,
                         ref: str = "main") -> FetchedFile:
        """获取单个文件内容"""
        data = self._request(f"/repos/{owner}/{repo}/contents/{file_path}?ref={ref}")

        # Base64 解码
        content = base64.b64decode(data.get("content", "")).decode("utf-8")

        return FetchedFile(
            path=file_path,
            content=content,
            repo=f"{owner}/{repo}",
            branch=ref,
            sha=data.get("sha", ""),
            size=data.get("size", 0),
        )

    def fetch_files_recursive(self, owner: str, repo: str, path: str = "",
                               ref: str = "main", extensions: List[str] = None) -> List[FetchedFile]:
        """递归获取仓库中的文件"""
        if extensions is None:
            extensions = [".md", ".txt", ".rst"]

        result = []
        contents = self.list_repo_contents(owner, repo, path, ref)

        for item in contents:
            item_path = item.get("path", "")
            item_type = item.get("type", "")

            if item_type == "file":
                # 检查文件扩展名
                if any(item_path.endswith(ext) for ext in extensions):
                    try:
                        fetched = self.get_file_content(owner, repo, item_path, ref)
                        result.append(fetched)
                    except Exception as e:
                        logger.warning(f"Failed to fetch {item_path}: {e}")

            elif item_type == "dir":
                # 递归获取子目录
                try:
                    sub_files = self.fetch_files_recursive(owner, repo, item_path, ref, extensions)
                    result.extend(sub_files)
                except Exception as e:
                    logger.warning(f"Failed to fetch directory {item_path}: {e}")

        return result

    def fetch_repo(self, owner: str, repo: str, path: str = "",
                    ref: str = "main", extensions: List[str] = None) -> List[FetchedFile]:
        """获取仓库文件（主入口）"""
        logger.info(f"Fetching files from {owner}/{repo} (path={path}, ref={ref})")
        files = self.fetch_files_recursive(owner, repo, path, ref, extensions)
        logger.info(f"Fetched {len(files)} files from {owner}/{repo}")
        return files

    def fetch_from_url(self, github_url: str, extensions: List[str] = None) -> List[FetchedFile]:
        """从 GitHub URL 获取文件

        支持格式：
        - https://github.com/owner/repo
        - https://github.com/owner/repo/tree/branch
        - https://github.com/owner/repo/tree/branch/path
        """
        # 解析 URL
        parts = github_url.replace("https://github.com/", "").split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {github_url}")

        owner = parts[0]
        repo = parts[1]

        # 解析分支和路径
        ref = "main"
        path = ""
        if len(parts) > 3 and parts[2] == "tree":
            ref = parts[3]
            if len(parts) > 4:
                path = "/".join(parts[4:])

        return self.fetch_repo(owner, repo, path, ref, extensions)


def fetch_github_repo(github_url: str, token: str = "",
                       extensions: List[str] = None) -> List[Dict[str, str]]:
    """便捷函数：从 GitHub URL 获取文件内容

    Returns:
        [{"path": "README.md", "content": "..."}, ...]
    """
    config = GitHubConfig(token=token) if token else GitHubConfig()
    fetcher = GitHubFetcher(config)
    files = fetcher.fetch_from_url(github_url, extensions)

    return [{"path": f.path, "content": f.content} for f in files]
