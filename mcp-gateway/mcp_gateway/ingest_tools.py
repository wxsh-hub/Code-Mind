"""文档入库 MCP tools：将 Markdown 内容通过瘦身 + 冲突检测后入库"""
import logging
from mcp.server.fastmcp import FastMCP
from mcp_gateway.rag_client import RAGClient
from mcp_gateway.collector.slimmer import MDSlimmer
from mcp_gateway.collector.metadata import ChunkMetadata
from mcp_gateway.conflict.detector import ConflictDetector
from mcp_gateway.conflict.resolver import ConflictResolver

logger = logging.getLogger(__name__)


def format_ingest_result(result: dict) -> str:
    """格式化入库结果"""
    if result.get("success"):
        return (
            f"入库成功。\n"
            f"  文档ID: {result.get('doc_id', '未知')}\n"
            f"  分块触发: {'是' if result.get('chunk_trigger') else '否'}\n"
            f"  冲突处理: {result.get('conflict_action', '无')}"
        )
    errors = result.get("errors", ["未知错误"])
    return f"入库失败: {'; '.join(errors)}"


def register_ingest_tools(
    mcp: FastMCP,
    rag_client: RAGClient,
    slimmer: MDSlimmer,
    conflict_detector: ConflictDetector,
    conflict_resolver: ConflictResolver,
):
    """注册文档入库相关的 MCP tools"""

    @mcp.tool()
    async def ingest_document(
        content: str,
        doc_name: str,
        kb_id: str,
        source: str = "",
    ) -> str:
        """将 Markdown 文档入库到知识库

        流程：瘦身（过滤短期内容）→ 冲突检测 → 入库。
        适用于手动提交经验文档、踩坑记录等。

        Args:
            content: Markdown 格式的文档内容
            doc_name: 文档名称，如 "spring-boot-api规范"
            kb_id: 目标知识库 ID
            source: 来源标识，如 "gitlab://project/docs/api.md"
        """
        try:
            # 1. 瘦身
            chunks = await slimmer.slim(content, doc_name)
            if not chunks:
                return "瘦身后无有效内容，跳过入库。"

            # 2. 冲突检测
            conflict_action = "无冲突"
            for chunk in chunks:
                similar = await conflict_detector.find_similar_chunks(
                    chunk["text"], top_k=3
                )
                if similar:
                    for existing in similar:
                        judgment = await conflict_detector.judge_contradiction(
                            chunk["text"], existing.get("excerpt", "")
                        )
                        if judgment.get("is_contradiction"):
                            resolution = await conflict_resolver.resolve(
                                {"metadata": {"file_hash": source}},
                                [{"existing_metadata": existing, "conflicting_chunk": existing}],
                            )
                            conflict_action = resolution.get("action", "unknown")
                            logger.info(
                                "Conflict detected: %s -> %s",
                                judgment.get("reason"), conflict_action,
                            )

            # 3. 入库
            merged_content = "\n\n".join(c["text"] for c in chunks)
            upload_resp = await rag_client.upload_document(
                kb_id=kb_id,
                doc_name=doc_name,
                content=merged_content.encode("utf-8"),
                filename=f"{doc_name}.md",
            )

            if upload_resp.get("code") != "0":
                return format_ingest_result({
                    "success": False,
                    "errors": [upload_resp.get("message", "上传失败")],
                })

            doc_id = upload_resp["data"]["id"]

            # 4. 触发分块
            chunk_resp = await rag_client.trigger_chunk(doc_id)

            return format_ingest_result({
                "success": True,
                "doc_id": doc_id,
                "chunk_trigger": chunk_resp.get("code") == "0",
                "conflict_action": conflict_action,
            })

        except Exception as e:
            logger.error("Ingest failed: %s", e, exc_info=True)
            return format_ingest_result({"success": False, "errors": [str(e)]})
