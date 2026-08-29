from mcp_gateway.collector.metadata import ChunkMetadata


def test_chunk_metadata_create():
    meta = ChunkMetadata(
        source="gitlab://proj/docs/api.md",
        file_hash="abc123",
        file_path="docs/api.md",
        project="my-project",
        branch="main",
        author="zhangsan",
        last_modified="2026-08-29T10:00:00Z",
        category="standard",
        long_term_value=0.9,
    )
    d = meta.to_dict()
    assert d["source"] == "gitlab://proj/docs/api.md"
    assert d["vote_count"] == 0
    assert d["deprecated"] is False


def test_metadata_json():
    import json
    meta = ChunkMetadata(
        source="test", file_hash="x", file_path="test.md",
        project="p", branch="main", author="a",
        last_modified="2026-01-01", category="experience",
        long_term_value=0.8,
    )
    json_str = json.dumps(meta.to_dict())
    assert "experience" in json_str
