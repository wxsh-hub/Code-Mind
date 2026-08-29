from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class ChunkMetadata:
    source: str           # "gitlab://project/docs/api-guide.md"
    file_hash: str        # 文件 SHA
    file_path: str        # 原始路径
    project: str          # 项目名
    branch: str           # 分支
    author: str           # 最后修改者
    last_modified: str    # 最后修改时间
    category: str         # standard / experience / ...
    long_term_value: float # 0-1
    tags: list[str] = field(default_factory=list)
    version: int = 1
    vote_count: int = 0
    deprecated: bool = False
    chunk_index: int = 0

    def to_dict(self) -> dict:
        return asdict(self)
