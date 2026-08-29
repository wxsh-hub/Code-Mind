import pytest
from mcp_gateway.conflict.aware_search import ConflictAwareSearcher
from mcp_gateway.conflict.voter import ConflictVoter


class TestConflictAwareSearcher:
    @pytest.mark.asyncio
    async def test_search_no_conflicts(self):
        class MockRAG:
            async def search(self, q, top_k=5):
                return [{"id": "1", "content": "规范A", "metadata": {}}]

        searcher = ConflictAwareSearcher(rag_client=MockRAG(), voter=ConflictVoter())
        result = await searcher.search("测试")
        assert "results" in result
        assert "conflicts" in result
        assert len(result["conflicts"]) == 0

    @pytest.mark.asyncio
    async def test_search_with_conflict_pair(self):
        class MockRAG:
            async def search(self, q, top_k=5):
                return [
                    {"id": "a", "content": "A", "metadata": {"conflict_pair_id": "b"}},
                    {"id": "b", "content": "B", "metadata": {"conflict_pair_id": "a"}},
                ]

        searcher = ConflictAwareSearcher(rag_client=MockRAG(), voter=ConflictVoter())
        result = await searcher.search("测试")
        assert len(result["conflicts"]) > 0
