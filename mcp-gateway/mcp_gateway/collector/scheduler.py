"""
Collection Scheduler - 采集调度器

定时从 GitLab 拉取文档，处理后上传到 ragent
"""

import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from mcp_gateway.collector.gitlab_fetcher import GitLabFetcher, GitLabConfig, FetchedFile
from mcp_gateway.collector.slimmer import ContentSlimmer
from mcp_gateway.collector.metadata_extractor import MetadataExtractor, DocumentMetadata
from mcp_gateway.collector.ingest_client import IngestClient

logger = logging.getLogger(__name__)


@dataclass
class CollectionJob:
    """采集任务配置"""
    job_id: str
    project_ids: List[str]
    kb_id: str
    path_pattern: str = ""
    branch: str = "main"
    interval_seconds: int = 3600  # 默认 1 小时
    enabled: bool = True


@dataclass
class CollectionStatus:
    """采集状态"""
    job_id: str
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    files_collected: int = 0
    files_slimmed: int = 0
    files_uploaded: int = 0
    errors: List[str] = field(default_factory=list)
    running: bool = False


class CollectionScheduler:
    """采集调度器"""

    def __init__(self, gitlab_config: GitLabConfig,
                 ingest_client: IngestClient,
                 slimmer: Optional[ContentSlimmer] = None,
                 metadata_extractor: Optional[MetadataExtractor] = None):
        self.fetcher = GitLabFetcher(gitlab_config)
        self.ingest_client = ingest_client
        self.slimmer = slimmer or ContentSlimmer()
        self.metadata_extractor = metadata_extractor or MetadataExtractor()

        self._jobs: Dict[str, CollectionJob] = {}
        self._status: Dict[str, CollectionStatus] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def add_job(self, job: CollectionJob):
        """添加采集任务"""
        self._jobs[job.job_id] = job
        self._status[job.job_id] = CollectionStatus(job_id=job.job_id)
        logger.info(f"Added collection job: {job.job_id}")

    def remove_job(self, job_id: str):
        """移除采集任务"""
        self._jobs.pop(job_id, None)
        self._status.pop(job_id, None)
        logger.info(f"Removed collection job: {job_id}")

    def get_status(self, job_id: Optional[str] = None) -> Dict[str, CollectionStatus]:
        """获取采集状态"""
        if job_id:
            status = self._status.get(job_id)
            return {job_id: status} if status else {}
        return dict(self._status)

    def run_once(self, job_id: str) -> CollectionStatus:
        """执行一次采集任务"""
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        status = self._status[job_id]
        status.running = True
        status.last_run = datetime.now().isoformat()
        status.errors = []

        try:
            # Step 1: 从 GitLab 获取文件
            logger.info(f"[{job_id}] Fetching files from projects: {job.project_ids}")
            files = self.fetcher.fetch_multiple_projects(
                project_ids=job.project_ids,
                path=job.path_pattern,
                ref=job.branch,
            )
            status.files_collected = len(files)

            # Step 2: 瘦身处理
            slimmed_docs = []
            for f in files:
                try:
                    slim_result = self.slimmer.slim(f.content)
                    if slim_result.slimmed_length > 0:
                        metadata = self.metadata_extractor.extract_from_content(
                            f.content, f.path, f.project_id, f.branch
                        )
                        slimmed_docs.append({
                            "content": slim_result.content,
                            "filename": f.path.split("/")[-1],
                            "metadata": metadata,
                            "reduction": slim_result.reduction_ratio,
                        })
                except Exception as e:
                    status.errors.append(f"Slim error for {f.path}: {e}")

            status.files_slimmed = len(slimmed_docs)

            # Step 3: 上传到 ragent
            for doc in slimmed_docs:
                try:
                    result = self.ingest_client.upload_document(
                        kb_id=job.kb_id,
                        content=doc["content"],
                        filename=doc["filename"],
                        source_type="gitlab",
                    )
                    if result.success:
                        status.files_uploaded += 1
                    else:
                        status.errors.append(f"Upload failed: {result.error}")
                except Exception as e:
                    status.errors.append(f"Upload error: {e}")

            logger.info(
                f"[{job_id}] Collection complete: "
                f"{status.files_collected} fetched, "
                f"{status.files_slimmed} slimmed, "
                f"{status.files_uploaded} uploaded"
            )

        except Exception as e:
            status.errors.append(f"Job error: {e}")
            logger.error(f"[{job_id}] Collection failed: {e}")
        finally:
            status.running = False

        return status

    def start(self):
        """启动定时调度"""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._schedule_loop, daemon=True)
        self._thread.start()
        logger.info("Collection scheduler started")

    def stop(self):
        """停止调度"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Collection scheduler stopped")

    def _schedule_loop(self):
        """调度循环"""
        last_run_times: Dict[str, float] = {}

        while self._running:
            now = time.time()
            for job_id, job in self._jobs.items():
                if not job.enabled:
                    continue

                last_run = last_run_times.get(job_id, 0)
                if now - last_run >= job.interval_seconds:
                    try:
                        self.run_once(job_id)
                        last_run_times[job_id] = now
                    except Exception as e:
                        logger.error(f"Scheduled run failed for {job_id}: {e}")

            time.sleep(10)  # 每 10 秒检查一次
