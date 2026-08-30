"""
Memory MCP Tools - 项目记忆管理工具

支持：
- upload_memory: 上传项目记忆文件到独立向量库
- ask_project: 按项目名问答
- list_projects: 列出所有项目
"""

import logging
import urllib.request
import urllib.error
import json
import tempfile
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from mcp_gateway.path_resolver import extract_paths, find_matching_chunks, build_reference_metadata

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfig:
    """记忆管理配置"""
    base_url: str = "http://localhost:9090/api/ragent"
    username: str = "admin"
    password: str = "admin"


class MemoryManager:
    """项目记忆管理器"""

    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self._token: Optional[str] = None
        self._project_cache: Dict[str, str] = {}  # project_name -> kb_id

    def _request(self, method: str, path: str, data: Optional[dict] = None) -> dict:
        """发送 HTTP 请求（带重试）"""
        import time as _time
        # 直接使用路径，不进行额外编码（调用方已处理编码）
        url = f"{self.config.base_url}{path}"
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        if self._token:
            headers["Authorization"] = self._token

        body = json.dumps(data).encode("utf-8") if data else None

        last_error = None
        for attempt in range(3):
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    # 检查业务错误码
                    if result.get("code") and result.get("code") != "0":
                        error_msg = result.get("message", "")
                        if "数据访问" in error_msg or "系统执行" in error_msg:
                            if attempt < 2:
                                logger.warning(f"Business error on attempt {attempt+1}, retrying: {error_msg}")
                                _time.sleep(1)
                                continue
                    return result
            except urllib.error.HTTPError as e:
                body_text = e.read().decode("utf-8", errors="replace")
                logger.error(f"HTTP {e.code}: {body_text}")
                if attempt < 2:
                    _time.sleep(1)
                    continue
                raise RuntimeError(f"HTTP {e.code}: {body_text}")
            except Exception as e:
                last_error = e
                if attempt < 2:
                    logger.warning(f"Request failed on attempt {attempt+1}, retrying: {e}")
                    _time.sleep(1)
                    continue
                raise

        raise RuntimeError(f"Request failed after 3 attempts: {last_error}")

    def _upload_file(self, path: str, file_path: str,
                     extra_fields: Optional[Dict[str, str]] = None) -> dict:
        """上传文件"""
        url = f"{self.config.base_url}{path}"
        boundary = "----MemoryUpload"

        with open(file_path, "rb") as f:
            file_data = f.read()

        filename = os.path.basename(file_path)
        body_parts = [
            f"--{boundary}".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode(),
            b"Content-Type: application/octet-stream",
            b"",
            file_data,
        ]

        if extra_fields:
            for key, value in extra_fields.items():
                body_parts.extend([
                    f"--{boundary}".encode(),
                    f'Content-Disposition: form-data; name="{key}"'.encode(),
                    b"",
                    value.encode("utf-8"),
                ])

        body_parts.append(f"--{boundary}--".encode())
        body = b"\r\n".join(body_parts)

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        if self._token:
            headers["Authorization"] = self._token

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            logger.error(f"Upload error {e.code}: {body_text}")
            raise RuntimeError(f"Upload failed: {body_text}")

    def login(self) -> str:
        """登录"""
        resp = self._request("POST", "/auth/login", {
            "username": self.config.username,
            "password": self.config.password,
        })
        self._token = resp["data"]["token"]
        return self._token

    def ensure_logged_in(self):
        """确保已登录"""
        if not self._token:
            self.login()

    def get_or_create_project_kb(self, project_name: str) -> str:
        """获取或创建项目的知识库（支持模糊匹配）"""
        self.ensure_logged_in()

        # 检查缓存
        if project_name in self._project_cache:
            return self._project_cache[project_name]

        # 查询现有知识库
        resp = self._request("GET", "/knowledge-base")
        kb_page = resp.get("data") or {}
        kb_list = kb_page.get("records", []) if isinstance(kb_page, dict) else []

        # 精确匹配
        for kb in kb_list:
            if kb.get("name") == f"memory_{project_name}":
                self._project_cache[project_name] = str(kb["id"])
                return str(kb["id"])

        # 模糊匹配（不区分大小写，支持部分匹配）
        project_lower = project_name.lower()
        for kb in kb_list:
            kb_name = kb.get("name", "").lower()
            if kb_name.startswith("memory_") and project_lower in kb_name:
                logger.info(f"Fuzzy matched knowledge base: {kb.get('name')}")
                self._project_cache[project_name] = str(kb["id"])
                return str(kb["id"])

        # 创建新知识库
        resp = self._request("POST", "/knowledge-base", {
            "name": f"memory_{project_name}",
            "embeddingModel": "qwen-emb-8b",
            "collectionName": f"memory_{project_name}_col",
        })
        kb_id = resp.get("data")
        if not kb_id:
            # 可能是知识库已存在，重新查询
            logger.info(f"Knowledge base creation returned null, fetching from list")
            resp = self._request("GET", "/knowledge-base")
            kb_page = resp.get("data") or {}
            kb_list = kb_page.get("records", []) if isinstance(kb_page, dict) else []
            for kb in kb_list:
                if kb.get("name") == f"memory_{project_name}":
                    self._project_cache[project_name] = str(kb["id"])
                    return str(kb["id"])
            # 如果仍然找不到，返回第一个匹配的知识库 ID
            if kb_list:
                logger.warning(f"Using first knowledge base as fallback: {kb_list[0].get('name')}")
                self._project_cache[project_name] = str(kb_list[0]["id"])
                return str(kb_list[0]["id"])
            raise RuntimeError(f"Failed to create knowledge base: {resp}")
        kb_id = str(kb_id)
        self._project_cache[project_name] = kb_id
        logger.info(f"Created knowledge base for project '{project_name}': {kb_id}")
        return kb_id

    def upload_memory(self, project_name: str, filename: str, content: str,
                      calculate_confidence: bool = True,
                      resolve_paths: bool = True,
                      feature_codes: Optional[List[str]] = None,
                      module: Optional[str] = None) -> Dict[str, Any]:
        """上传记忆文件到项目知识库

        Args:
            project_name: 项目名称
            filename: 文件名
            content: 文件内容
            calculate_confidence: 是否计算置信度（默认 True）
            resolve_paths: 是否解析路径引用（默认 True）
            feature_codes: 功能编号列表（可选）
            module: 模块名称（可选）
        """
        self.ensure_logged_in()

        # 获取或创建项目知识库
        kb_id = self.get_or_create_project_kb(project_name)

        # 解析路径引用
        path_refs = []
        if resolve_paths:
            try:
                paths = extract_paths(content)
                if paths:
                    # 获取已有文档列表
                    docs_resp = self._request("GET", f"/knowledge-base/{kb_id}/docs")
                    existing_docs = []
                    if isinstance(docs_resp.get("data"), dict):
                        for record in docs_resp["data"].get("records", []):
                            existing_docs.append({
                                "id": record.get("id"),
                                "name": record.get("docName", ""),
                            })
                    elif isinstance(docs_resp.get("data"), list):
                        existing_docs = docs_resp["data"]

                    # 查找匹配
                    path_refs = find_matching_chunks(paths, existing_docs)
                    if path_refs:
                        logger.info(f"Found {len(path_refs)} path references in {filename}")
            except Exception as e:
                logger.warning(f"Path resolution failed: {e}")

        # 写入临时文件（使用用户指定的文件名）
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, filename)
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)

        try:
            # 构建上传参数
            upload_fields = {"sourceType": "file", "processMode": "chunk"}
            if feature_codes:
                upload_fields["featureCodes"] = ",".join(feature_codes)
            if module:
                upload_fields["module"] = module

            # 上传文档
            resp = self._upload_file(
                f"/knowledge-base/{kb_id}/docs/upload",
                temp_path,
                extra_fields=upload_fields,
            )

            doc_id = resp.get("data", {}).get("id")
            if doc_id:
                # 触发分块
                self._request("POST", f"/knowledge-base/docs/{doc_id}/chunk")

                # 计算置信度（如果有分块）
                if calculate_confidence:
                    import time
                    time.sleep(5)  # 等待分块完成
                    # 获取分块列表并计算置信度
                    chunks_resp = self._request("GET", f"/knowledge-base/docs/{doc_id}/chunks")
                    chunks = chunks_resp.get("data", {})
                    records = chunks.get("records", []) if isinstance(chunks, dict) else []
                    for chunk in records:
                        chunk_id = chunk.get("id")
                        if chunk_id:
                            try:
                                self._request("POST", f"/knowledge-base/chunks/{chunk_id}/calculate-confidence")
                            except Exception:
                                pass

                return {
                    "status": "success",
                    "project": project_name,
                    "kb_id": kb_id,
                    "doc_id": doc_id,
                    "filename": filename,
                    "path_references": len(path_refs),
                }
            else:
                return {"status": "error", "error": "No doc_id in response"}

        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            # 清理临时目录
            try:
                os.unlink(temp_path)
                os.rmdir(temp_dir)
            except Exception:
                pass

    def ask_project(self, project_name: str, question: str, top_k: int = 5,
                    normalize: bool = True,
                    feature_codes: Optional[List[str]] = None,
                    module: Optional[str] = None) -> Dict[str, Any]:
        """向项目知识库提问（支持逐级降级检索）

        流程：
        1. 如果用户指定了 feature_codes 和 module，直接使用
        2. 如果未指定，先搜索功能元数据自动识别相关功能
        3. 用识别到的功能编号过滤搜索 chunk

        Args:
            project_name: 项目名称
            question: 问题
            top_k: 返回数量
            normalize: 是否归一化置信度到100 分（默认 True）
            feature_codes: 功能编号列表（优先级最高，可选）
            module: 模块名称（次优先级，可选）
        """
        self.ensure_logged_in()

        # 获取项目知识库
        kb_id = self.get_or_create_project_kb(project_name)

        # 自动识别功能：如果用户未指定，先搜索功能元数据
        auto_detected_features = []
        auto_detected_module = None

        if not feature_codes and not module:
            try:
                # 使用 RAGClient 的 search_features 方法
                from mcp_gateway.rag_client import RAGClient
                rag_client = RAGClient()
                rag_client._token = self._token  # 复用 token

                features = rag_client.search_features(question, limit=3)
                if features:
                    auto_detected_features = [f.get("featureCode") for f in features if f.get("featureCode")]
                    # 取第一个功能的模块作为模块过滤
                    if features[0].get("moduleName"):
                        auto_detected_module = features[0].get("moduleName")
                    logger.info(f"Auto-detected features: {auto_detected_features}, module: {auto_detected_module}")
            except Exception as e:
                logger.warning(f"Failed to auto-detect features: {e}")

        # 使用用户指定的或自动识别的参数
        effective_feature_codes = feature_codes or (auto_detected_features if auto_detected_features else None)
        effective_module = module or auto_detected_module

        # 逐级降级检索（混合模式：先 LIKE 后向量）
        level = "global"
        results = []

        # [1] 功能级检索（LIKE）
        if effective_feature_codes:
            resp = self._request("POST", "/knowledge-base/search/similar", {
                "query": question,
                "kbId": kb_id,
                "topK": top_k,
                "featureCodes": ",".join(effective_feature_codes),
            })
            results = resp.get("data") or []
            if results:
                level = "feature"
                logger.info(f"Feature-level LIKE search returned {len(results)} results")

        # [2] 模块级检索（LIKE）
        if not results and effective_module:
            resp = self._request("POST", "/knowledge-base/search/similar", {
                "query": question,
                "kbId": kb_id,
                "topK": top_k,
                "module": effective_module,
            })
            results = resp.get("data") or []
            if results:
                level = "module"
                logger.info(f"Module-level LIKE search returned {len(results)} results")

        # [3] 全库检索（LIKE）
        if not results:
            resp = self._request("POST", "/knowledge-base/search/similar", {
                "query": question,
                "kbId": kb_id,
                "topK": top_k,
            })
            results = resp.get("data") or []
            if results:
                level = "global"
                logger.info(f"Global LIKE search returned {len(results)} results")

        # [4] 向量检索（如果 LIKE 无结果）
        if not results:
            try:
                # 使用 rag_chat 进行向量检索
                from mcp_gateway.rag_client import RAGClient
                rag_client = RAGClient()
                rag_client._token = self._token

                # 构造带过滤条件的问题
                filter_question = question
                if effective_feature_codes:
                    filter_question += f" (功能: {','.join(effective_feature_codes)})"
                if effective_module:
                    filter_question += f" (模块: {effective_module})"

                # 调用向量检索（通过 rag_chat_with_sources）
                vector_result = rag_client.rag_chat_with_sources(filter_question)
                if vector_result and vector_result.get("answer"):
                    # 从 sources 中构造结果
                    sources = vector_result.get("sources", [])
                    for source in sources[:top_k]:
                        doc_id = source.get("docId")
                        if doc_id:
                            # 获取 chunk 信息
                            chunks = rag_client.get_chunks(doc_id)
                            if chunks:
                                records = chunks.get("records", []) if isinstance(chunks, dict) else chunks
                                for chunk in (records if isinstance(records, list) else []):
                                    chunk_id = chunk.get("id") if isinstance(chunk, dict) else None
                                    if chunk_id:
                                        results.append({
                                            "chunkId": chunk_id,
                                            "content": chunk.get("content", ""),
                                            "docId": doc_id,
                                            "kbId": kb_id,
                                            "score": 0.8,  # 向量检索默认分数
                                        })

                    if results:
                        level = "vector"
                        logger.info(f"Vector search returned {len(results)} results")
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")

        # 记录引用
        for item in results:
            chunk_id = item.get("chunkId")
            if chunk_id:
                try:
                    self._request("POST", f"/knowledge-base/chunks/{chunk_id}/reference")
                except Exception:
                    pass

        # 归一化置信度
        confidence_map = {}
        if normalize and results:
            chunk_ids = [r.get("chunkId") for r in results if r.get("chunkId")]
            if chunk_ids:
                try:
                    normalized = self._request("POST", "/knowledge-base/chunks/normalize-confidence", chunk_ids)
                    for item in normalized.get("data", []):
                        confidence_map[item.get("chunkId")] = {
                            "confidence": item.get("confidence", 1),
                            "normalizedScore": item.get("normalizedScore", 0),
                        }
                except Exception:
                    pass

        # 组装结果
        enriched_results = []
        for item in results:
            chunk_id = item.get("chunkId")
            conf = confidence_map.get(chunk_id, {})
            enriched_results.append({
                "chunkId": chunk_id,
                "content": item.get("content", ""),
                "docId": item.get("docId"),
                "kbId": item.get("kbId"),
                "score": item.get("score", 0),  # 相似度分数
                "metadata": item.get("metadata", {}),
                "confidence": conf.get("confidence", 1),
                "normalizedScore": conf.get("normalizedScore", 0),
                "upload_count": item.get("uploadCount", 1),
                "last_upload": item.get("lastUploadAt", ""),
                "days_old": item.get("daysOld", 0),
            })

        return {
            "project": project_name,
            "question": question,
            "results": enriched_results,
            "count": len(enriched_results),
            "level": level,
            "feature_codes": effective_feature_codes,
            "module": effective_module,
            "auto_detected": {
                "feature_codes": auto_detected_features if not feature_codes else [],
                "module": auto_detected_module if not module else None,
            },
        }

    def list_projects(self) -> List[Dict[str, Any]]:
        """列出所有项目"""
        self.ensure_logged_in()

        resp = self._request("GET", "/knowledge-base")
        kb_page = resp.get("data") or {}
        kb_list = kb_page.get("records", []) if isinstance(kb_page, dict) else []

        projects = []
        for kb in kb_list:
            name = kb.get("name", "")
            if name.startswith("memory_"):
                project_name = name[7:]  # 去掉 "memory_" 前缀
                projects.append({
                    "project": project_name,
                    "kb_id": str(kb["id"]),
                    "name": name,
                })

        return projects


