#!/usr/bin/env python3
"""
问题修复验证测试 - 针对测试中发现的具体问题

问题清单：
1. 中文编码问题 - 中文内容存储为乱码
2. 中文LIKE搜索问题 - 搜索返回空结果
3. Module/Feature API问题 - 返回"系统执行出错"
4. 置信度API问题 - 返回None
"""

import sys
import json
import time
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, ".")

from mcp_gateway.rag_client import RAGClient, RAGConfig
from mcp_gateway.memory_tools import MemoryManager, MemoryConfig


class IssuesFixTest:
    """问题修复验证测试"""

    def __init__(self):
        self.config = MemoryConfig()
        self.manager = MemoryManager(self.config)
        self.rag_client = RAGClient(RAGConfig())
        self.test_project = "TestProject_IssuesFix"
        self.results = []

    def log_result(self, issue: str, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        status = "PASS" if passed else "FAIL"
        self.results.append({
            "issue": issue,
            "test": test_name,
            "status": status,
            "details": details
        })
        logger.info(f"[{status}] {issue} - {test_name}: {details}")

    def test_issue1_chinese_encoding(self):
        """问题1: 中文编码 - 验证中文内容正确存储"""
        logger.info("=" * 60)
        logger.info("问题1: 中文编码测试")
        logger.info("=" * 60)

        try:
            self.manager.ensure_logged_in()

            # 测试各种中文字符
            test_cases = [
                ("简单中文", "用户管理功能"),
                ("中文标点", "用户管理、订单处理、支付系统"),
                ("中文数字", "第1章、第2节、第3条"),
                ("混合内容", "用户管理(User Management)功能说明"),
            ]

            for test_name, content in test_cases:
                full_content = f"# {test_name}\n\n{content}\n\n## 详细说明\n这是测试内容。"

                result = self.manager.upload_memory(
                    self.test_project,
                    f"encoding_{test_name}.md",
                    full_content,
                    feature_codes=[f"encoding_{test_name}"],
                    module="encoding_test"
                )

                if result.get("status") == "success":
                    self.log_result("中文编码", f"上传{test_name}", True, f"doc_id={result.get('doc_id')}")
                else:
                    self.log_result("中文编码", f"上传{test_name}", False, f"失败: {result}")
                    return False

            time.sleep(5)  # 等待分块完成

            # 验证检索
            for test_name, content in test_cases:
                result = self.manager.ask_project(
                    self.test_project,
                    content[:4],  # 搜索前4个字
                    top_k=1,
                    feature_codes=[f"encoding_{test_name}"]
                )

                if result.get("results"):
                    retrieved_content = result["results"][0].get("content", "")
                    if content in retrieved_content:
                        self.log_result("中文编码", f"检索{test_name}", True, "内容正确")
                    else:
                        self.log_result("中文编码", f"检索{test_name}", False, f"内容异常: {retrieved_content[:50]}")
                        return False
                else:
                    self.log_result("中文编码", f"检索{test_name}", False, "未检索到结果")
                    return False

            return True

        except Exception as e:
            self.log_result("中文编码", "测试异常", False, f"异常: {e}")
            return False

    def test_issue2_chinese_search(self):
        """问题2: 中文LIKE搜索 - 验证中文关键词搜索"""
        logger.info("=" * 60)
        logger.info("问题2: 中文LIKE搜索测试")
        logger.info("=" * 60)

        try:
            self.manager.ensure_logged_in()

            # 测试不同长度的中文关键词
            test_queries = [
                ("短关键词", "用户"),
                ("中关键词", "用户管理"),
                ("长关键词", "用户管理功能"),
                ("句子关键词", "用户管理功能说明"),
            ]

            all_passed = True
            for test_name, query in test_queries:
                result = self.manager.ask_project(
                    self.test_project,
                    query,
                    top_k=3
                )

                if result.get("results"):
                    self.log_result("中文搜索", f"{test_name}: {query}", True, f"返回{len(result['results'])}条结果")
                else:
                    # LIKE搜索可能不支持中文，但向量搜索应该可以
                    logger.warning(f"LIKE搜索未返回结果，尝试向量搜索: {query}")
                    # 这里记录问题但不一定算失败
                    self.log_result("中文搜索", f"{test_name}: {query}", False, "LIKE搜索未返回结果")
                    all_passed = False

            return all_passed

        except Exception as e:
            self.log_result("中文搜索", "测试异常", False, f"异常: {e}")
            return False

    def test_issue3_module_feature_api(self):
        """问题3: Module/Feature API - 验证API可用性"""
        logger.info("=" * 60)
        logger.info("问题3: Module/Feature API测试")
        logger.info("=" * 60)

        try:
            self.rag_client.ensure_logged_in()

            # 测试模块API
            test_module = "test_module_issues"

            # 创建模块
            try:
                result = self.rag_client.create_module(test_module, "问题测试模块")
                if result and "error" not in result:
                    self.log_result("模块API", "创建模块", True, f"module={test_module}")
                else:
                    self.log_result("模块API", "创建模块", False, f"创建失败: {result}")
                    return False
            except Exception as e:
                self.log_result("模块API", "创建模块", False, f"API调用失败: {e}")
                return False

            # 列出模块
            try:
                modules = self.rag_client.list_modules()
                if any(m.get("name") == test_module for m in modules):
                    self.log_result("模块API", "列出模块", True, f"找到模块{test_module}")
                else:
                    self.log_result("模块API", "列出模块", False, f"未找到模块")
                    return False
            except Exception as e:
                self.log_result("模块API", "列出模块", False, f"API调用失败: {e}")
                return False

            # 删除模块
            try:
                result = self.rag_client.delete_module(test_module)
                if result and "error" not in result:
                    self.log_result("模块API", "删除模块", True, f"module={test_module}")
                else:
                    self.log_result("模块API", "删除模块", False, f"删除失败: {result}")
                    return False
            except Exception as e:
                self.log_result("模块API", "删除模块", False, f"API调用失败: {e}")
                return False

            # 测试功能API
            test_feature = "test_feature_issues"

            # 创建功能
            try:
                result = self.rag_client.create_feature(
                    test_feature,
                    "问题测试功能",
                    test_module,
                    "问题测试功能描述"
                )
                if result and "error" not in result:
                    self.log_result("功能API", "创建功能", True, f"feature={test_feature}")
                else:
                    self.log_result("功能API", "创建功能", False, f"创建失败: {result}")
                    return False
            except Exception as e:
                self.log_result("功能API", "创建功能", False, f"API调用失败: {e}")
                return False

            # 列出功能
            try:
                features = self.rag_client.list_features()
                if any(f.get("featureCode") == test_feature for f in features):
                    self.log_result("功能API", "列出功能", True, f"找到功能{test_feature}")
                else:
                    self.log_result("功能API", "列出功能", False, f"未找到功能")
                    return False
            except Exception as e:
                self.log_result("功能API", "列出功能", False, f"API调用失败: {e}")
                return False

            # 删除功能
            try:
                result = self.rag_client.delete_feature(test_feature)
                if result and "error" not in result:
                    self.log_result("功能API", "删除功能", True, f"feature={test_feature}")
                else:
                    self.log_result("功能API", "删除功能", False, f"删除失败: {result}")
                    return False
            except Exception as e:
                self.log_result("功能API", "删除功能", False, f"API调用失败: {e}")
                return False

            return True

        except Exception as e:
            self.log_result("Module/Feature API", "测试异常", False, f"异常: {e}")
            return False

    def test_issue4_confidence_api(self):
        """问题4: 置信度API - 验证置信度计算和获取"""
        logger.info("=" * 60)
        logger.info("问题4: 置信度API测试")
        logger.info("=" * 60)

        try:
            self.manager.ensure_logged_in()

            # 上传测试内容
            test_content = """# 置信度API测试

## 功能说明
这是一个置信度API测试文档，用于验证置信度计算功能。

## 测试场景
1. 获取置信度
2. 计算置信度
3. 归一化置信度
"""

            result = self.manager.upload_memory(
                self.test_project,
                "confidence_api_test.md",
                test_content,
                feature_codes=["confidence_api"],
                module="confidence_test"
            )

            if result.get("status") != "success":
                self.log_result("置信度API", "上传测试内容", False, f"上传失败: {result}")
                return False

            self.log_result("置信度API", "上传测试内容", True, f"doc_id={result.get('doc_id')}")
            time.sleep(5)

            # 检索获取chunk_id
            search_result = self.manager.ask_project(
                self.test_project,
                "置信度API测试",
                top_k=1,
                feature_codes=["confidence_api"]
            )

            if not search_result.get("results"):
                self.log_result("置信度API", "检索测试内容", False, "未检索到结果")
                return False

            chunk_id = search_result["results"][0].get("chunkId")
            if not chunk_id:
                self.log_result("置信度API", "获取chunk_id", False, "未获取到chunk_id")
                return False

            self.log_result("置信度API", "获取chunk_id", True, f"chunk_id={chunk_id}")

            # 测试获取置信度
            try:
                confidence = self.rag_client.get_confidence(chunk_id)
                if confidence is not None:
                    self.log_result("置信度API", "获取置信度", True, f"confidence={confidence}")
                else:
                    self.log_result("置信度API", "获取置信度", False, "置信度为None")
                    return False
            except Exception as e:
                self.log_result("置信度API", "获取置信度", False, f"API调用失败: {e}")
                return False

            # 测试计算置信度
            try:
                confidence = self.rag_client.calculate_confidence(chunk_id)
                if confidence is not None and confidence >= 1:
                    self.log_result("置信度API", "计算置信度", True, f"confidence={confidence}")
                else:
                    self.log_result("置信度API", "计算置信度", False, f"置信度异常: {confidence}")
                    return False
            except Exception as e:
                self.log_result("置信度API", "计算置信度", False, f"API调用失败: {e}")
                return False

            # 测试归一化置信度
            try:
                chunk_ids = [chunk_id]
                normalized = self.rag_client.normalize_confidence(chunk_ids)
                if normalized and len(normalized) > 0:
                    self.log_result("置信度API", "归一化置信度", True, f"normalized={normalized[0]}")
                else:
                    self.log_result("置信度API", "归一化置信度", False, f"归一化失败: {normalized}")
                    return False
            except Exception as e:
                self.log_result("置信度API", "归一化置信度", False, f"API调用失败: {e}")
                return False

            return True

        except Exception as e:
            self.log_result("置信度API", "测试异常", False, f"异常: {e}")
            return False

    def cleanup(self):
        """清理测试数据"""
        logger.info("=" * 60)
        logger.info("清理测试数据")
        logger.info("=" * 60)

        try:
            from mcp_gateway.memory_tools import delete_memory_impl
            result = delete_memory_impl(self.test_project)
            if result.get("status") == "success":
                logger.info(f"清理成功: {result}")
            else:
                logger.warning(f"清理失败: {result}")
        except Exception as e:
            logger.warning(f"清理异常: {e}")

    def run_all_tests(self):
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("开始问题修复验证测试")
        logger.info("=" * 60)

        tests = [
            ("问题1: 中文编码", self.test_issue1_chinese_encoding),
            ("问题2: 中文LIKE搜索", self.test_issue2_chinese_search),
            ("问题3: Module/Feature API", self.test_issue3_module_feature_api),
            ("问题4: 置信度API", self.test_issue4_confidence_api),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"{test_name} 异常: {e}")
                failed += 1

        # 清理
        self.cleanup()

        # 输出总结
        logger.info("=" * 60)
        logger.info("测试总结")
        logger.info("=" * 60)
        logger.info(f"通过: {passed}")
        logger.info(f"失败: {failed}")
        logger.info(f"总计: {passed + failed}")

        # 输出详细结果
        logger.info("\n详细结果:")
        for result in self.results:
            logger.info(f"  [{result['status']}] {result['issue']} - {result['test']}: {result['details']}")

        return failed == 0


def main():
    """主函数"""
    test = IssuesFixTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
