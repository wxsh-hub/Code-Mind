import pytest
from mcp_gateway.collector.slimmer import MDSlimmer


class TestMDSlimmer:
    def test_split_markdown(self):
        slimmer = MDSlimmer()
        md = "# 标题1\n内容1\n\n## 标题2\n内容2"
        chunks = slimmer._split_markdown(md)
        assert len(chunks) >= 1

    @pytest.mark.asyncio
    async def test_classify_default(self):
        slimmer = MDSlimmer()
        result = await slimmer.classify_chunk("所有接口必须返回Result对象", "api.md")
        assert "category" in result
        assert "long_term_value" in result

    @pytest.mark.asyncio
    async def test_slim_no_llm(self):
        slimmer = MDSlimmer()
        md = "# 规范\n所有接口必须返回Result对象\n\n# 临时记录\n2024-03-15 重启服务器"
        chunks = await slimmer.slim(md, "mixed.md")
        assert isinstance(chunks, list)