# 全局管理器实例
_manager: Optional[MemoryManager] = None


def get_manager() -> MemoryManager:
    """获取全局管理器"""
    global _manager
    if _manager is None:
        _manager = MemoryManager()
    return _manager


def set_manager(manager: MemoryManager):
    """设置全局管理器（用于测试）"""
    global _manager
    _manager = manager


# MCP Tool 实现

def upload_memory_impl(project: str, filename: str, content: str,
                       feature_codes: Optional[List[str]] = None,
                       module: Optional[str] = None) -> Dict[str, Any]:
    """上传记忆文件到项目知识库

    Args:
        project: 项目名称，如 "Code-Mind"、"MyApp"
        filename: 文件名，如 "MEMORY.md"、"rag-status.md"
        content: 文件内容
        feature_codes: 功能编号列表（可选）
        module: 模块名称（可选）

    Returns:
        上传结果
    """
    manager = get_manager()
    return manager.upload_memory(project, filename, content,
                                 feature_codes=feature_codes, module=module)


def ask_project_impl(project: str, question: str, top_k: int = 5,
                     feature_codes: Optional[List[str]] = None,
                     module: Optional[str] = None) -> Dict[str, Any]:
    """向项目知识库提问（支持逐级降级检索）

    Args:
        project: 项目名称，如 "Code-Mind"
        question: 问题内容，如 "RAG 模块的完成度是多少？"
        top_k: 返回结果数量
        feature_codes: 功能编号列表（优先级最高）
        module: 模块名称（次优先级）

    Returns:
        包含答案的结果
    """
    manager = get_manager()
    return manager.ask_project(project, question, top_k,
                               feature_codes=feature_codes, module=module)


