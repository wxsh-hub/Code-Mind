"""
Skill Tools 测试
"""

import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from mcp_gateway.skill_tools import (
    SkillStore, Skill, SkillMetadata,
    upload_skill_impl, search_skill_impl, list_skills_impl, get_skill_impl,
    set_store,
)


class TestSkillStore(unittest.TestCase):
    """SkillStore 单元测试"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.store = SkillStore(base_dir=self.test_dir)
        self.store._token = "test-token"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_skill_dir(self):
        """测试获取技能目录"""
        skill_dir = self.store._get_skill_dir("TestProject", "coding")
        self.assertTrue(skill_dir.exists())
        self.assertEqual(skill_dir.name, "coding")

    def test_build_skill_content(self):
        """测试构建技能内容"""
        skill = Skill(
            metadata=SkillMetadata(
                name="Java Naming",
                category="coding",
                tags=["java", "naming"],
                description="Java naming conventions",
                author="team",
            ),
            content="Use PascalCase for classes.",
        )

        content = self.store._build_skill_content(skill)
        self.assertIn("# Java Naming", content)
        self.assertIn("## Description", content)
        self.assertIn("## Metadata", content)
        self.assertIn("## Content", content)
        self.assertIn("Use PascalCase", content)

    def test_parse_skill_content(self):
        """测试解析技能内容"""
        content = """# Java Naming

## Description
Java naming conventions

## Metadata
- **Category**: coding
- **Tags**: java, naming
- **Version**: 1.0
- **Author**: team

## Content

Use PascalCase for classes.
"""
        skill = self.store._parse_skill_content(content, "test.md")
        self.assertEqual(skill.metadata.name, "Java Naming")
        self.assertEqual(skill.metadata.category, "coding")
        self.assertIn("java", skill.metadata.tags)
        self.assertIn("PascalCase", skill.content)

    @patch("urllib.request.urlopen")
    def test_upload_skill_local(self, mock_urlopen):
        """测试上传技能到本地"""
        # Mock list KB
        list_resp = MagicMock()
        list_resp.read.return_value = json.dumps({
            "code": "0",
            "data": [{"id": 100, "name": "skills_TestProject"}],
        }).encode("utf-8")
        list_resp.__enter__ = lambda s: s
        list_resp.__exit__ = MagicMock(return_value=False)

        # Mock upload
        upload_resp = MagicMock()
        upload_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {"id": 200},
        }).encode("utf-8")
        upload_resp.__enter__ = lambda s: s
        upload_resp.__exit__ = MagicMock(return_value=False)

        # Mock chunk
        chunk_resp = MagicMock()
        chunk_resp.read.return_value = json.dumps({"code": "0"}).encode("utf-8")
        chunk_resp.__enter__ = lambda s: s
        chunk_resp.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [list_resp, upload_resp, chunk_resp]

        result = self.store.upload_skill(
            project="TestProject",
            skill_name="Git Commit",
            content="Use conventional commits.",
            category="coding",
            tags=["git", "commit"],
            description="Git commit conventions",
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["project"], "TestProject")
        self.assertEqual(result["skill_name"], "Git Commit")
        self.assertTrue(os.path.exists(result["local_path"]))

    def test_list_skills(self):
        """测试列出技能"""
        # 上传两个技能
        self.store.upload_skill("TestProject", "Skill1", "Content1", "coding")
        self.store.upload_skill("TestProject", "Skill2", "Content2", "testing")

        result = self.store.list_skills("TestProject")
        self.assertEqual(result["count"], 2)
        self.assertEqual(len(result["skills"]), 2)

    def test_get_skill(self):
        """测试获取技能"""
        self.store.upload_skill(
            "TestProject", "TestSkill", "Test content", "coding",
            description="Test description"
        )

        result = self.store.get_skill("TestProject", "TestSkill")
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "TestSkill")
        self.assertEqual(result["category"], "coding")

    def test_get_skill_not_found(self):
        """测试获取不存在的技能"""
        result = self.store.get_skill("TestProject", "NonExistent")
        self.assertIsNone(result)

    @patch("urllib.request.urlopen")
    def test_search_skill(self, mock_urlopen):
        """测试搜索技能"""
        # Mock login
        login_resp = MagicMock()
        login_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {"token": "test-token"},
        }).encode("utf-8")
        login_resp.__enter__ = lambda s: s
        login_resp.__exit__ = MagicMock(return_value=False)

        # Mock list KB
        list_resp = MagicMock()
        list_resp.read.return_value = json.dumps({
            "code": "0",
            "data": [{"id": 100, "name": "skills_TestProject"}],
        }).encode("utf-8")
        list_resp.__enter__ = lambda s: s
        list_resp.__exit__ = MagicMock(return_value=False)

        # Mock search
        search_resp = MagicMock()
        search_resp.read.return_value = json.dumps({
            "code": "0",
            "data": [
                {"chunkId": "1", "content": "Use PascalCase", "metadata": {}},
            ],
        }).encode("utf-8")
        search_resp.__enter__ = lambda s: s
        search_resp.__exit__ = MagicMock(return_value=False)

        # Mock reference
        ref_resp = MagicMock()
        ref_resp.read.return_value = json.dumps({"code": "0"}).encode("utf-8")
        ref_resp.__enter__ = lambda s: s
        ref_resp.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [login_resp, list_resp, search_resp, ref_resp]

        store = SkillStore(base_dir=self.test_dir)
        result = store.search_skill("TestProject", "naming conventions")

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["project"], "TestProject")


class TestSkillToolsImpl(unittest.TestCase):
    """Skill Tools 实现测试"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.mock_store = SkillStore(base_dir=self.test_dir)
        self.mock_store._token = "test-token"  # 预设 token
        set_store(self.mock_store)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("urllib.request.urlopen")
    def test_upload_skill_impl(self, mock_urlopen):
        """测试 upload_skill_impl"""
        # Mock list KB
        list_resp = MagicMock()
        list_resp.read.return_value = json.dumps({
            "code": "0",
            "data": [{"id": 100, "name": "skills_TestProject"}],
        }).encode("utf-8")
        list_resp.__enter__ = lambda s: s
        list_resp.__exit__ = MagicMock(return_value=False)

        # Mock upload
        upload_resp = MagicMock()
        upload_resp.read.return_value = json.dumps({
            "code": "0",
            "data": {"id": 200},
        }).encode("utf-8")
        upload_resp.__enter__ = lambda s: s
        upload_resp.__exit__ = MagicMock(return_value=False)

        # Mock chunk
        chunk_resp = MagicMock()
        chunk_resp.read.return_value = json.dumps({"code": "0"}).encode("utf-8")
        chunk_resp.__enter__ = lambda s: s
        chunk_resp.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [list_resp, upload_resp, chunk_resp]

        result = upload_skill_impl(
            "TestProject", "TestSkill", "Content",
            category="coding", tags=["test"]
        )
        self.assertEqual(result["status"], "success")

    def test_list_skills_impl(self):
        """测试 list_skills_impl"""
        upload_skill_impl("TestProject", "Skill1", "Content1", "coding")
        upload_skill_impl("TestProject", "Skill2", "Content2", "testing")

        result = list_skills_impl("TestProject")
        self.assertEqual(result["count"], 2)

    def test_get_skill_impl(self):
        """测试 get_skill_impl"""
        upload_skill_impl("TestProject", "TestSkill", "Content", "coding")

        result = get_skill_impl("TestProject", "TestSkill")
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "TestSkill")

    def test_get_skill_impl_not_found(self):
        """测试获取不存在的技能"""
        result = get_skill_impl("TestProject", "NonExistent")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
