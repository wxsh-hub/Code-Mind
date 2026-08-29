# F5 矛盾向量审核后台

## 目标
自动检测反义向量（矛盾），找出置信度相近的矛盾对，提供人工审核接口。

## 实现思路

### 1. 矛盾检测逻辑

在 conflict/detector.py 中增强：

```python
def detect_contradictions(self, kb_id: str, threshold: float = 0.2) -> List[dict]:
    """检测知识库中的矛盾向量

    Args:
        kb_id: 知识库 ID
        threshold: 置信度差异阈值（0.2 表示 20%）

    Returns:
        [
            {
                "chunk_a": {"id": "...", "content": "...", "confidence": 5},
                "chunk_b": {"id": "...", "content": "...", "confidence": 4},
                "confidence_diff": 0.2,
                "contradiction_type": "negation"
            }
        ]
    """
```

检测方法：
- 否定模式：应该 vs 不应该、启用 vs 禁用
- 语义对立：使用 A vs 使用 B（互斥方案）
- 置信度相近：差异 < 20%

### 2. 审核 API

在 KnowledgeChunkApiController 中新增：

```java
// 获取待审核的矛盾对
GET /knowledge-base/{kbId}/conflicts/pending

// 审核矛盾对
POST /knowledge-base/conflicts/review
Body: {
    "chunk_a_id": "...",
    "chunk_b_id": "...",
    "winner": "a",  // 或 "b" 或 "both"
    "reason": "..."
}
```

### 3. MCP Gateway 审核工具

```python
def list_conflicts_impl(project: str) -> dict:
    """列出待审核的矛盾对"""

def review_conflict_impl(project: str, chunk_a: str, chunk_b: str,
                         winner: str, reason: str) -> dict:
    """审核矛盾对

    Args:
        winner: "a" | "b" | "both"
        reason: 审核原因
    """
```

### 4. 审核后处理

- winner=a：废弃 chunk_b，置信度转移到 chunk_a
- winner=b：废弃 chunk_a，置信度转移到 chunk_b
- winner=both：保留两者，标记为"已审核，两者都有效"

## 测试脚本思路

### test_conflict_review.sh

```
1. 创建知识库
2. 上传两个矛盾文档：
   - "应该使用 Redis 缓存"
   - "不应该使用 Redis 缓存"
3. 等待分块
4. 调用 list_conflicts → 返回 1 个矛盾对
5. 调用 review_conflict(winner=a)
6. 验证 chunk_b 被废弃
7. 验证 chunk_a 置信度增加
```

### 单元测试

```python
class TestConflictReview:
    def test_detect_negation_contradiction(self):
        # 测试检测否定矛盾

    def test_detect_similar_confidence(self):
        # 测试置信度相近的矛盾对

    def test_review_winner_a(self):
        # 测试审核选择 a

    def test_review_winner_both(self):
        # 测试审核选择 both

    def test_list_pending_conflicts(self):
        # 测试列出待审核
```

## 依赖
- ragent 需要实现审核 API
- MCP Gateway 调用 ragent API