def list_projects_impl() -> Dict[str, Any]:
    """列出所有项目

    Returns:
        项目列表
    """
    manager = get_manager()
    projects = manager.list_projects()
    return {"projects": projects, "count": len(projects)}


def delete_memory_impl(project: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """删除记忆文件或整个项目

    Args:
        project: 项目名称
        filename: 文件名（为空时删除整个项目）

    Returns:
        删除结果
    """
    manager = get_manager()
    manager.ensure_logged_in()

    try:
        kb_id = manager.get_or_create_project_kb(project)

        if filename:
            # 按文件名删除
            # 查询该文件的文档
            docs_resp = manager._request("GET", f"/knowledge-base/{kb_id}/docs")
            docs = docs_resp.get("data", {})
            records = docs.get("records", []) if isinstance(docs, dict) else []

            deleted_count = 0
            for doc in records:
                if doc.get("docName") == filename:
                    doc_id = doc.get("id")
                    if doc_id:
                        manager._request("DELETE", f"/knowledge-base/docs/{doc_id}")
                        deleted_count += 1

            return {
                "status": "success",
                "project": project,
                "filename": filename,
                "deleted_docs": deleted_count,
            }
        else:
            # 删除整个知识库
            manager._request("DELETE", f"/knowledge-base/{kb_id}")
            return {
                "status": "success",
                "project": project,
                "deleted_kb": kb_id,
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def batch_upload_memories_impl(project: str, files: List[Dict[str, str]],
                                feature_codes: Optional[List[str]] = None,
                                module: Optional[str] = None) -> Dict[str, Any]:
    """批量上传记忆文件

    Args:
        project: 项目名称
        files: 文件列表，每项包含 {"filename": "...", "content": "..."}
        feature_codes: 功能编号列表（可选）
        module: 模块名称（可选）

    Returns:
        批量上传结果
    """
    manager = get_manager()
    results = []
    success_count = 0
    fail_count = 0

    for file_info in files:
        filename = file_info.get("filename", "")
        content = file_info.get("content", "")
        if not filename or not content:
            results.append({"filename": filename, "status": "error", "error": "Missing filename or content"})
            fail_count += 1
            continue

        try:
            result = manager.upload_memory(project, filename, content,
                                           feature_codes=feature_codes, module=module)
            results.append(result)
            if result.get("status") == "success":
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            results.append({"filename": filename, "status": "error", "error": str(e)})
            fail_count += 1

    return {
        "status": "completed",
        "project": project,
        "total": len(files),
        "success": success_count,
        "failed": fail_count,
        "results": results,
    }


def batch_delete_memories_impl(project: str, filenames: List[str]) -> Dict[str, Any]:
    """批量删除记忆文件

    Args:
        project: 项目名称
        filenames: 文件名列表

    Returns:
        批量删除结果
    """
    manager = get_manager()
    manager.ensure_logged_in()

    try:
        kb_id = manager.get_or_create_project_kb(project)

        # 查询所有文档
        docs_resp = manager._request("GET", f"/knowledge-base/{kb_id}/docs")
        docs = docs_resp.get("data", {})
        records = docs.get("records", []) if isinstance(docs, dict) else []

        # 按文件名匹配
        deleted_count = 0
        not_found = []
        for filename in filenames:
            found = False
            for doc in records:
                if doc.get("docName") == filename:
                    doc_id = doc.get("id")
                    if doc_id:
                        manager._request("DELETE", f"/knowledge-base/docs/{doc_id}")
                        deleted_count += 1
                        found = True
                        break
            if not found:
                not_found.append(filename)

        return {
            "status": "success",
            "project": project,
            "deleted": deleted_count,
            "not_found": not_found,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# MCP Tool 元数据

UPLOAD_MEMORY_TOOL = {
    "name": "upload_memory",
    "description": "上传项目记忆文件到独立向量库。每个项目有独立的知识库，用于存储项目规范、经验、状态等持久化记忆。",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {
                "type": "string",
                "description": "项目名称，如 'Code-Mind'、'MyApp'",
            },
            "filename": {
                "type": "string",
                "description": "文件名，如 'MEMORY.md'、'rag-status.md'",
            },
            "content": {
                "type": "string",
                "description": "文件内容（Markdown 格式）",
            },
            "feature_codes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "功能编号列表（可选），如 ['2437', '2438']",
            },
            "module": {
                "type": "string",
                "description": "模块名称（可选），如 'user'、'order'",
            },
        },
        "required": ["project", "filename", "content"],
    },
}

