import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class KnowledgeIngester:
    """将处理后的 chunk 入库到 ragent 的知识库"""

    def __init__(self, rag_api_url: str, token: str):
        self.rag_api_url = rag_api_url.rstrip("/")
        self.token = token

    async def ingest_chunks(self, kb_id: str, doc_name: str,
                             chunks: list[dict]) -> dict:
        """将 chunks 作为文档上传到 ragent 知识库

        流程：
        1. 将 chunks 合并为一个 MD 文件
        2. 调用 ragent 的文档上传接口
        3. 触发分块
        """
        # 合并 chunks 为 MD 文件
        content = "\n\n".join(c["text"] for c in chunks)

        async with httpx.AsyncClient(timeout=60) as client:
            # 上传文档
            files = {"file": (f"{doc_name}.md", content.encode("utf-8"), "text/markdown")}
            resp = await client.post(
                f"{self.rag_api_url}/api/ragent/knowledge-base/{kb_id}/docs/upload",
                headers={"Authorization": self.token},
                files=files,
                data={"sourceType": "file", "processMode": "chunk"},
            )
            resp.raise_for_status()
            result = resp.json()

            if result.get("code") != "0":
                logger.error("Upload failed: %s", result.get("message"))
                return {"success": 0, "failed": len(chunks), "errors": [result.get("message")]}

            doc_id = result["data"]["id"]

            # 触发分块
            chunk_resp = await client.post(
                f"{self.rag_api_url}/api/ragent/knowledge-base/docs/{doc_id}/chunk",
                headers={"Authorization": self.token},
            )
            chunk_result = chunk_resp.json()

            return {
                "success": 1,
                "failed": 0,
                "doc_id": doc_id,
                "chunk_trigger": chunk_result.get("code") == "0",
            }

    async def mark_deprecated(self, doc_id: str) -> bool:
        """禁用文档"""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.patch(
                f"{self.rag_api_url}/api/ragent/knowledge-base/docs/{doc_id}/enable",
                headers={"Authorization": self.token},
                params={"value": "false"},
            )
            return resp.json().get("code") == "0"
