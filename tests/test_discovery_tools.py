"""
Discovery Tools 测试
"""

import unittest
from mcp_gateway.discovery_tools import list_mcp_tools_impl, TOOL_CATEGORIES


class TestDiscoveryTools(unittest.TestCase):
    """Discovery Tools 单元测试"""

    def test_list_tools_categorized(self):
        """测试按分类列出工具"""
        result = list_mcp_tools_impl(categorized=True)

        self.assertIn("tools", result)
        self.assertIn("categories", result)
        self.assertIn("total_count", result)
        self.assertGreater(result["total_count"], 0)

    def test_list_tools_not_categorized(self):
        """测试不按分类列出工具"""
        result = list_mcp_tools_impl(categorized=False)

        self.assertIn("tools", result)
        self.assertIn("total_count", result)
        self.assertNotIn("categories", result)

    def test_tools_have_required_fields(self):
        """测试工具包含必需字段"""
        result = list_mcp_tools_impl()

        for tool in result["tools"]:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("category", tool)
            self.assertIn("parameters", tool)

    def test_categories_exist(self):
        """测试分类存在"""
        result = list_mcp_tools_impl(categorized=True)

        self.assertIn("module_management", result["categories"])
        self.assertIn("feature_management", result["categories"])
        self.assertIn("memory_management", result["categories"])
        self.assertIn("skill_management", result["categories"])

    def test_module_management_tools(self):
        """测试模块管理工具"""
        result = list_mcp_tools_impl(categorized=True)
        module_tools = result["categories"]["module_management"]["tools"]

        tool_names = [t["name"] for t in module_tools]
        self.assertIn("create_module", tool_names)
        self.assertIn("list_modules", tool_names)
        self.assertIn("delete_module", tool_names)

    def test_feature_management_tools(self):
        """测试功能管理工具"""
        result = list_mcp_tools_impl(categorized=True)
        feature_tools = result["categories"]["feature_management"]["tools"]

        tool_names = [t["name"] for t in feature_tools]
        self.assertIn("create_feature", tool_names)
        self.assertIn("list_features", tool_names)
        self.assertIn("delete_feature", tool_names)

    def test_memory_management_tools(self):
        """测试记忆管理工具"""
        result = list_mcp_tools_impl(categorized=True)
        memory_tools = result["categories"]["memory_management"]["tools"]

        tool_names = [t["name"] for t in memory_tools]
        self.assertIn("upload_memory", tool_names)
        self.assertIn("ask_project", tool_names)
        self.assertIn("delete_memory", tool_names)

    def test_skill_management_tools(self):
        """测试技能管理工具"""
        result = list_mcp_tools_impl(categorized=True)
        skill_tools = result["categories"]["skill_management"]["tools"]

        tool_names = [t["name"] for t in skill_tools]
        self.assertIn("upload_skill", tool_names)
        self.assertIn("search_skill", tool_names)
        self.assertIn("delete_skill", tool_names)

    def test_tool_parameters_format(self):
        """测试工具参数格式"""
        result = list_mcp_tools_impl()

        for tool in result["tools"]:
            params = tool["parameters"]
            for param_name, param_info in params.items():
                self.assertIn("type", param_info)
                self.assertIn("required", param_info)
                self.assertIn("description", param_info)


if __name__ == "__main__":
    unittest.main()
