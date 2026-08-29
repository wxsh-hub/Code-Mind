"""
GitLab Fetcher - 从 GitLab 仓库获取 MD 文件

支持按项目、分支、路径模式批量拉取 Markdown 文件
"""

import logging
import urllib.request
import urllib.error
import json
import base64
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class GitLabConfig:
    """GitLab 连接配置"""
    base_url: str = "https://gitlab.example.com"
    token: str = ""
    api_version: str = "v4"


@dataclass
class FetchedFile:
    """获取到的文件"""
    path: str
    content: str
    project_id: str
    branch: str
    last_commit_date: Optional[str] = None
    author: Optional[str] = None
    size: int = 0


class GitLabFetcher:
    """GitLab 文件获取器"""

    def __init__(self, config: Optional[GitLabConfig] = None):
        self.config = config or GitLabConfig()

    def _request(self, path: str) -> Any:
        """发送 GitLab API 请求"""
        url = f"{self.config.base_url}/api/{self.config.api_version}{path}"
        req = urllib.request.Request(url, headers={
            "PRIVATE-TOKEN": self.config.token,
            "Content-Type": "application/json",
        })

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            logger.error(f"GitLab API error {e.code}: {url}")
            raise
        except urllib.error.URLError as e:
            logger.error(f"GitLab connection error: {e}")
            raise

    def list_projects(self, search: str = "", per_page: int = 20) -> List[Dict]:
        """列出项目"""
        params = f"?search={search}&per_page={per_page}"
        return self._request(f"/projects{params}")

    def list_files(self, project_id: str, path: str = "",
                   ref: str = "main", recursive: bool = True) -> List[Dict]:
        """列出仓库中的文件"""
        params = f"?path={path}&ref={ref}&recursive={'true' if recursive else 'false'}&per_page=100"
        return self._request(f"/projects/{project_id}/repository/tree{params}")

    def get_file_content(self, project_id: str, file_path: str,
                         ref: str = "main") -> FetchedFile:
        """获取单个文件内容"""
        encoded_path = urllib.request.quote(file_path, safe="")
        data = self._request(f"/projects/{project_id}/repository/files/{encoded_path}?ref={ref}")

        # Base64 解码
        content = base64.b64decode(data.get("content", "")).decode("utf-8")

        return FetchedFile(
            path=file_path,
            content=content,
            project_id=str(project_id),
            branch=ref,
            size=data.get("size", 0),
        )

    def fetch_md_files(self, project_id: str, path: str = "",
                       ref: str = "main") -> List[FetchedFile]:
        """批量获取仓库中的 MD 文件"""
        files = self.list_files(project_id, path, ref, recursive=True)
        md_files = [f for f in files if f.get("path", "").endswith(".md")]

        result = []
        for f in md_files:
            try:
                fetched = self.get_file_content(project_id, f["path"], ref)
                result.append(fetched)
            except Exception as e:
                logger.warning(f"Failed to fetch {f['path']}: {e}")

        logger.info(f"Fetched {len(result)} MD files from project {project_id}")
        return result

    def fetch_multiple_projects(self, project_ids: List[str],
                                 path: str = "", ref: str = "main") -> List[FetchedFile]:
        """从多个项目批量获取 MD 文件"""
        all_files = []
        for pid in project_ids:
            try:
                files = self.fetch_md_files(pid, path, ref)
                all_files.extend(files)
            except Exception as e:
                logger.error(f"Failed to fetch from project {pid}: {e}")
        return all_files
