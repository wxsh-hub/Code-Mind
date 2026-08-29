from mcp.server.fastmcp import FastMCP
from mcp_gateway.rag_client import RAGClient
from mcp_gateway.rag_tools import register_rag_tools
from mcp_gateway.conflict.voter import ConflictVoter


def test_tool_registered():
    mcp = FastMCP("test")
    client = RAGClient(base_url="http://localhost:9090", token="test")
    register_rag_tools(mcp, client)
    # 注册成功不抛异常即可


def test_tool_registered_with_voter():
    mcp = FastMCP("test")
    client = RAGClient(base_url="http://localhost:9090", token="test")
    voter = ConflictVoter(rag_client=client)
    register_rag_tools(mcp, client, voter=voter)
    # 注册成功不抛异常即可
