"""
Skill MCP Tools - 项目技能管理工具

支持：
- upload_skill: 上传技能到项目技能库
- search_skill: 按任务描述搜索技能
- list_skills: 列出项目所有技能
- get_skill: 获取指定技能详情
"""

import logging
import os
import json
import tempfile
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SkillMetadata:
    """技能元数据"""
    name: str
    category: str  # coding, testing, deployment, architecture, etc.
    tags: List[str] = field(default_factory=list)
    description: str = ""
    project: str = ""
    version: str = "1.0"
    author: str = ""


@dataclass
class Skill:
    """技能定义"""
    metadata: SkillMetadata
    content: str
    file_path: str = ""


class SkillStore:
    """技能存储管理器"""

    def __init__(self, base_dir: str = "skills",
                 rag_url: str = "http://localhost:9090/api/ragent",
                 username: str = "admin",
                 password: str = "admin"):
        self.base_dir = Path(base_dir)
        self.rag_url = rag_url
        self.username = username
        self.password = password
        self._token: Optional[str] = None
        self._kb_cache: Dict[str, str] = {}  # project -> kb_id

        # 确保本地目录存在
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _request(self, method: str, path: str, data: Optional[dict] = None) -> dict:
        """发送 HTTP 请求"""
        url = f"{self.rag_url}{path}"
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
        url = f"{self.rag_url}{path}"
        boundary = "----SkillUpload"

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
            "username": self.username,
            "password": self.password,
        })
        self._token = resp["data"]["token"]
        return self._token

    def ensure_logged_in(self):
        """确保已登录"""
        if not self._token:
            self.login()

    def get_or_create_skill_kb(self, project: str) -> str:
        """获取或创建项目的技能知识库"""
        self.ensure_logged_in()

        if project in self._kb_cache:
            return self._kb_cache[project]

        # 查询现有知识库
        resp = self._request("GET", "/knowledge-base")
        kb_page = resp.get("data") or {}
        kb_list = kb_page.get("records", []) if isinstance(kb_page, dict) else []

        for kb in kb_list:
            if kb.get("name") == f"skills_{project}":
                self._kb_cache[project] = str(kb["id"])
                return str(kb["id"])

        # 创建新知识库
        resp = self._request("POST", "/knowledge-base", {
            "name": f"skills_{project}",
            "embeddingModel": "qwen-emb-8b",
            "collectionName": f"skills_{project}_col",
        })
        kb_id = str(resp["data"])
        self._kb_cache[project] = kb_id
        logger.info(f"Created skill KB for project '{project}': {kb_id}")
        return kb_id

    def _get_skill_dir(self, project: str, category: str) -> Path:
        """获取技能本地目录"""
        skill_dir = self.base_dir / project / category
        skill_dir.mkdir(parents=True, exist_ok=True)
        return skill_dir

    def _build_skill_content(self, skill: Skill) -> str:
        """构建技能文件内容（包含元数据）"""
        lines = [
            f"# {skill.metadata.name}",
            "",
            f"## Description",
            skill.metadata.description,
            "",
            f"## Metadata",
            f"- **Category**: {skill.metadata.category}",
            f"- **Tags**: {', '.join(skill.metadata.tags)}",
            f"- **Version**: {skill.metadata.version}",
            f"- **Author**: {skill.metadata.author}",
            "",
            f"## Content",
            "",
            skill.content,
        ]
        return "\n".join(lines)

    def _parse_skill_content(self, content: str, file_path: str) -> Skill:
        """解析技能文件内容"""
        lines = content.split("\n")

        # 提取标题
        name = ""
        for line in lines:
            if line.startswith("# "):
                name = line[2:].strip()
                break

        # 提取元数据
        category = ""
        tags = []
        description = ""
        version = "1.0"
        author = ""
        in_metadata = False
        in_content = False
        content_lines = []

        for line in lines:
            if line.startswith("## Description"):
                in_metadata = False
                continue
            elif line.startswith("## Metadata"):
                in_metadata = True
                continue
            elif line.startswith("## Content"):
                in_content = True
                in_metadata = False
                continue

            if in_metadata:
                if line.startswith("- **Category**:"):
                    category = line.split(":", 1)[1].strip()
                elif line.startswith("- **Tags**:"):
                    tags = [t.strip() for t in line.split(":", 1)[1].split(",")]
                elif line.startswith("- **Version**:"):
                    version = line.split(":", 1)[1].strip()
                elif line.startswith("- **Author**:"):
                    author = line.split(":", 1)[1].strip()
            elif in_content:
                content_lines.append(line)
            elif not name and not in_metadata:
                # 描述在标题之后、元数据之前
                if line.strip() and not line.startswith("#"):
                    description += line.strip() + " "

        return Skill(
            metadata=SkillMetadata(
                name=name or os.path.basename(file_path),
                category=category or "general",
                tags=tags,
                description=description.strip(),
                version=version,
                author=author,
            ),
            content="\n".join(content_lines).strip(),
            file_path=file_path,
        )

    def upload_skill(self, project: str, skill_name: str, content: str,
                     category: str = "general", tags: List[str] = None,
                     description: str = "", author: str = "") -> Dict[str, Any]:
        """上传技能到项目技能库

        Args:
            project: 项目名称
            skill_name: 技能名称
            content: 技能内容
            category: 分类（coding, testing, deployment, architecture 等）
            tags: 标签列表
            description: 技能描述
            author: 作者
        """
        self.ensure_logged_in()

        # 构建技能对象
        skill = Skill(
            metadata=SkillMetadata(
                name=skill_name,
                category=category,
                tags=tags or [],
                description=description,
                project=project,
                author=author,
            ),
            content=content,
        )

        # 保存到本地
        skill_dir = self._get_skill_dir(project, category)
        safe_name = skill_name.replace(" ", "_").replace("/", "_")
        file_path = skill_dir / f"{safe_name}.md"
        file_content = self._build_skill_content(skill)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        # 上传到 RAG
        kb_id = self.get_or_create_skill_kb(project)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(file_content)
            temp_path = f.name

        try:
            resp = self._upload_file(
                f"/knowledge-base/{kb_id}/docs/upload",
                temp_path,
                extra_fields={"sourceType": "file", "processMode": "chunk"},
            )

            doc_id = resp.get("data", {}).get("id")
            if doc_id:
                # 触发分块
                self._request("POST", f"/knowledge-base/docs/{doc_id}/chunk")

                return {
                    "status": "success",
                    "project": project,
                    "skill_name": skill_name,
                    "category": category,
                    "kb_id": kb_id,
                    "doc_id": doc_id,
                    "local_path": str(file_path),
                }
            else:
                return {"status": "error", "error": "No doc_id in response"}

        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            os.unlink(temp_path)

    def search_skill(self, project: str, task_description: str,
                     top_k: int = 3, category: str = None) -> Dict[str, Any]:
        """搜索技能

        Args:
            project: 项目名称
            task_description: 任务描述（用于语义匹配）
            top_k: 返回数量
            category: 限定分类（可选）
        """
        self.ensure_logged_in()

        kb_id = self.get_or_create_skill_kb(project)

        # 构建搜索查询
        query = task_description
        if category:
            query = f"{category} {query}"

        # 相似检索
        resp = self._request("POST", "/knowledge-base/search/similar", {
            "query": query,
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

        return {
            "project": project,
            "task": task_description,
            "results": results,
            "count": len(results),
        }

    def list_skills(self, project: str) -> Dict[str, Any]:
        """列出项目所有技能（从本地目录）"""
        project_dir = self.base_dir / project
        if not project_dir.exists():
            return {"project": project, "skills": [], "count": 0}

        skills = []
        for category_dir in project_dir.iterdir():
            if category_dir.is_dir():
                for skill_file in category_dir.glob("*.md"):
                    try:
                        with open(skill_file, "r", encoding="utf-8") as f:
                            content = f.read()
                        skill = self._parse_skill_content(content, str(skill_file))
                        skills.append({
                            "name": skill.metadata.name,
                            "category": skill.metadata.category,
                            "tags": skill.metadata.tags,
                            "description": skill.metadata.description,
                            "file_path": str(skill_file),
                        })
                    except Exception as e:
                        logger.warning(f"Failed to parse {skill_file}: {e}")

        return {
            "project": project,
            "skills": skills,
            "count": len(skills),
        }

    def get_skill(self, project: str, skill_name: str,
                  category: str = None) -> Optional[Dict[str, Any]]:
        """获取指定技能详情"""
        project_dir = self.base_dir / project

        # 搜索所有分类
        categories = [category] if category else [
            d.name for d in project_dir.iterdir() if d.is_dir()
        ] if project_dir.exists() else []

        for cat in categories:
            safe_name = skill_name.replace(" ", "_").replace("/", "_")
            skill_file = project_dir / cat / f"{safe_name}.md"

            if skill_file.exists():
                with open(skill_file, "r", encoding="utf-8") as f:
                    content = f.read()
                skill = self._parse_skill_content(content, str(skill_file))
                return {
                    "name": skill.metadata.name,
                    "category": skill.metadata.category,
                    "tags": skill.metadata.tags,
                    "description": skill.metadata.description,
                    "content": skill.content,
                    "file_path": str(skill_file),
                }

        return None

    def delete_skill(self, project: str, skill_name: str,
                     category: str = None) -> Dict[str, Any]:
        """删除技能"""
        self.ensure_logged_in()

        project_dir = self.base_dir / project
        if not project_dir.exists():
            return {"status": "error", "error": "项目不存在"}

        # 搜索所有分类
        categories = [category] if category else [
            d.name for d in project_dir.iterdir() if d.is_dir()
        ]

        deleted_files = []
        for cat in categories:
            safe_name = skill_name.replace(" ", "_").replace("/", "_")
            skill_file = project_dir / cat / f"{safe_name}.md"

            if skill_file.exists():
                # 删除本地文件
                skill_file.unlink()
                deleted_files.append(str(skill_file))

                # 删除向量库中的对应向量
                try:
                    kb_id = self.get_or_create_skill_kb(project)
                    # 搜索并删除包含该技能名的向量
                    search_resp = self._request("POST", "/knowledge-base/search/similar", {
                        "query": skill_name,
                        "kbId": kb_id,
                        "topK": 100,
                    })
                    for chunk in search_resp.get("data", []):
                        if skill_name.lower() in chunk.get("content", "").lower():
                            self._request("DELETE", f"/knowledge-base/chunks/{chunk.get('chunkId')}")
                except Exception as e:
                    logger.warning(f"Failed to delete vectors: {e}")

        if deleted_files:
            return {
                "status": "success",
                "project": project,
                "skill_name": skill_name,
                "deleted_files": deleted_files,
            }
        else:
            return {"status": "error", "error": "技能不存在"}


# 全局存储实例
_store: Optional[SkillStore] = None


def get_store() -> SkillStore:
    """获取全局存储"""
    global _store
    if _store is None:
        _store = SkillStore()
    return _store


def set_store(store: SkillStore):
    """设置全局存储（用于测试）"""
    global _store
    _store = store


# MCP Tool 实现

def upload_skill_impl(project: str, skill_name: str, content: str,
                      category: str = "general", tags: List[str] = None,
                      description: str = "", author: str = "") -> Dict[str, Any]:
    """上传技能到项目技能库"""
    store = get_store()
    return store.upload_skill(project, skill_name, content, category, tags, description, author)


def search_skill_impl(project: str, task_description: str,
                      top_k: int = 3, category: str = None) -> Dict[str, Any]:
    """搜索技能"""
    store = get_store()
    return store.search_skill(project, task_description, top_k, category)


def list_skills_impl(project: str) -> Dict[str, Any]:
    """列出项目所有技能"""
    store = get_store()
    return store.list_skills(project)


def get_skill_impl(project: str, skill_name: str, category: str = None) -> Optional[Dict[str, Any]]:
    """获取指定技能详情"""
    store = get_store()
    return store.get_skill(project, skill_name, category)


def delete_skill_impl(project: str, skill_name: str, category: str = None) -> Dict[str, Any]:
    """删除技能"""
    store = get_store()
    return store.delete_skill(project, skill_name, category)


# MCP Tool 元数据

UPLOAD_SKILL_TOOL = {
    "name": "upload_skill",
    "description": "上传技能到项目技能库。技能是可复用的操作指南、代码片段、最佳实践等。",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {"type": "string", "description": "项目名称"},
            "skill_name": {"type": "string", "description": "技能名称"},
            "content": {"type": "string", "description": "技能内容（Markdown 格式）"},
            "category": {"type": "string", "description": "分类：coding, testing, deployment, architecture 等"},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "标签列表"},
            "description": {"type": "string", "description": "技能描述"},
            "author": {"type": "string", "description": "作者"},
        },
        "required": ["project", "skill_name", "content"],
    },
}

