import pytest
from mcp_gateway.conflict.resolver import ConflictResolver


class TestConflictResolver:
    @pytest.mark.asyncio
    async def test_resolve_same_file(self):
        resolver = ConflictResolver()
        new_chunk = {"metadata": {"file_hash": "abc"}}
        conflicts = [{
            "existing_metadata": {"file_hash": "abc", "version": 3},
            "conflicting_chunk": {"id": "chunk-1"},
        }]
        result = await resolver.resolve(new_chunk, conflicts)
        assert result["action"] == "replace_old"
        assert result["metadata_updates"]["version"] == 4

    @pytest.mark.asyncio
    async def test_resolve_different_file(self):
        resolver = ConflictResolver()
        new_chunk = {"metadata": {"file_hash": "aaa"}}
        conflicts = [{
            "existing_metadata": {"file_hash": "bbb"},
            "conflicting_chunk": {"id": "chunk-2"},
        }]
        result = await resolver.resolve(new_chunk, conflicts)
        assert result["action"] == "store_both"

    @pytest.mark.asyncio
    async def test_resolve_no_conflicts(self):
        resolver = ConflictResolver()
        result = await resolver.resolve({}, [])
        assert result["action"] == "store_new"
