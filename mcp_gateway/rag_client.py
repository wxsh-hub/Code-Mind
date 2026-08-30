"""
RAG HTTP Client - 用于与 ragent 服务通信

提供知识库检索、chunk 管理等 HTTP 接口调用
"""

import logging
import urllib.request
import urllib.error
import json
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 错误码映射
ERROR_CODE_MAP = {
    "A000001": "用户端错误",
    "A000100": "用户注册错误",
    "A000110": "用户名校验失败",
    "A000111": "用户名已存在",
    "A000120": "密码校验失败",
    "A000200": "幂等Token为空",
    "A000201": "幂等Token已被使用或失效",
    "A000300": "查询数据量超过最大限制",
    "B000001": "系统执行出错",
    "B000100": "系统执行超时",
    "C000001": "调用第三方服务出错",
}


def get_friendly_error_message(error_code: str, default_message: str) -> str:
    """获取友好的错误信息"""
    friendly_msg = ERROR_CODE_MAP.get(error_code)
    if friendly_msg:
        return f"{friendly_msg}: {default_message}" if default_message else friendly_msg
    return default_message or "未知错误"


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed: {e}")
            raise last_exception
        return wrapper
    return decorator


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

    @retry_on_failure(max_attempts=3, delay=1.0)
    def _request(self, method: str, path: str, data: Optional[dict] = None,
                 headers: Optional[dict] = None) -> dict:
        """发送 HTTP 请求（带重试）"""
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
                result = json.loads(resp.read().decode("utf-8"))
                # 检查业务错误码
                if result.get("code") and result.get("code") != "0":
                    error_code = result.get("code")
                    error_msg = result.get("message", "")
                    friendly_msg = get_friendly_error_message(error_code, error_msg)
                    logger.warning(f"Business error from {path}: [{error_code}] {friendly_msg}")
                return result
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            logger.error(f"HTTP {e.code} from {url}: {body}")
            try:
                error_json = json.loads(body)
                error_code = error_json.get("code", "")
                error_msg = error_json.get("message", body)
                friendly_msg = get_friendly_error_message(error_code, error_msg)
                raise RuntimeError(friendly_msg)
            except json.JSONDecodeError:
                raise RuntimeError(f"HTTP {e.code}: {body}")
        except urllib.error.URLError as e:
            logger.error(f"Connection error to {url}: {e}")
            raise RuntimeError(f"网络连接异常: {e}")

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
        """标记单个 chunk 为废弃"""
        self.ensure_logged_in()
        self._request("POST", f"/knowledge-base/chunks/{chunk_id}/deprecate")

    def batch_deprecate_chunks(self, chunk_ids: List[str]) -> Dict[str, Any]:
        """批量标记 chunks 为废弃

        Args:
            chunk_ids: chunk ID 列表

        Returns:
            {"success": int, "failed": int, "errors": [...]}
        """
        self.ensure_logged_in()
        success = 0
        failed = 0
        errors = []

        for chunk_id in chunk_ids:
            try:
                self.deprecate_chunk(chunk_id)
                success += 1
            except Exception as e:
                failed += 1
                errors.append({"chunk_id": chunk_id, "error": str(e)})

        return {"success": success, "failed": failed, "errors": errors}

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

    def rag_chat_with_sources(self, question: str, max_tokens: int = 2000) -> Dict[str, Any]:
        """RAG 问答（返回 AI 回答 + 引用来源）"""
        self.ensure_logged_in()
        url = f"{self.config.base_url}/rag/v3/chat?question={urllib.request.quote(question)}"
        req = urllib.request.Request(url, headers={
            "Authorization": self._token,
        })

        answer_parts = []
        sources = []
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                for line in resp.read().decode("utf-8").split("\n"):
                    if line.startswith("data:"):
                        try:
                            d = json.loads(line[5:].strip())
                            if "delta" in d:
                                answer_parts.append(d["delta"])
                            if "sources" in d:
                                sources = d["sources"]
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            logger.error(f"RAG chat error: {e}")
            raise

        return {
            "answer": "".join(answer_parts),
            "sources": sources,
        }

    def get_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """获取文档的分块列表"""
        self.ensure_logged_in()
        resp = self._request("GET", f"/knowledge-base/docs/{doc_id}/chunks")
        return resp.get("data", [])

    # ========== 模块管理 ==========

    def create_module(self, name: str, description: str = "") -> Dict[str, Any]:
        """创建模块"""
        self.ensure_logged_in()
        resp = self._request("POST", "/modules", {
            "name": name,
            "description": description,
        })
        return resp.get("data", {})

    def list_modules(self) -> List[Dict[str, Any]]:
        """列出所有模块"""
        self.ensure_logged_in()
        resp = self._request("GET", "/modules")
        return resp.get("data", [])

    def get_module(self, name: str) -> Optional[Dict[str, Any]]:
        """获取模块详情"""
        self.ensure_logged_in()
        try:
            resp = self._request("GET", f"/modules/{name}")
            return resp.get("data")
        except RuntimeError:
            return None

    def delete_module(self, name: str) -> Dict[str, Any]:
        """删除模块（级联删除功能和向量）"""
        self.ensure_logged_in()
        resp = self._request("DELETE", f"/modules/{name}")
        return resp.get("data", {})

    # ========== 功能管理 ==========

    def create_feature(self, code: str, name: str, module_name: str,
                       description: str = "") -> Dict[str, Any]:
        """创建功能"""
        self.ensure_logged_in()
        resp = self._request("POST", "/feature-metadata", {
            "featureCode": code,
            "featureName": name,
            "moduleName": module_name,
            "description": description,
        })
        return resp.get("data", {})

    def list_features(self, module_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出功能"""
        self.ensure_logged_in()
        path = "/feature-metadata"
        if module_name:
            path += f"?module={module_name}"
        resp = self._request("GET", path)
        return resp.get("data", [])

    def get_feature(self, code: str) -> Optional[Dict[str, Any]]:
        """获取功能详情"""
        self.ensure_logged_in()
        try:
            resp = self._request("GET", f"/feature-metadata/{code}")
            return resp.get("data")
        except RuntimeError:
            return None

    def delete_feature(self, code: str) -> Dict[str, Any]:
        """删除功能（级联删除向量）"""
        self.ensure_logged_in()
        resp = self._request("DELETE", f"/feature-metadata/{code}")
        return resp.get("data", {})

    def search_features(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索功能元数据（模糊匹配功能名称和描述）"""
        self.ensure_logged_in()
        # 使用 URL 编码处理中文
        import urllib.parse
        import re

        # 分词：按空格、标点等分隔符分割
        keywords = re.split(r'[\s,.!?;:，。！？；：]+', keyword)

        # 取第一个关键词进行搜索（避免太长的查询）
        search_keyword = keywords[0] if keywords else keyword

        # 如果关键词太长（超过6个字符），截取前6个字符
        if len(search_keyword) > 6:
            search_keyword = search_keyword[:6]

        encoded_keyword = urllib.parse.quote(search_keyword)
        resp = self._request("GET", f"/feature-metadata/search?keyword={encoded_keyword}&limit={limit}")
        return resp.get("data", [])

    # ========== 带元数据的检索 ==========

    def search_with_metadata(self, query: str, kb_id: Optional[str] = None,
                              feature_codes: Optional[List[str]] = None,
                              module: Optional[str] = None,
                              top_k: int = 10) -> Dict[str, Any]:
        """带元数据的检索（支持逐级降级）"""
        self.ensure_logged_in()
        body: Dict[str, Any] = {"query": query, "topK": top_k}
        if kb_id:
            body["kbId"] = kb_id
        if feature_codes:
            body["featureCodes"] = ",".join(feature_codes)
        if module:
            body["module"] = module
        resp = self._request("POST", "/knowledge-base/search/similar", body)
        return resp

    # ========== 按元数据删除 ==========

    def delete_by_feature_code(self, code: str) -> Dict[str, Any]:
        """按功能编号删除向量"""
        self.ensure_logged_in()
        resp = self._request("DELETE", f"/knowledge-base/chunks/by-feature/{code}")
        return resp.get("data", {})

    def delete_by_module(self, module: str) -> Dict[str, Any]:
        """按模块删除向量"""
        self.ensure_logged_in()
        resp = self._request("DELETE", f"/knowledge-base/chunks/by-module/{module}")
        return resp.get("data", {})

    def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """删除文档及其所有向量"""
        self.ensure_logged_in()
        resp = self._request("DELETE", f"/knowledge-base/docs/{doc_id}")
        return resp.get("data", {})

    def delete_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """删除整个知识库"""
        self.ensure_logged_in()
        resp = self._request("DELETE", f"/knowledge-base/{kb_id}")
        return resp.get("data", {})
