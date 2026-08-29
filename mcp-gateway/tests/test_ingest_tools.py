"""测试文档入库 MCP tools"""
import pytest
from mcp.server.fastmcp import FastMCP
from mcp_gateway.rag_client import RAGClient
from mcp_gateway.collector.slimmer import MDSlimmer
from mcp_gateway.conflict.detector import ConflictDetector
from mcp_gateway.conflict.resolver import ConflictResolver
from mcp_gateway.ingest_tools import register_ingest_tools, format_ingest_result


class TestFormatIngestResult:
    def test_success_result(self):
        result = {
            "success": True,
            "doc_id": "doc-123",
            "chunk_trigger": True,
            "conflict_action": "无冲突",
        }
        text = format_ingest_result(result)
        assert "成功" in text
        assert "doc-123" in text

    def test_failure_result(self):
        result = {"success": False, "errors": ["上传失败", "网络超时"]}
        text = format_ingest_result(result)
        assert "失败" in text
        assert "上传失败" in text


class TestRegisterIngestTools:
    def test_register_no_error(self):
        mcp = FastMCP("test")
        client = RAGClient(base_url="http://localhost:9090", token="test")
        slimmer = MDSlimmer()
        detector = ConflictDetector(rag_client=client)
        resolver = ConflictResolver()
        register_ingest_tools(mcp, client, slimmer, detector, resolver)
        # 注册成功不抛异常即可
