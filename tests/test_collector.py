"""
Collector 模块测试
"""

import unittest
from unittest.mock import patch, MagicMock
from mcp_gateway.collector.slimmer import ContentSlimmer
from mcp_gateway.collector.metadata_extractor import MetadataExtractor


class TestContentSlimmer(unittest.TestCase):
    """ContentSlimmer 单元测试"""

    def setUp(self):
        self.slimmer = ContentSlimmer()

    def test_slim_removes_short_term_content(self):
        """测试移除短期价值内容"""
        content = """# 项目规范

## 编码规范

使用 4 空格缩进。

## 更新日志

v1.0.0 - 修复了xxx
v1.0.1 - 临时修复了yyy
"""
        result = self.slimmer.slim(content)
        self.assertNotIn("更新日志", result.content)
        self.assertIn("编码规范", result.content)
        self.assertGreater(len(result.removed_sections), 0)

    def test_slim_keeps_long_term_content(self):
        """测试保留长期价值内容"""
        content = """# 架构设计

## 微服务架构

采用 Spring Cloud 微服务架构，包含：
- 服务注册与发现
- 配置中心
- 网关

## 最佳实践

1. 使用 DTO 隔离层
2. 统一异常处理
"""
        result = self.slimmer.slim(content)
        self.assertIn("微服务架构", result.content)
        self.assertIn("最佳实践", result.content)

    def test_slim_short_content_untouched(self):
        """测试短内容不处理"""
        content = "# 短文档\n\n简短内容。"
        result = self.slimmer.slim(content)
        self.assertEqual(result.content, content)
        self.assertEqual(len(result.removed_sections), 0)

    def test_is_long_term_valuable(self):
        """测试长期价值判断"""
        valuable = "这是一个架构设计最佳实践指南，包含编码规范和流程标准。"
        not_valuable = "今天调试了一个 bug，临时修复了一下。"

        self.assertTrue(self.slimmer.is_long_term_valuable(valuable))
        self.assertFalse(self.slimmer.is_long_term_valuable(not_valuable))

    def test_reduction_ratio(self):
        """测试压缩比计算"""
        content = """# 文档

## 更新日志

v1.0.0
v1.0.1
v1.0.2
v1.0.3

## 正文

这是正文内容。
"""
        result = self.slimmer.slim(content)
        self.assertGreater(result.reduction_ratio, 0)


class TestMetadataExtractor(unittest.TestCase):
    """MetadataExtractor 单元测试"""

    def setUp(self):
        self.extractor = MetadataExtractor()

    def test_extract_title_from_h1(self):
        """测试从 H1 标题提取"""
        content = "# Spring Boot 开发指南\n\n内容..."
        metadata = self.extractor.extract_from_content(content)
        self.assertEqual(metadata.title, "Spring Boot 开发指南")

    def test_extract_tags(self):
        """测试提取标签"""
        content = """# 文档

tags: [Spring Boot, Redis, Docker]

内容...
"""
        metadata = self.extractor.extract_from_content(content)
        self.assertIn("Spring Boot", metadata.tags)
        self.assertIn("Redis", metadata.tags)

    def test_infer_category_from_path(self):
        """测试从路径推断分类"""
        content = "# 文档"
        metadata = self.extractor.extract_from_content(
            content, file_path="docs/编码规范/Java规范.md"
        )
        self.assertEqual(metadata.category, "编码规范")

    def test_extract_tech_tags(self):
        """测试自动提取技术标签"""
        content = """# 使用 Spring Boot 和 Redis

import redis
from fastapi import FastAPI

docker run redis
"""
        metadata = self.extractor.extract_from_content(content)
        self.assertIn("Redis", metadata.tags)

    def test_extract_from_frontmatter(self):
        """测试从 YAML frontmatter 提取"""
        content = """---
title: API 文档
author: 张三
category: 接口文档
tags: [API, REST]
---

# API 文档

内容...
"""
        metadata = self.extractor.extract_from_content(content)
        self.assertEqual(metadata.title, "API 文档")
        self.assertEqual(metadata.author, "张三")
        self.assertEqual(metadata.category, "接口文档")
        self.assertIn("API", metadata.tags)


if __name__ == "__main__":
    unittest.main()
