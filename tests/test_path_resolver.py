"""
Path Resolver 测试
"""

import unittest
from mcp_gateway.path_resolver import (
    extract_paths, find_matching_chunks, build_reference_metadata,
    enhance_query_with_paths, PathReference,
)


class TestExtractPaths(unittest.TestCase):
    """路径提取测试"""

    def test_extract_absolute_path(self):
        """测试提取绝对路径"""
        content = "详见 /src/main/java/UserService.java"
        paths = extract_paths(content)
        # 标准化后去掉前导斜杠
        found = any("UserService.java" in p for p in paths)
        self.assertTrue(found)

    def test_extract_relative_path(self):
        """测试提取相对路径"""
        content = "参考 docs/memory/rag-status.md"
        paths = extract_paths(content)
        found = any("rag-status.md" in p for p in paths)
        self.assertTrue(found)

    def test_extract_code_reference(self):
        """测试提取代码引用"""
        content = "修改 `mcp_gateway/rag_client.py` 文件"
        paths = extract_paths(content)
        self.assertIn("mcp_gateway/rag_client.py", paths)

    def test_extract_markdown_link(self):
        """测试提取 Markdown 链接"""
        content = "查看 [文档](docs/guide.md)"
        paths = extract_paths(content)
        self.assertIn("docs/guide.md", paths)

    def test_ignore_http(self):
        """测试忽略 HTTP 链接"""
        content = "访问 https://example.com/test"
        paths = extract_paths(content)
        self.assertEqual(len(paths), 0)

    def test_multiple_paths(self):
        """测试提取多个路径"""
        content = """
        修改 mcp_gateway/rag_client.py
        参考 docs/memory/rag-status.md
        """
        paths = extract_paths(content)
        self.assertGreaterEqual(len(paths), 2)


class TestFindMatchingChunks(unittest.TestCase):
    """查找匹配测试"""

    def test_exact_match(self):
        """测试精确匹配"""
        paths = {"docs/memory/rag-status.md"}
        existing_docs = [
            {"id": "1", "name": "rag-status.md"},
            {"id": "2", "name": "other.md"},
        ]

        refs = find_matching_chunks(paths, existing_docs)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0].chunk_id, "1")

    def test_filename_match(self):
        """测试文件名匹配"""
        paths = {"rag_client.py"}
        existing_docs = [
            {"id": "1", "name": "mcp_gateway/rag_client.py"},
        ]

        refs = find_matching_chunks(paths, existing_docs)
        self.assertEqual(len(refs), 1)

    def test_no_match(self):
        """测试无匹配"""
        paths = {"nonexistent.py"}
        existing_docs = [
            {"id": "1", "name": "other.py"},
        ]

        refs = find_matching_chunks(paths, existing_docs)
        self.assertEqual(len(refs), 0)


class TestBuildReferenceMetadata(unittest.TestCase):
    """构建元数据测试"""

    def test_build_metadata(self):
        """测试构建元数据"""
        refs = [
            PathReference("docs/memory/rag-status.md", "rag-status.md", "123"),
            PathReference("mcp_gateway/rag_client.py", "rag_client.py", "456"),
        ]

        metadata = build_reference_metadata(refs)
        self.assertIn("path_references", metadata)
        self.assertEqual(len(metadata["path_references"]), 2)

    def test_empty_refs(self):
        """测试空引用"""
        metadata = build_reference_metadata([])
        self.assertEqual(metadata, {})


class TestEnhanceQuery(unittest.TestCase):
    """查询增强测试"""

    def test_enhance_with_path(self):
        """测试路径查询增强"""
        query = "查看 docs/memory/rag-status.md 的内容"
        refs = [
            PathReference("docs/memory/rag-status.md", "rag-status.md", "123"),
        ]

        enhanced = enhance_query_with_paths(query, refs)
        self.assertIn("rag-status.md", enhanced)

    def test_no_enhancement(self):
        """测试无需增强"""
        query = "RAG 模块完成度"
        refs = [
            PathReference("docs/memory/rag-status.md", "rag-status.md", "123"),
        ]

        enhanced = enhance_query_with_paths(query, refs)
        self.assertEqual(enhanced, query)


if __name__ == "__main__":
    unittest.main()
