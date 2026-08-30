import os
#!/usr/bin/env python3
"""
综合测试脚本 - 覆盖所有发现的问题

测试内容：
1. 中文编码测试
2. 中文搜索测试
3. Module/Feature CRUD 测试
4. 置信度计算测试
5. 逐级降级检索测试
"""

import sys
import json
import time
import logging
from typing import Dict, Any, List

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from mcp_gateway.rag_client import RAGClient, RAGConfig
from mcp_gateway.memory_tools import MemoryManager, MemoryConfig


class ComprehensiveTest:
    """综合测试类"""

    def __init__(self):
        self.config = MemoryConfig()
        self.manager = MemoryManager(self.config)
        self.rag_client = RAGClient(RAGConfig())
        self.test_project = "TestProject_Comprehensive"
        self.results = []

    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        status = "PASS" if passed else "FAIL"
        self.results.append({
            "test": test_name,
            "status": status,
            "details": details
        })
        logger.info(f"[{status}] {test_name}: {details}")

    def test_chinese_encoding(self) -> bool:
        """测试1: 中文编码 - 确保中文内容正确存储"""
        logger.info("=" * 60)
        logger.info("测试1: 中文编码测试")
        logger.info("=" * 60)

        try:
            self.manager.ensure_logged_in()

            # 测试中文内容
            chinese_content = """# 中文编码测试

## 功能说明
这是一个中文编码测试文档，用于验证中文内容是否能正确存储和检索。

## 关键词
- 用户管理
- 订单处理
- 支付系统
- 数据分析

## 详细描述
本系统支持多语言处理，包括简体中文、繁体中文和英文。
"""

            # 上传中文内容
            result = self.manager.upload_memory(
                self.test_project,
                "chinese_encoding_test.md",
                chinese_content,
                feature_codes=["test_encoding"],
                module="test"
            )

            if result.get("status") == "success":
                self.log_result("中文编码上传", True, f"doc_id={result.get('doc_id')}")
                time.sleep(3)  # 等待分块完成

                # 检索验证
                search_result = self.manager.ask_project(
                    self.test_project,
                    "用户管理",
                    top_k=3
                )

                if search_result.get("results"):
                    # 检查内容是否包含正确的中文
                    content = search_result["results"][0].get("content", "")
                    if "用户管理" in content:
                        self.log_result("中文编码检索", True, "中文内容正确存储和检索")
                        return True
                    else:
                        self.log_result("中文编码检索", False, f"内容异常: {content[:100]}")
                        return False
                else:
                    self.log_result("中文编码检索", False, "未检索到结果")
                    return False
            else:
                self.log_result("中文编码上传", False, f"上传失败: {result}")
                return False

        except Exception as e:
            self.log_result("中文编码测试", False, f"异常: {e}")
            return False

    def test_chinese_search(self) -> bool:
        """测试2: 中文搜索 - 验证中文关键词搜索"""
        logger.info("=" * 60)
        logger.info("测试2: 中文搜索测试")
        logger.info("=" * 60)

        try:
            self.manager.ensure_logged_in()

            # 测试不同中文关键词
            test_queries = [
                ("用户管理", "应返回用户管理相关内容"),
                ("订单处理", "应返回订单处理相关内容"),
                ("支付系统", "应返回支付系统相关内容"),
            ]

            all_passed = True
            for query, expected in test_queries:
                result = self.manager.ask_project(
                    self.test_project,
                    query,
                    top_k=3
                )

                if result.get("results"):
                    self.log_result(f"中文搜索: {query}", True, f"返回{len(result['results'])}条结果")
                else:
                    self.log_result(f"中文搜索: {query}", False, f"未返回结果")
                    all_passed = False

            return all_passed

        except Exception as e:
            self.log_result("中文搜索测试", False, f"异常: {e}")
            return False

    def test_module_feature_crud(self) -> bool:
        """测试3: Module/Feature CRUD - 验证模块和功能管理"""
        logger.info("=" * 60)
        logger.info("测试3: Module/Feature CRUD 测试")
        logger.info("=" * 60)

        try:
            self.rag_client.ensure_logged_in()

            # 测试创建模块
            test_module = "test_module_comprehensive"
            try:
                result = self.rag_client.create_module(test_module, "综合测试模块")
                if result and "error" not in result:
                    self.log_result("创建模块", True, f"module={test_module}")
                else:
                    self.log_result("创建模块", False, f"创建失败: {result}")
                    return False
            except Exception as e:
                self.log_result("创建模块", False, f"API调用失败: {e}")
                return False

            # 测试列出模块
            try:
                modules = self.rag_client.list_modules()
                if any(m.get("name") == test_module for m in modules):
                    self.log_result("列出模块", True, f"找到模块{test_module}")
                else:
                    self.log_result("列出模块", False, f"未找到模块")
                    return False
            except Exception as e:
                self.log_result("列出模块", False, f"API调用失败: {e}")
                return False

            # 测试创建功能
            test_feature = "test_feature_001"
            try:
                result = self.rag_client.create_feature(
                    test_feature,
                    "测试功能",
                    test_module,
                    "综合测试功能"
                )
                if result and "error" not in result:
                    self.log_result("创建功能", True, f"feature={test_feature}")
                else:
                    self.log_result("创建功能", False, f"创建失败: {result}")
                    return False
            except Exception as e:
                self.log_result("创建功能", False, f"API调用失败: {e}")
                return False

            # 测试列出功能
            try:
                features = self.rag_client.list_features(test_module)
                if any(f.get("featureCode") == test_feature for f in features):
                    self.log_result("列出功能", True, f"找到功能{test_feature}")
                else:
                    self.log_result("列出功能", False, f"未找到功能")
                    return False
            except Exception as e:
                self.log_result("列出功能", False, f"API调用失败: {e}")
                return False

            # 测试删除功能
            try:
                result = self.rag_client.delete_feature(test_feature)
                if result and "error" not in result:
                    self.log_result("删除功能", True, f"feature={test_feature}")
                else:
                    self.log_result("删除功能", False, f"删除失败: {result}")
                    return False
            except Exception as e:
                self.log_result("删除功能", False, f"API调用失败: {e}")
                return False

            # 测试删除模块
            try:
                result = self.rag_client.delete_module(test_module)
                if result and "error" not in result:
                    self.log_result("删除模块", True, f"module={test_module}")
                else:
                    self.log_result("删除模块", False, f"删除失败: {result}")
                    return False
            except Exception as e:
                self.log_result("删除模块", False, f"API调用失败: {e}")
                return False

            return True

        except Exception as e:
            self.log_result("Module/Feature CRUD", False, f"异常: {e}")
            return False

    def test_confidence_calculation(self) -> bool:
        """测试4: 置信度计算 - 验证置信度API"""
        logger.info("=" * 60)
        logger.info("测试4: 置信度计算测试")
        logger.info("=" * 60)

        try:
            self.manager.ensure_logged_in()

            # 上传测试内容
            test_content = """# 置信度测试

## 功能说明
这是一个置信度测试文档，用于验证置信度计算功能。

## 测试场景
1. 单一来源：置信度应为1
2. 多个来源：置信度应增加
"""

            result = self.manager.upload_memory(
                self.test_project,
                "confidence_test.md",
                test_content,
                feature_codes=["test_confidence"],
                module="test"
            )

            if result.get("status") != "success":
                self.log_result("置信度上传", False, f"上传失败: {result}")
                return False

            self.log_result("置信度上传", True, f"doc_id={result.get('doc_id')}")
            time.sleep(5)  # 等待分块和置信度计算

            # 检索获取chunk_id
            search_result = self.manager.ask_project(
                self.test_project,
                "置信度测试",
                top_k=1
            )

            if not search_result.get("results"):
                self.log_result("置信度检索", False, "未检索到结果")
                return False

            chunk_id = search_result["results"][0].get("chunkId")
            if not chunk_id:
                self.log_result("置信度检索", False, "未获取到chunk_id")
                return False

            # 测试获取置信度
            try:
                confidence = self.rag_client.get_confidence(chunk_id)
                if confidence is not None:
                    self.log_result("获取置信度", True, f"confidence={confidence}")
                else:
                    self.log_result("获取置信度", False, "置信度为None")
                    return False
            except Exception as e:
                self.log_result("获取置信度", False, f"API调用失败: {e}")
                return False

            # 测试计算置信度
            try:
                confidence = self.rag_client.calculate_confidence(chunk_id)
                if confidence is not None and confidence >= 1:
                    self.log_result("计算置信度", True, f"confidence={confidence}")
                else:
                    self.log_result("计算置信度", False, f"置信度异常: {confidence}")
                    return False
            except Exception as e:
                self.log_result("计算置信度", False, f"API调用失败: {e}")
                return False

            return True

        except Exception as e:
            self.log_result("置信度计算测试", False, f"异常: {e}")
            return False

    def test_hierarchical_retrieval(self) -> bool:
        """测试5: 逐级降级检索 - 验证功能级→模块级→全库检索"""
        logger.info("=" * 60)
        logger.info("测试5: 逐级降级检索测试")
        logger.info("=" * 60)

        try:
            self.manager.ensure_logged_in()

            # 上传带不同feature_codes的内容
            contents = [
                ("hierarchical_feature_A.md", "# 功能A文档\n\n这是功能A的详细说明。", ["feature_A"], "module_X"),
                ("hierarchical_feature_B.md", "# 功能B文档\n\n这是功能B的详细说明。", ["feature_B"], "module_X"),
                ("hierarchical_module.md", "# 模块X文档\n\n这是模块X的通用说明。", None, "module_X"),
            ]

            for filename, content, codes, module in contents:
                result = self.manager.upload_memory(
                    self.test_project,
                    filename,
                    content,
                    feature_codes=codes,
                    module=module
                )
                if result.get("status") != "success":
                    self.log_result(f"上传{filename}", False, f"上传失败: {result}")
                    return False
                self.log_result(f"上传{filename}", True, f"doc_id={result.get('doc_id')}")

            time.sleep(5)  # 等待分块完成

            # 测试功能级检索
            result = self.manager.ask_project(
                self.test_project,
                "功能A",
                top_k=3,
                feature_codes=["feature_A"]
            )
            if result.get("results") and result.get("level") == "feature":
                self.log_result("功能级检索", True, f"level={result['level']}, count={result['count']}")
            else:
                self.log_result("功能级检索", False, f"level={result.get('level')}, count={result.get('count')}")
                return False

            # 测试模块级检索
            result = self.manager.ask_project(
                self.test_project,
                "模块X",
                top_k=3,
                module="module_X"
            )
            if result.get("results") and result.get("level") in ["feature", "module"]:
                self.log_result("模块级检索", True, f"level={result['level']}, count={result['count']}")
            else:
                self.log_result("模块级检索", False, f"level={result.get('level')}, count={result.get('count')}")
                return False

            # 测试全库检索
            result = self.manager.ask_project(
                self.test_project,
                "文档说明",
                top_k=3
            )
            if result.get("results") and result.get("level") == "global":
                self.log_result("全库检索", True, f"level={result['level']}, count={result['count']}")
            else:
                self.log_result("全库检索", False, f"level={result.get('level')}, count={result.get('count')}")
                return False

            return True

        except Exception as e:
            self.log_result("逐级降级检索测试", False, f"异常: {e}")
            return False

    def test_metadata_storage(self) -> bool:
        """测试6: 元数据存储 - 验证feature_codes和module元数据"""
        logger.info("=" * 60)
        logger.info("测试6: 元数据存储测试")
        logger.info("=" * 60)

        try:
            self.manager.ensure_logged_in()

            # 上传带元数据的内容
            test_content = """# 元数据测试

## 功能编号
- feature_001
- feature_002

## 模块
user_module
"""

            result = self.manager.upload_memory(
                self.test_project,
                "metadata_test.md",
                test_content,
                feature_codes=["feature_001", "feature_002"],
                module="user_module"
            )

            if result.get("status") != "success":
                self.log_result("元数据上传", False, f"上传失败: {result}")
                return False

            self.log_result("元数据上传", True, f"doc_id={result.get('doc_id')}")
            time.sleep(5)

            # 按feature_code检索
            result = self.manager.ask_project(
                self.test_project,
                "元数据测试",
                top_k=3,
                feature_codes=["feature_001"]
            )
            if result.get("results"):
                self.log_result("按feature_code检索", True, f"返回{len(result['results'])}条结果")
            else:
                self.log_result("按feature_code检索", False, "未返回结果")
                return False

            # 按module检索
            result = self.manager.ask_project(
                self.test_project,
                "元数据测试",
                top_k=3,
                module="user_module"
            )
            if result.get("results"):
                self.log_result("按module检索", True, f"返回{len(result['results'])}条结果")
            else:
                self.log_result("按module检索", False, "未返回结果")
                return False

            return True

        except Exception as e:
            self.log_result("元数据存储测试", False, f"异常: {e}")
            return False

    def test_delete_operations(self) -> bool:
        """测试7: 删除操作 - 验证记忆文件删除"""
        logger.info("=" * 60)
        logger.info("测试7: 删除操作测试")
        logger.info("=" * 60)

        try:
            self.manager.ensure_logged_in()

            # 上传测试文件
            test_content = "# 删除测试\n\n这个文件将被删除。"
            result = self.manager.upload_memory(
                self.test_project,
                "delete_test.md",
                test_content
            )

            if result.get("status") != "success":
                self.log_result("删除测试上传", False, f"上传失败: {result}")
                return False

            self.log_result("删除测试上传", True, f"doc_id={result.get('doc_id')}")
            time.sleep(3)

            # 删除文件
            from mcp_gateway.memory_tools import delete_memory_impl
            delete_result = delete_memory_impl(self.test_project, "delete_test.md")

            if delete_result.get("status") == "success":
                self.log_result("删除文件", True, f"deleted_docs={delete_result.get('deleted_docs')}")
            else:
                self.log_result("删除文件", False, f"删除失败: {delete_result}")
                return False

            return True

        except Exception as e:
            self.log_result("删除操作测试", False, f"异常: {e}")
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
        logger.info("开始综合测试")
        logger.info("=" * 60)

        tests = [
            ("中文编码测试", self.test_chinese_encoding),
            ("中文搜索测试", self.test_chinese_search),
            ("Module/Feature CRUD测试", self.test_module_feature_crud),
            ("置信度计算测试", self.test_confidence_calculation),
            ("逐级降级检索测试", self.test_hierarchical_retrieval),
            ("元数据存储测试", self.test_metadata_storage),
            ("删除操作测试", self.test_delete_operations),
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
            logger.info(f"  [{result['status']}] {result['test']}: {result['details']}")

        return failed == 0


def main():
    """主函数"""
    test = ComprehensiveTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
