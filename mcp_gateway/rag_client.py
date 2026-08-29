"""
RAG HTTP Client - 用于与 ragent 服务通信

提供知识库检索、chunk 管理等 HTTP 接口调用
"""

import logging
import urllib.request
import urllib.error
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RAGConfig:
    """ragent 连接配置"""
    base_url: str = "http://localhost:9090/api/ragent"
    username: str = "admin"
    password: str = "admin"
    timeout: int = 30


class RAGClient:
    """ragent HTTP 客户端"""

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        self._token: Optional[str] = None

    def _request(self, method: str, path: str, data: Optional[dict] = None,
                 headers: Optional[dict] = None) -> dict:
        """发送 HTTP 请求"""
        url = f"{self.config.base_url}{path}"
        req_headers = {"Content-Type": "application/json; charset=UTF-8"}
        if self._token:
            req_headers["Authorization"] = self._token
        if headers:
            req_headers.update(headers)

        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=req_headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            logger.error(f"HTTP {e.code} from {url}: {body}")
            raise RuntimeError(f"HTTP {e.code}: {body}")
        except urllib.error.URLError as e:
            logger.error(f"Connection error to {url}: {e}")
            raise RuntimeError(f"Connection error: {e}")

    def login(self) -> str:
        """登录获取 token"""
        resp = self._request("POST", "/auth/login", {
            "username": self.config.username,
            "password": self.config.password,
        })
        self._token = resp["data"]["token"]
        logger.info("RAG client login successful")
        return self._token

    def ensure_logged_in(self):
        """确保已登录"""
        if not self._token:
            self.login()

    def search_similar(self, query: str, kb_id: Optional[str] = None,
                       top_k: int = 10) -> List[Dict[str, Any]]:
        """相似 chunk 检索"""
        self.ensure_logged_in()
        body: Dict[str, Any] = {"query": query, "topK": top_k}
        if kb_id:
            body["kbId"] = kb_id
        resp = self._request("POST", "/knowledge-base/search/similar", body)
        return resp.get("data", [])

    def record_reference(self, chunk_id: str) -> None:
        """记录 chunk 被引用（vote_count + 1）"""
        self.ensure_logged_in()
        self._request("POST", f"/knowledge-base/chunks/{chunk_id}/reference")

    def get_vote_score(self, chunk_id: str) -> int:
        """查询 chunk 投票分数"""
        self.ensure_logged_in()
        resp = self._request("GET", f"/knowledge-base/chunks/{chunk_id}/vote")
        return resp.get("data", 0)

    def set_conflict_pair(self, chunk_id: str, conflict_pair_id: str) -> None:
        """设置矛盾对"""
        self.ensure_logged_in()
        self._request("POST", f"/knowledge-base/chunks/{chunk_id}/conflict-pair", {
            "conflictPairId": conflict_pair_id,
        })

    def deprecate_chunk(self, chunk_id: str) -> None:
        """标记 chunk 为废弃"""
        self.ensure_logged_in()
        self._request("POST", f"/knowledge-base/chunks/{chunk_id}/deprecate")

    def calculate_confidence(self, chunk_id: str) -> int:
        """计算并更新 chunk 置信度"""
        self.ensure_logged_in()
        resp = self._request("POST", f"/knowledge-base/chunks/{chunk_id}/calculate-confidence")
        return resp.get("data", 1)

    def get_confidence(self, chunk_id: str) -> int:
        """获取 chunk 置信度"""
        self.ensure_logged_in()
        resp = self._request("GET", f"/knowledge-base/chunks/{chunk_id}/confidence")
        return resp.get("data", 1)

    def normalize_confidence(self, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        """批量归一化置信度到100 总分"""
        self.ensure_logged_in()
        resp = self._request("POST", "/knowledge-base/chunks/normalize-confidence", chunk_ids)
        return resp.get("data", [])

    def rag_chat(self, question: str, max_tokens: int = 2000) -> str:
        """RAG 问答（SSE 流式）"""
        self.ensure_logged_in()
        url = f"{self.config.base_url}/rag/v3/chat?question={urllib.request.quote(question)}"
        req = urllib.request.Request(url, headers={
            "Authorization": self._token,
        })

        answer_parts = []
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                for line in resp.read().decode("utf-8").split("\n"):
                    if line.startswith("data:"):
                        try:
                            d = json.loads(line[5:].strip())
                            if "delta" in d:
                                answer_parts.append(d["delta"])
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            logger.error(f"RAG chat error: {e}")
            raise

        return "".join(answer_parts)

    def get_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """获取文档的分块列表"""
        self.ensure_logged_in()
        resp = self._request("GET", f"/knowledge-base/docs/{doc_id}/chunks")
        return resp.get("data", [])