SEARCH_SKILL_TOOL = {
    "name": "search_skill",
    "description": "搜索技能。根据任务描述查找最相关的技能。",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {"type": "string", "description": "项目名称"},
            "task_description": {"type": "string", "description": "任务描述，如 '如何配置数据库连接'"},
            "top_k": {"type": "integer", "description": "返回数量，默认 3"},
            "category": {"type": "string", "description": "限定分类（可选）"},
        },
        "required": ["project", "task_description"],
    },
}

LIST_SKILLS_TOOL = {
    "name": "list_skills",
    "description": "列出项目所有技能",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {"type": "string", "description": "项目名称"},
        },
        "required": ["project"],
    },
}

GET_SKILL_TOOL = {
    "name": "get_skill",
    "description": "获取指定技能详情",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {"type": "string", "description": "项目名称"},
            "skill_name": {"type": "string", "description": "技能名称"},
            "category": {"type": "string", "description": "分类（可选）"},
        },
        "required": ["project", "skill_name"],
    },
}

DELETE_SKILL_TOOL = {
    "name": "delete_skill",
    "description": "删除技能（同时删除本地文件和向量）",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project": {"type": "string", "description": "项目名称"},
            "skill_name": {"type": "string", "description": "技能名称"},
            "category": {"type": "string", "description": "分类（可选）"},
        },
        "required": ["project", "skill_name"],
    },
}


