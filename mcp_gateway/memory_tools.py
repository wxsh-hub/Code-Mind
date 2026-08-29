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
        """发送 HTTP 请求"""
        url = f"{self.config.base_url}{path}"
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        if self._token:
            headers["Authorization"] = self._token

        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            logger.error(f"HTTP {e.code}: {body_text}")
            raise RuntimeError(f"HTTP {e.code}: {body_text}")

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
        """获取或创建项目的知识库"""
        self.ensure_logged_in()

        # 检查缓存
        if project_name in self._project_cache:
            return self._project_cache[project_name]

        # 查询现有知识库
        resp = self._request("GET", "/knowledge-base/list")
        kb_list = resp.get("data") or []

        for kb in kb_list:
            if kb.get("name") == f"memory_{project_name}":
                self._project_cache[project_name] = str(kb["id"])
                return str(kb["id"])

        # 创建新知识库
        resp = self._request("POST", "/knowledge-base", {
            "name": f"memory_{project_name}",
            "embeddingModel": "qwen-emb-8b",
            "collectionName": f"memory_{project_name}_col",
        })
        kb_id = str(resp["data"])
        self._project_cache[project_name] = kb_id
        logger.info(f"Created knowledge base for project '{project_name}': {kb_id}")
        return kb_id

    def upload_memory(self, project_name: str, filename: str, content: str,
                      calculate_confidence: bool = True) -> Dict[str, Any]:
        """上传记忆文件到项目知识库

        Args:
            project_name: 项目名称
            filename: 文件名
            content: 文件内容
            calculate_confidence: 是否计算置信度（默认 True）
        """
        self.ensure_logged_in()

        # 获取或创建项目知识库
        kb_id = self.get_or_create_project_kb(project_name)

        # 写入临时文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(content)
            temp_path = f.name

        try:
            # 上传文档
            resp = self._upload_file(
                f"/knowledge-base/{kb_id}/docs/upload",
                temp_path,
                extra_fields={"sourceType": "file", "processMode": "chunk"},
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
                }
            else:
                return {"status": "error", "error": "No doc_id in response"}

        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            os.unlink(temp_path)

    def ask_project(self, project_name: str, question: str, top_k: int = 5,
                    normalize: bool = True) -> Dict[str, Any]:
        """向项目知识库提问

        Args:
            project_name: 项目名称
            question: 问题
            top_k: 返回数量
            normalize: 是否归一化置信度到100 分（默认 True）
        """
        self.ensure_logged_in()

        # 获取项目知识库
        kb_id = self.get_or_create_project_kb(project_name)

        # 相似检索
        resp = self._request("POST", "/knowledge-base/search/similar", {
            "query": question,
            "kbId": kb_id,
            "topK": top_k,
        })

        results = resp.get("data", [])

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
                "metadata": item.get("metadata", {}),
                "confidence": conf.get("confidence", 1),
                "normalizedScore": conf.get("normalizedScore", 0),
            })

        return {
            "project": project_name,
            "question": question,
            "results": enriched_results,
            "count": len(enriched_results),
            "totalConfidence": sum(r.get("confidence", 1) for r in enriched_results),
        }

    def list_projects(self) -> List[Dict[str, Any]]:
        """列出所有项目"""
        self.ensure_logged_in()

        resp = self._request("GET", "/knowledge-base/list")
        kb_list = resp.get("data") or []

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

def upload_memory_impl(project: str, filename: str, content: str) -> Dict[str, Any]:
    """上传记忆文件到项目知识库

    Args:
        project: 项目名称，如 "Code-Mind"、"MyApp"
        filename: 文件名，如 "MEMORY.md"、"rag-status.md"
        content: 文件内容

    Returns:
        上传结果
    """
    manager = get_manager()
    return manager.upload_memory(project, filename, content)


def ask_project_impl(project: str, question: str, top_k: int = 5) -> Dict[str, Any]:
    """向项目知识库提问

    Args:
        project: 项目名称，如 "Code-Mind"
        question: 问题内容，如 "RAG 模块的完成度是多少？"
        top_k: 返回结果数量

    Returns:
        包含答案的结果
    """
    manager = get_manager()
    return manager.ask_project(project, question, top_k)


def list_projects_impl() -> Dict[str, Any]:
    """列出所有项目

    Returns:
        项目列表
    """
    manager = get_manager()
    projects = manager.list_projects()
    return {"projects": projects, "count": len(projects)}


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
        },
        "required": ["project", "filename", "content"],
    },
}

ASK_PROJECT_TOOL = {
    "name": "ask_project",
    "description": "向项目知识库提问。根据项目名检索对应的知识库，返回相关的记忆内容。用于查询项目状态、规范、经验等。",
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


def register_memory_tools(gateway_mcp):
    """向 FastMCP 注册记忆管理工具"""
    from mcp import types

    async def upload_memory(ctx, project: str, filename: str, content: str):
        """上传记忆文件"""
        result = upload_memory_impl(project, filename, content)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def ask_project(ctx, project: str, question: str, top_k: int = 5):
        """项目问答"""
        result = ask_project_impl(project, question, top_k)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def list_projects(ctx):
        """列出项目"""
        result = list_projects_impl()
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

    # 注册工具
    gateway_mcp.tool(name="upload_memory", description=UPLOAD_MEMORY_TOOL["description"])(upload_memory)
    gateway_mcp.tool(name="ask_project", description=ASK_PROJECT_TOOL["description"])(ask_project)
    gateway_mcp.tool(name="list_projects", description=LIST_PROJECTS_TOOL["description"])(list_projects)

    logger.info("Registered memory tools: upload_memory, ask_project, list_projects")
