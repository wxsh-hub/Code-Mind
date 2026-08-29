"""
Ingest Client - 文档摄入客户端

将处理后的文档上传到 ragent 知识库进行分块和向量化
"""

import logging
import urllib.request
import urllib.error
import json
import tempfile
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    """摄入结果"""
    success: bool
    doc_id: Optional[str] = None
    kb_id: Optional[str] = None
    error: Optional[str] = None


class IngestClient:
    """文档摄入客户端 - 上传文档到 ragent"""

    def __init__(self, base_url: str = "http://localhost:9090/api/ragent",
                 token: Optional[str] = None):
        self.base_url = base_url
        self._token = token

    def set_token(self, token: str):
        """设置认证 token"""
        self._token = token

    def _request(self, method: str, path: str, data: Optional[dict] = None) -> dict:
        """发送 JSON 请求"""
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        if self._token:
            headers["Authorization"] = self._token

        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            logger.error(f"HTTP {e.code} from {url}: {body_text}")
            raise RuntimeError(f"HTTP {e.code}: {body_text}")

    def _upload_file(self, path: str, file_path: str,
                     extra_fields: Optional[Dict[str, str]] = None) -> dict:
        """上传文件（multipart/form-data）"""
        url = f"{self.base_url}{path}"

        # 构建 multipart body
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_parts = []

        # 添加文件
        with open(file_path, "rb") as f:
            file_data = f.read()

        filename = os.path.basename(file_path)
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode())
        body_parts.append(b"Content-Type: application/octet-stream")
        body_parts.append(b"")
        body_parts.append(file_data)

        # 添加额外字段
        if extra_fields:
            for key, value in extra_fields.items():
                body_parts.append(f"--{boundary}".encode())
                body_parts.append(f'Content-Disposition: form-data; name="{key}"'.encode())
                body_parts.append(b"")
                body_parts.append(value.encode("utf-8"))

        body_parts.append(f"--{boundary}--".encode())
        body = b"\r\n".join(body_parts)

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        if self._token:
            headers["Authorization"] = self._token

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            logger.error(f"Upload error {e.code}: {body_text}")
            raise RuntimeError(f"Upload failed: {body_text}")

    def upload_document(self, kb_id: str, content: str, filename: str,
                        source_type: str = "gitlab") -> IngestResult:
        """
        上传文档到知识库

        Args:
            kb_id: 知识库 ID
            content: 文档内容
            filename: 文件名
            source_type: 来源类型

        Returns:
            IngestResult
        """
        # 写入临时文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md",
                                          delete=False, encoding="utf-8") as f:
            f.write(content)
            temp_path = f.name

        try:
            # 上传文档
            resp = self._upload_file(
                f"/knowledge-base/{kb_id}/docs/upload",
                temp_path,
                extra_fields={"sourceType": source_type, "processMode": "chunk"},
            )

            doc_id = resp.get("data", {}).get("id")
            if doc_id:
                # 触发分块
                self._request("POST", f"/knowledge-base/docs/{doc_id}/chunk")
                logger.info(f"Uploaded and chunked document {doc_id} to KB {kb_id}")
                return IngestResult(success=True, doc_id=str(doc_id), kb_id=kb_id)
            else:
                return IngestResult(success=False, error="No doc_id in response")

        except Exception as e:
            logger.error(f"Failed to upload document: {e}")
            return IngestResult(success=False, error=str(e))
        finally:
            os.unlink(temp_path)

    def batch_upload(self, kb_id: str, documents: List[Dict[str, str]],
                     source_type: str = "gitlab") -> List[IngestResult]:
        """
        批量上传文档

        Args:
            kb_id: 知识库 ID
            documents: [{"content": "...", "filename": "..."}]
            source_type: 来源类型

        Returns:
            List[IngestResult]
        """
        results = []
        for doc in documents:
            result = self.upload_document(
                kb_id=kb_id,
                content=doc["content"],
                filename=doc["filename"],
                source_type=source_type,
            )
            results.append(result)
        return results
