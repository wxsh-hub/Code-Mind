#!/usr/bin/env python3
"""
全链路体验测试 - 详细记录每个功能的使用体验
"""

import sys
import json
import time
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, ".")

from mcp_gateway.rag_client import RAGClient, RAGConfig
from mcp_gateway.memory_tools import MemoryManager, MemoryConfig, upload_memory_impl, ask_project_impl, list_projects_impl, delete_memory_impl
from mcp_gateway.skill_tools import SkillStore, upload_skill_impl, search_skill_impl, list_skills_impl, get_skill_impl
from mcp_gateway.feature_tools import create_module_impl, list_modules_impl, delete_module_impl, create_feature_impl, list_features_impl, delete_feature_impl
from mcp_gateway.discovery_tools import list_mcp_tools_impl
from mcp_gateway.conflict_review import list_conflicts_impl, review_conflict_impl


class FullExperienceTest:
    """全链路体验测试"""

    def __init__(self):
        self.memory_manager = MemoryManager(MemoryConfig())
        self.rag_client = RAGClient(RAGConfig())
        self.test_project = "FullExperienceTest"
        self.results = []

    def log(self, module: str, action: str, status: str, details: str = ""):
        """记录测试结果"""
        self.results.append({
            "module": module,
            "action": action,
            "status": status,
            "details": details
        })
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        logger.info(f"{emoji} [{module}] {action}: {details}")

    def test_1_memory_upload(self):
        """测试1: 记忆上传功能"""
        logger.info("\n" + "=" * 60)
        logger.info("测试1: 记忆上传功能 (upload_memory)")
        logger.info("=" * 60)

        # 测试中文内容
        content = """# 项目记忆测试

## 功能说明
这是 Code-Mind 项目的记忆管理功能测试。

## 关键特性
- 支持中文内容
- 支持 Markdown 格式
- 自动分块存储
- 支持元数据标注

## 使用场景
1. 项目规范文档
2. 开发经验记录
3. API 使用说明
4. 架构设计文档
"""

        result = upload_memory_impl(
            self.test_project,
            "test_memory.md",
            content,
            feature_codes=["memory_upload"],
            module="core"
        )

        if result.get("status") == "success":
            self.log("记忆管理", "上传中文记忆", "PASS", f"doc_id={result.get('doc_id')}")
        else:
            self.log("记忆管理", "上传中文记忆", "FAIL", f"错误: {result}")

    def test_2_memory_search(self):
        """测试2: 记忆搜索功能"""
        logger.info("\n" + "=" * 60)
        logger.info("测试2: 记忆搜索功能 (ask_project)")
        logger.info("=" * 60)

        # 测试不同搜索场景
        test_cases = [
            ("中文关键词搜索", "项目规范"),
            ("功能相关搜索", "记忆管理"),
            ("模块相关搜索", "core 模块"),
        ]

        for desc, query in test_cases:
            result = ask_project_impl(self.test_project, query, top_k=3)
            if result.get("results"):
                self.log("记忆管理", desc, "PASS", f"返回 {len(result['results'])} 条结果")
            else:
                self.log("记忆管理", desc, "FAIL", "未返回结果")

    def test_3_list_projects(self):
        """测试3: 项目列表功能"""
        logger.info("\n" + "=" * 60)
        logger.info("测试3: 项目列表功能 (list_projects)")
        logger.info("=" * 60)

        result = list_projects_impl()
        projects = result.get("projects", [])
        self.log("记忆管理", "列出项目", "PASS" if projects else "WARN", f"找到 {len(projects)} 个项目")

    def test_4_skill_management(self):
        """测试4: 技能管理功能"""
        logger.info("\n" + "=" * 60)
        logger.info("测试4: 技能管理功能 (upload_skill, search_skill)")
        logger.info("=" * 60)

        # 上传技能
        result = upload_skill_impl(
            self.test_project,
            "Git Commit 规范",
            "# Git Commit 规范\n\n使用 Conventional Commits 格式：\n- feat: 新功能\n- fix: 修复\n- docs: 文档",
            category="coding",
            tags=["git", "commit", "规范"],
            description="Git 提交信息规范"
        )

        if result.get("status") == "success":
            self.log("技能管理", "上传技能", "PASS", f"技能名: Git Commit 规范")
        else:
            self.log("技能管理", "上传技能", "FAIL", f"错误: {result}")

        # 列出技能
        result = list_skills_impl(self.test_project)
        if result.get("skills"):
            self.log("技能管理", "列出技能", "PASS", f"找到 {result['count']} 个技能")
        else:
            self.log("技能管理", "列出技能", "FAIL", "未找到技能")

        # 搜索技能
        result = search_skill_impl(self.test_project, "commit")
        if result.get("results"):
            self.log("技能管理", "搜索技能", "PASS", f"返回 {result['count']} 条结果")
        else:
            self.log("技能管理", "搜索技能", "FAIL", "未返回结果")

    def test_5_module_management(self):
        """测试5: 模块管理功能"""
        logger.info("\n" + "=" * 60)
        logger.info("测试5: 模块管理功能 (create_module, list_modules)")
        logger.info("=" * 60)

        # 创建模块
        result = create_module_impl(self.test_project, "test_module", "测试模块")
        if result.get("error"):
            self.log("模块管理", "创建模块", "FAIL", f"错误: {result.get('error')}")
        elif result.get("data") and result["data"].get("id"):
            self.log("模块管理", "创建模块", "PASS", f"module_id={result['data']['id']}")
        elif result.get("status") == "success":
            self.log("模块管理", "创建模块", "PASS", f"响应: {result}")
        else:
            self.log("模块管理", "创建模块", "FAIL", f"未知响应: {result}")

        # 列出模块
        result = list_modules_impl(self.test_project)
        if result.get("modules"):
            self.log("模块管理", "列出模块", "PASS", f"找到 {result['count']} 个模块")
        else:
            self.log("模块管理", "列出模块", "FAIL", f"响应: {result}")

    def test_6_feature_management(self):
        """测试6: 功能管理功能"""
        logger.info("\n" + "=" * 60)
        logger.info("测试6: 功能管理功能 (create_feature, list_features)")
        logger.info("=" * 60)

        # 创建功能
        result = create_feature_impl(self.test_project, "test_001", "测试功能", "test_module", "测试功能描述")
        if result.get("error"):
            self.log("功能管理", "创建功能", "FAIL", f"错误: {result.get('error')}")
        elif result.get("data") and result["data"].get("id"):
            self.log("功能管理", "创建功能", "PASS", f"feature_id={result['data']['id']}")
        elif result.get("status") == "success":
            self.log("功能管理", "创建功能", "PASS", f"响应: {result}")
        else:
            self.log("功能管理", "创建功能", "FAIL", f"未知响应: {result}")

        # 列出功能
        result = list_features_impl(self.test_project)
        if result.get("features"):
            self.log("功能管理", "列出功能", "PASS", f"找到 {result['count']} 个功能")
        else:
            self.log("功能管理", "列出功能", "FAIL", f"响应: {result}")

    def test_7_discovery_tools(self):
        """测试7: 工具发现功能"""
        logger.info("\n" + "=" * 60)
        logger.info("测试7: 工具发现功能 (list_mcp_tools)")
        logger.info("=" * 60)

        result = list_mcp_tools_impl()
        if result.get("tools"):
            self.log("工具发现", "列出MCP工具", "PASS", f"找到 {result['total_count']} 个工具")
        else:
            self.log("工具发现", "列出MCP工具", "FAIL", f"响应: {result}")

    def test_8_conflict_review(self):
        """测试8: 冲突审查功能"""
        logger.info("\n" + "=" * 60)
        logger.info("测试8: 冲突审查功能 (list_conflicts)")
        logger.info("=" * 60)

        result = list_conflicts_impl(self.test_project)
        if "conflicts" in result:
            self.log("冲突审查", "列出冲突", "PASS", f"找到 {result.get('count', 0)} 个冲突")
        else:
            self.log("冲突审查", "列出冲突", "FAIL", f"响应异常: {result}")

    def test_9_delete_operations(self):
        """测试9: 删除操作"""
        logger.info("\n" + "=" * 60)
        logger.info("测试9: 删除操作")
        logger.info("=" * 60)

        # 删除记忆
        result = delete_memory_impl(self.test_project, "test_memory.md")
        if result.get("status") == "success":
            self.log("删除操作", "删除记忆文件", "PASS", f"删除 {result.get('deleted_docs', 0)} 个文档")
        else:
            self.log("删除操作", "删除记忆文件", "FAIL", f"错误: {result}")

    def test_10_cleanup(self):
        """测试10: 清理测试数据"""
        logger.info("\n" + "=" * 60)
        logger.info("测试10: 清理测试数据")
        logger.info("=" * 60)

        result = delete_memory_impl(self.test_project)
        if result.get("status") == "success":
            self.log("清理", "删除测试项目", "PASS", f"项目已删除")
        else:
            self.log("清理", "删除测试项目", "FAIL", f"错误: {result}")

    def run_all_tests(self):
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("Code-Mind 全链路体验测试")
        logger.info("=" * 60)

        tests = [
            self.test_1_memory_upload,
            self.test_2_memory_search,
            self.test_3_list_projects,
            self.test_4_skill_management,
            self.test_5_module_management,
            self.test_6_feature_management,
            self.test_7_discovery_tools,
            self.test_8_conflict_review,
            self.test_9_delete_operations,
            self.test_10_cleanup,
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                self.log("异常", test.__name__, "FAIL", str(e))

        # 输出总结
        self.print_summary()

    def print_summary(self):
        """输出测试总结"""
        logger.info("\n" + "=" * 60)
        logger.info("测试总结")
        logger.info("=" * 60)

        pass_count = sum(1 for r in self.results if r["status"] == "PASS")
        fail_count = sum(1 for r in self.results if r["status"] == "FAIL")
        warn_count = sum(1 for r in self.results if r["status"] == "WARN")

        logger.info(f"✅ 通过: {pass_count}")
        logger.info(f"❌ 失败: {fail_count}")
        logger.info(f"⚠️  警告: {warn_count}")
        logger.info(f"📊 总计: {len(self.results)}")

        # 按模块分组
        logger.info("\n详细结果:")
        modules = {}
        for r in self.results:
            module = r["module"]
            if module not in modules:
                modules[module] = []
            modules[module].append(r)

        for module, results in modules.items():
            logger.info(f"\n  [{module}]")
            for r in results:
                emoji = "✅" if r["status"] == "PASS" else "❌" if r["status"] == "FAIL" else "⚠️"
                logger.info(f"    {emoji} {r['action']}: {r['details']}")


def main():
    test = FullExperienceTest()
    test.run_all_tests()


if __name__ == "__main__":
    main()
