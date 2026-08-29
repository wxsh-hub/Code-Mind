"""
Path Resolver - 轻量级路径引用解析

功能：
- 上传时扫描内容中的路径引用
- 在已有文档中查找匹配文件
- 存储引用关系到 metadata
"""

import re
import logging
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 路径匹配模式
PATH_PATTERNS = [
    # 绝对路径: /path/to/file.py
    r'(/[a-zA-Z0-9_/.-]+\.[a-zA-Z]{1,4})',
    # 相对路径: src/module/file.py 或 docs/memory/file.md
    r'([a-zA-Z0-9_]+(?:/[a-zA-Z0-9_-]+)+\.[a-zA-Z]{1,4})',
    # 代码引用: `path/to/file.py`
    r'`([a-zA-Z0-9_/.-]+\.[a-zA-Z]{1,4})`',
    # Markdown 链接: [text](path/to/file.md)
    r'\[.*?\]\(([^)]+\.[a-zA-Z]{1,4})\)',
]

# 忽略的路径（常见非文件路径）
IGNORE_PATHS = [
    'http://', 'https://', 'ftp://',  # URL
    'example.com', 'github.com',  # 域名
]


@dataclass
class PathReference:
    """路径引用"""
    source_path: str  # 引用来源（哪个文件提到了这个路径）
    target_path: str  # 被引用的路径
    chunk_id: Optional[str] = None  # 匹配到的 chunk ID


def extract_paths(content: str) -> Set[str]:
    """从内容中提取路径引用"""
    paths = set()

    for pattern in PATH_PATTERNS:
        matches = re.findall(pattern, content, re.MULTILINE)
        for match in matches:
            path = match.strip()
            # 过滤无效路径
            if path and not any(ignore in path for ignore in IGNORE_PATHS):
                # 标准化路径
                normalized = path.replace('\\', '/').strip('/')
                if normalized and '.' in normalized:  # 确保有扩展名
                    paths.add(normalized)

    return paths


def find_matching_chunks(paths: Set[str], existing_docs: List[Dict[str, Any]]) -> List[PathReference]:
    """在已有文档中查找匹配的路径

    Args:
        paths: 提取到的路径集合
        existing_docs: 已有文档列表 [{"id": "...", "name": "...", "content": "..."}]

    Returns:
        匹配到的引用列表
    """
    references = []

    for path in paths:
        # 提取文件名（不含路径）
        filename = path.split('/')[-1]

        for doc in existing_docs:
            doc_name = doc.get('name', '')
            doc_id = doc.get('id', '')

            # 精确匹配文件名
            if doc_name == filename or doc_name.endswith('/' + filename):
                references.append(PathReference(
                    source_path=path,
                    target_path=doc_name,
                    chunk_id=doc_id,
                ))
                break

            # 模糊匹配：路径的最后一部分
            if filename in doc_name or doc_name in filename:
                references.append(PathReference(
                    source_path=path,
                    target_path=doc_name,
                    chunk_id=doc_id,
                ))
                break

    return references


def build_reference_metadata(references: List[PathReference]) -> Dict[str, Any]:
    """构建引用元数据（用于存储到 chunk metadata）"""
    if not references:
        return {}

    ref_map = {}
    for ref in references:
        ref_map[ref.source_path] = {
            "target": ref.target_path,
            "chunk_id": ref.chunk_id,
        }

    return {"path_references": ref_map}


def enhance_query_with_paths(query: str, references: List[PathReference]) -> str:
    """增强查询：如果查询包含路径，添加引用的文件名

    Args:
        query: 原始查询
        references: 已有的引用列表

    Returns:
        增强后的查询
    """
    query_lower = query.lower()

    # 检查查询中是否包含路径
    for ref in references:
        if ref.source_path.lower() in query_lower:
            # 添加目标文件名到查询
            filename = ref.target_path.split('/')[-1]
            if filename not in query_lower:
                return f"{query} {filename}"

    return query
