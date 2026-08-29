"""
Content Slimmer - 内容瘦身器

过滤短期价值内容，保留长期有价值的项目经验和规范
"""

import re
import logging
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SlimResult:
    """瘦身结果"""
    content: str
    removed_sections: List[str]
    original_length: int
    slimmed_length: int

    @property
    def reduction_ratio(self) -> float:
        if self.original_length == 0:
            return 0.0
        return 1 - (self.slimmed_length / self.original_length)


class ContentSlimmer:
    """内容瘦身器 - 过滤短期价值内容"""

    # 短期价值关键词（临时调试、hotfix、版本特定信息）
    SHORT_TERM_PATTERNS = [
        r"(?i)临时修复|hotfix|workaround|TODO|FIXME|HACK",
        r"(?i)调试|debug|临时|temporary",
        r"(?i)版本\s*\d+\.\d+\.\d+\s*(修复|补丁)",  # 特定版本修复
    ]

    # 长期价值关键词（架构、规范、最佳实践）
    LONG_TERM_KEYWORDS = [
        "架构", "设计模式", "规范", "最佳实践", "原则",
        "流程", "标准", "指南", "手册", "经验总结",
        "architecture", "pattern", "standard", "guide", "best practice",
    ]

    # 需要移除的章节标题模式
    REMOVE_SECTION_PATTERNS = [
        r"^#{1,3}\s*更新日志.*$",
        r"^#{1,3}\s*Change\s*Log.*$",
        r"^#{1,3}\s*已知问题.*$",
        r"^#{1,3}\s*临时.*$",
    ]

    def __init__(self, min_content_length: int = 50,
                 keep_short_term_threshold: float = 0.3):
        """
        Args:
            min_content_length: 最小内容长度（低于此值不过滤）
            keep_short_term_threshold: 短期价值内容保留比例（0-1）
        """
        self.min_content_length = min_content_length
        self.keep_short_term_threshold = keep_short_term_threshold

    def slim(self, content: str) -> SlimResult:
        """
        对内容进行瘦身

        Args:
            content: 原始 Markdown 内容

        Returns:
            SlimResult 瘦身结果
        """
        original_length = len(content)

        # 如果内容太短，不过滤
        if original_length < self.min_content_length:
            return SlimResult(
                content=content,
                removed_sections=[],
                original_length=original_length,
                slimmed_length=original_length,
            )

        # Step 1: 移除短期价值章节
        content, removed = self._remove_short_term_sections(content)

        # Step 2: 移除临时性代码块
        content, code_removed = self._remove_temp_code_blocks(content)
        removed.extend(code_removed)

        # Step 3: 清理空行和多余空格
        content = self._clean_whitespace(content)

        return SlimResult(
            content=content,
            removed_sections=removed,
            original_length=original_length,
            slimmed_length=len(content),
        )

    def _remove_short_term_sections(self, content: str) -> tuple:
        """移除短期价值章节"""
        removed = []
        lines = content.split("\n")
        result = []
        skip = False
        skip_level = 0

        for line in lines:
            # 检查是否是需要移除的章节
            should_remove = False
            for pattern in self.REMOVE_SECTION_PATTERNS:
                if re.match(pattern, line, re.IGNORECASE):
                    should_remove = True
                    break

            if should_remove:
                skip = True
                skip_level = self._get_heading_level(line)
                removed.append(line.strip())
                continue

            # 检查是否遇到同级或更高级标题（结束跳过）
            if skip:
                current_level = self._get_heading_level(line)
                if current_level > 0 and current_level <= skip_level:
                    skip = False
                else:
                    continue

            result.append(line)

        return "\n".join(result), removed

    def _remove_temp_code_blocks(self, content: str) -> tuple:
        """移除临时性代码块"""
        removed = []

        # 移除标记为临时的代码块
        pattern = r"```.*?(临时|temp|debug|hack).*?\n.*?```"
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        for match in matches:
            removed.append(match[:50] + "...")

        cleaned = re.sub(pattern, "", content, flags=re.DOTALL | re.IGNORECASE)
        return cleaned, removed

    def _clean_whitespace(self, content: str) -> str:
        """清理多余空行"""
        # 连续空行合并为两个
        cleaned = re.sub(r"\n{3,}", "\n\n", content)
        return cleaned.strip()

    def _get_heading_level(self, line: str) -> int:
        """获取标题级别"""
        match = re.match(r"^(#{1,6})\s", line)
        return len(match.group(1)) if match else 0

    def is_long_term_valuable(self, content: str) -> bool:
        """判断内容是否具有长期价值"""
        content_lower = content.lower()
        matches = sum(1 for kw in self.LONG_TERM_KEYWORDS if kw in content_lower)
        return matches >= 2  # 至少匹配 2 个长期价值关键词
