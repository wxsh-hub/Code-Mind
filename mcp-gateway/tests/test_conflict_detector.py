import pytest
from mcp_gateway.conflict.detector import ConflictDetector


class TestConflictDetector:
    def test_init(self):
        detector = ConflictDetector(rag_client=None)
        assert detector is not None

    @pytest.mark.asyncio
    async def test_judge_default_no_contradiction(self):
        detector = ConflictDetector(rag_client=None)
        result = await detector.judge_contradiction(
            "接口必须返回 Result 对象",
            "Result 对象包含 code、message、data"
        )
        assert "is_contradiction" in result
        assert "relationship" in result