ASK_PROJECT_TOOL = {
    "name": "ask_project",
    "description": "向项目知识库提问。支持逐级降级检索：功能级→模块级→全库。",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {
                "type": "string",
                "description": "项目名称，如 'Code-Mind'",
            },
            "question": {
                "type": "string",
                "description": "问题内容，如 'RAG 模块的完成度是多少？'",
            },
            "top_k": {
                "type": "integer",
                "description": "返回结果数量，默认 5",
                "default": 5,
            },
            "feature_codes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "功能编号列表（优先级最高），如 ['2437']",
            },
            "module": {
                "type": "string",
                "description": "模块名称（次优先级），如 'user'",
            },
        },
        "required": ["project", "question"],
    },
}

LIST_PROJECTS_TOOL = {
    "name": "list_projects",
    "description": "列出所有已创建的项目知识库",
    "inputSchema": {
        "type": "object",
        "properties": {},
    },
}

DELETE_MEMORY_TOOL = {
    "name": "delete_memory",
    "description": "删除记忆文件或整个项目知识库",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {
                "type": "string",
                "description": "项目名称",
            },
            "filename": {
                "type": "string",
                "description": "文件名（为空时删除整个项目）",
            },
        },
        "required": ["project"],
    },
}

BATCH_UPLOAD_MEMORIES_TOOL = {
    "name": "batch_upload_memories",
    "description": "批量上传记忆文件到项目知识库",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {
                "type": "string",
                "description": "项目名称",
            },
            "files": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["filename", "content"],
                },
                "description": "文件列表",
            },
            "feature_codes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "功能编号列表（可选）",
            },
            "module": {
                "type": "string",
                "description": "模块名称（可选）",
            },
        },
        "required": ["project", "files"],
    },
}

