import pytest
from mcp_gateway.conflict.voter import ConflictVoter


class TestConflictVoter:
    @pytest.mark.asyncio
    async def test_resolve_clear_winner(self):
        voter = ConflictVoter()
        voter._vote_counts = {"a": 100, "b": 10}
        result = await voter.resolve_by_vote("a", "b")
        assert result["action"] == "keep_winner"
        assert result["winner_id"] == "a"
        assert result["ratio"] == 10.0

    @pytest.mark.asyncio
    async def test_resolve_close_votes(self):
        voter = ConflictVoter()
        voter._vote_counts = {"a": 50, "b": 45}
        result = await voter.resolve_by_vote("a", "b")
        assert result["action"] == "keep_both"

    @pytest.mark.asyncio
    async def test_record_reference(self):
        voter = ConflictVoter()
        await voter.record_reference("chunk-1")
        await voter.record_reference("chunk-1")
        assert await voter.get_vote_score("chunk-1") == 2