def register_skill_tools(gateway_mcp):
    """向 FastMCP 注册技能管理工具"""
    from mcp import types

    async def upload_skill(ctx, project: str, skill_name: str, content: str,
                          category: str = "general", tags: List[str] = None,
                          description: str = "", author: str = ""):
        """上传技能"""
        result = upload_skill_impl(project, skill_name, content, category, tags, description, author)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def search_skill(ctx, project: str, task_description: str,
                          top_k: int = 3, category: str = None):
        """搜索技能"""
        result = search_skill_impl(project, task_description, top_k, category)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def list_skills(ctx, project: str):
        """列出技能"""
        result = list_skills_impl(project)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    async def get_skill(ctx, project: str, skill_name: str, category: str = None):
        """获取技能"""
        result = get_skill_impl(project, skill_name, category)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result or {}, ensure_ascii=False))]
        )

    async def delete_skill(ctx, project: str, skill_name: str, category: str = None):
        """删除技能"""
        result = delete_skill_impl(project, skill_name, category)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        )

    # 设置元数据
    upload_skill.__name__ = "upload_skill"
    upload_skill.__doc__ = UPLOAD_SKILL_TOOL["description"]

    search_skill.__name__ = "search_skill"
    search_skill.__doc__ = SEARCH_SKILL_TOOL["description"]

    list_skills.__name__ = "list_skills"
    list_skills.__doc__ = LIST_SKILLS_TOOL["description"]

    get_skill.__name__ = "get_skill"
    get_skill.__doc__ = GET_SKILL_TOOL["description"]

    delete_skill.__name__ = "delete_skill"
    delete_skill.__doc__ = DELETE_SKILL_TOOL["description"]

    # 注册工具
    gateway_mcp.tool(name="upload_skill", description=UPLOAD_SKILL_TOOL["description"])(upload_skill)
    gateway_mcp.tool(name="search_skill", description=SEARCH_SKILL_TOOL["description"])(search_skill)
    gateway_mcp.tool(name="list_skills", description=LIST_SKILLS_TOOL["description"])(list_skills)
    gateway_mcp.tool(name="get_skill", description=GET_SKILL_TOOL["description"])(get_skill)
    gateway_mcp.tool(name="delete_skill", description=DELETE_SKILL_TOOL["description"])(delete_skill)

    logger.info("Registered skill tools: upload_skill, search_skill, list_skills, get_skill, delete_skill")
