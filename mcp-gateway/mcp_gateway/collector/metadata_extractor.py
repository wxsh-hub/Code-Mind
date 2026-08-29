"""
Metadata Extractor - 元数据提取器

从 Markdown 文件中提取元数据（标题、标签、来源等）
"""

import re
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    """文档元数据"""
    title: str = ""
    source_type: str = "gitlab"
    source_ref: str = ""
    tags: List[str] = field(default_factory=list)
    category: str = ""
    author: str = ""
    created_at: str = ""
    project_id: str = ""
    file_path: str = ""
    branch: str = "main"


class MetadataExtractor:
    """元数据提取器"""

    # 标题提取模式
    TITLE_PATTERNS = [
        r"^#\s+(.+)$",  # H1 标题
        r"title:\s*(.+)$",  # YAML frontmatter
    ]

    # 标签提取模式
    TAG_PATTERNS = [
        r"tags?:\s*\[([^\]]+)\]",  # tags: [tag1, tag2]
        r"tags?:\s*(.+)$",  # tags: tag1, tag2
        r"标签:\s*(.+)$",  # 标签: xxx
    ]

    # 分类提取模式
    CATEGORY_PATTERNS = [
        r"category:\s*(.+)$",
        r"分类:\s*(.+)$",
        r"类型:\s*(.+)$",
    ]

    # 作者提取模式
    AUTHOR_PATTERNS = [
        r"author:\s*(.+)$",
        r"作者:\s*(.+)$",
        r"created[_\s]by:\s*(.+)$",
    ]

    def extract_from_content(self, content: str, file_path: str = "",
                              project_id: str = "", branch: str = "main") -> DocumentMetadata:
        """从文件内容提取元数据"""
        metadata = DocumentMetadata(
            source_type="gitlab",
            source_ref=file_path,
            project_id=project_id,
            file_path=file_path,
            branch=branch,
        )

        lines = content.split("\n")

        # 提取 YAML frontmatter
        frontmatter = self._extract_frontmatter(content)
        if frontmatter:
            metadata.title = frontmatter.get("title", "")
            metadata.tags = self._parse_tags(frontmatter.get("tags", ""))
            metadata.category = frontmatter.get("category", "")
            metadata.author = frontmatter.get("author", "")

        # 如果 frontmatter 没有提取到，从内容中提取
        for line in lines[:30]:  # 只看前 30 行
            if not metadata.title:
                metadata.title = self._extract_pattern(line, self.TITLE_PATTERNS)
            if not metadata.tags:
                tags_str = self._extract_pattern(line, self.TAG_PATTERNS)
                if tags_str:
                    metadata.tags = self._parse_tags(tags_str)
            if not metadata.category:
                metadata.category = self._extract_pattern(line, self.CATEGORY_PATTERNS)
            if not metadata.author:
                metadata.author = self._extract_pattern(line, self.AUTHOR_PATTERNS)

        # 如果还是没有标题，用文件名
        if not metadata.title and file_path:
            metadata.title = file_path.split("/")[-1].replace(".md", "")

        # 从路径推断分类
        if not metadata.category and file_path:
            metadata.category = self._infer_category(file_path)

        # 添加技术标签
        metadata.tags.extend(self._extract_tech_tags(content))
        metadata.tags = list(set(metadata.tags))  # 去重

        return metadata

    def _extract_frontmatter(self, content: str) -> Optional[Dict[str, str]]:
        """提取 YAML frontmatter"""
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return None

        result = {}
        for line in match.group(1).split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip().lower()] = value.strip()
        return result

    def _extract_pattern(self, line: str, patterns: List[str]) -> str:
        """从行中提取匹配模式的值"""
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _parse_tags(self, tags_str: str) -> List[str]:
        """解析标签字符串"""
        if not tags_str:
            return []
        # 移除方括号，按逗号分割
        cleaned = tags_str.strip("[]")
        return [t.strip().strip("'\"") for t in cleaned.split(",") if t.strip()]

    def _infer_category(self, file_path: str) -> str:
        """从文件路径推断分类"""
        path_lower = file_path.lower()
        if any(kw in path_lower for kw in ["规范", "standard", "convention"]):
            return "编码规范"
        if any(kw in path_lower for kw in ["架构", "architecture", "design"]):
            return "架构设计"
        if any(kw in path_lower for kw in ["经验", "experience", "lesson"]):
            return "项目经验"
        if any(kw in path_lower for kw in ["指南", "guide", "tutorial"]):
            return "技术指南"
        if any(kw in path_lower for kw in ["api", "接口"]):
            return "API文档"
        return "技术文档"

    def _extract_tech_tags(self, content: str) -> List[str]:
        """从内容中提取技术标签"""
        tech_keywords = {
            "Spring Boot": ["spring boot", "springboot"],
            "MyBatis": ["mybatis", "mybatis-plus"],
            "Redis": ["redis", "缓存"],
            "MySQL": ["mysql", "sql"],
            "Docker": ["docker", "容器"],
            "Kubernetes": ["kubernetes", "k8s"],
            "微服务": ["微服务", "microservice"],
            "RAG": ["rag", "检索增强"],
            "MCP": ["mcp", "model context protocol"],
            "向量数据库": ["向量", "vector", "pgvector", "embedding"],
            "Git": ["git", "gitlab", "github"],
            "Java": ["java", "spring"],
            "Python": ["python", "fastapi", "flask"],
            "TypeScript": ["typescript", "ts"],
        }

        content_lower = content.lower()
        tags = []
        for tag, keywords in tech_keywords.items():
            if any(kw in content_lower for kw in keywords):
                tags.append(tag)
        return tags
