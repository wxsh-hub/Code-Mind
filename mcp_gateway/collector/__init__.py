# Collector 模块 - GitLab/GitHub 文档采集
from mcp_gateway.collector.gitlab_fetcher import GitLabFetcher
from mcp_gateway.collector.github_fetcher import GitHubFetcher, fetch_github_repo
from mcp_gateway.collector.slimmer import ContentSlimmer
from mcp_gateway.collector.metadata_extractor import MetadataExtractor
from mcp_gateway.collector.ingest_client import IngestClient
from mcp_gateway.collector.scheduler import CollectionScheduler
