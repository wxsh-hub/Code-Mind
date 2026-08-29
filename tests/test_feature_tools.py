"""
Feature Tools 测试
"""

import unittest
from unittest.mock import MagicMock
from mcp_gateway.feature_tools import (
    create_module_impl, list_modules_impl, delete_module_impl,
    create_feature_impl, list_features_impl, delete_feature_impl,
    set_client,
)
from mcp_gateway.rag_client import RAGClient


class TestFeatureTools(unittest.TestCase):
    """Feature Tools 单元测试"""

    def setUp(self):
        self.mock_client = MagicMock(spec=RAGClient)
        self.mock_client.ensure_logged_in = MagicMock()
        set_client(self.mock_client)

    def test_create_module(self):
        """测试创建模块"""
        self.mock_client.create_module.return_value = {"id": "1", "name": "user"}

        result = create_module_impl("TestProject", "user", "用户管理模块")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["module"], "user")
        self.mock_client.create_module.assert_called_once_with("user", "用户管理模块")

    def test_list_modules(self):
        """测试列出模块"""
        self.mock_client.list_modules.return_value = [
            {"name": "user", "description": "用户模块"},
            {"name": "order", "description": "订单模块"},
        ]

        result = list_modules_impl("TestProject")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["count"], 2)

    def test_delete_module(self):
        """测试删除模块"""
        self.mock_client.delete_module.return_value = {
            "deleted_chunks": 50,
            "deleted_features": 3,
        }

        result = delete_module_impl("TestProject", "user")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["deleted_chunks"], 50)
        self.assertEqual(result["deleted_features"], 3)

    def test_create_feature(self):
        """测试创建功能"""
        self.mock_client.create_feature.return_value = {
            "id": "1",
            "featureCode": "2437",
            "featureName": "人员管理",
        }

        result = create_feature_impl("TestProject", "2437", "人员管理", "user", "管理用户")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["feature_code"], "2437")
        self.assertEqual(result["module"], "user")
        self.mock_client.create_feature.assert_called_once_with("2437", "人员管理", "user", "管理用户")

    def test_list_features(self):
        """测试列出功能"""
        self.mock_client.list_features.return_value = [
            {"featureCode": "2437", "featureName": "人员管理"},
            {"featureCode": "2438", "featureName": "权限管理"},
        ]

        result = list_features_impl("TestProject")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["count"], 2)

    def test_list_features_by_module(self):
        """测试按模块列出功能"""
        self.mock_client.list_features.return_value = [
            {"featureCode": "2437", "featureName": "人员管理"},
        ]

        result = list_features_impl("TestProject", module="user")

        self.assertEqual(result["status"], "success")
        self.mock_client.list_features.assert_called_once_with("user")

    def test_delete_feature(self):
        """测试删除功能"""
        self.mock_client.delete_feature.return_value = {"deleted_chunks": 15}

        result = delete_feature_impl("TestProject", "2437")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["feature_code"], "2437")
        self.assertEqual(result["deleted_chunks"], 15)

    def test_create_module_error(self):
        """测试创建模块失败"""
        self.mock_client.create_module.side_effect = RuntimeError("Module already exists")

        result = create_module_impl("TestProject", "user")

        self.assertEqual(result["status"], "error")
        self.assertIn("Module already exists", result["error"])

    def test_delete_feature_error(self):
        """测试删除功能失败"""
        self.mock_client.delete_feature.side_effect = RuntimeError("Feature not found")

        result = delete_feature_impl("TestProject", "9999")

        self.assertEqual(result["status"], "error")
        self.assertIn("Feature not found", result["error"])


if __name__ == "__main__":
    unittest.main()