BATCH_DELETE_MEMORIES_TOOL = {
    "name": "batch_delete_memories",
    "description": "批量删除记忆文件",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {
                "type": "string",
                "description": "项目名称",
            },
            "filenames": {
                "type": "array",
                "items": {"type": "string"},
                "description": "文件名列表",
            },
        },
        "required": ["project", "filenames"],
    },
}


def register_memory_tools(gateway_mcp):
    """向 FastMCP 注册记忆管理工具"""
    from mcp import types

    async def upload_memory(ctx, project: str, filename: str, content: str,
                           feature_codes: List[str] = None, module: str = None):
        """上传记忆文件"""
        result = upload_memory_impl(project, filename, content,
                                   feature_codes=feature_codes, module=module)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def ask_project(ctx, project: str, question: str, top_k: int = 5,
                         feature_codes: List[str] = None, module: str = None):
        """项目问答"""
        result = ask_project_impl(project, question, top_k,
                                 feature_codes=feature_codes, module=module)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def list_projects(ctx):
        """列出项目"""
        result = list_projects_impl()
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def delete_memory(ctx, project: str, filename: str = None):
        """删除记忆文件或整个项目"""
        result = delete_memory_impl(project, filename)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def batch_upload_memories(ctx, project: str, files: List[Dict[str, str]],
                                     feature_codes: List[str] = None, module: str = None):
        """批量上传记忆文件"""
        result = batch_upload_memories_impl(project, files,
                                            feature_codes=feature_codes, module=module)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def batch_delete_memories(ctx, project: str, filenames: List[str]):
        """批量删除记忆文件"""
        result = batch_delete_memories_impl(project, filenames)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    # 设置元数据
    upload_memory.__name__ = "upload_memory"
    upload_memory.__doc__ = UPLOAD_MEMORY_TOOL["description"]

    ask_project.__name__ = "ask_project"
    ask_project.__doc__ = ASK_PROJECT_TOOL["description"]

    list_projects.__name__ = "list_projects"
    list_projects.__doc__ = LIST_PROJECTS_TOOL["description"]

    delete_memory.__name__ = "delete_memory"
    delete_memory.__doc__ = DELETE_MEMORY_TOOL["description"]

    batch_upload_memories.__name__ = "batch_upload_memories"
    batch_upload_memories.__doc__ = BATCH_UPLOAD_MEMORIES_TOOL["description"]

    batch_delete_memories.__name__ = "batch_delete_memories"
    batch_delete_memories.__doc__ = BATCH_DELETE_MEMORIES_TOOL["description"]

    # 注册工具
    gateway_mcp.tool(name="upload_memory", description=UPLOAD_MEMORY_TOOL["description"])(upload_memory)
    gateway_mcp.tool(name="ask_project", description=ASK_PROJECT_TOOL["description"])(ask_project)
    gateway_mcp.tool(name="list_projects", description=LIST_PROJECTS_TOOL["description"])(list_projects)
    gateway_mcp.tool(name="delete_memory", description=DELETE_MEMORY_TOOL["description"])(delete_memory)
    gateway_mcp.tool(name="batch_upload_memories", description=BATCH_UPLOAD_MEMORIES_TOOL["description"])(batch_upload_memories)
    gateway_mcp.tool(name="batch_delete_memories", description=BATCH_DELETE_MEMORIES_TOOL["description"])(batch_delete_memories)

    logger.info("Registered memory tools: upload_memory, ask_project, list_projects, delete_memory, batch_upload_memories, batch_delete_memories")
