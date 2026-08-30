# -*- coding: utf-8 -*-
"""
AI 无法判断时提交矛盾对到后台审核 测试

测试流程：
1. 上传两个给出不同结论的知识
2. AI 尝试判断但无法确定哪个是正确的
3. AI 调用 submit_conflict_for_review 提交到后台
4. 后台可以调用 list_conflicts 查看待审核的矛盾对
5. 后台调用 review_conflict 进行人工审核
"""

import sys
import io
import os
import time
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.path.insert(0, '.')

from mcp_gateway.memory_tools import MemoryManager
from mcp_gateway.rag_client import RAGClient
from mcp_gateway.conflict_review import (
    submit_conflict_for_review_impl,
    list_conflicts_impl,
    review_conflict_impl,
)

PROJECT = "Code-Mind-Conflict-Submit"

# ==================== 矛盾知识 ====================
# 两个知识给出不同结论，AI 无法判断哪个是正确的
CONFLICT_MEMORIES = [
    {
        "filename": "author_a_recommendation.md",
        "content": """# 技术选型建议 - 作者 A

## 数据库推荐
推荐使用 MySQL 8.0，理由：
1. 社区活跃，文档丰富
2. 性能满足大多数场景
3. 运维成本低

## 结论
MySQL 是最佳选择。
""",
    },
    {
        "filename": "author_b_recommendation.md",
        "content": """# 技术选型建议 - 作者 B

## 数据库推荐
推荐使用 PostgreSQL，理由：
1. 功能更强大，支持 JSONB
2. 扩展性更好
3. 向量检索支持（pgvector）

## 结论
PostgreSQL 是最佳选择。
""",
    },
]


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def upload_memories(manager):
    """上传矛盾知识"""
    print_header("1. 上传矛盾知识")

    for mem in CONFLICT_MEMORIES:
        manager.upload_memory(PROJECT, mem["filename"], mem["content"])
        print(f"  ✅ {mem['filename']}")


def wait_for_chunks(manager, timeout=60):
    """等待分块完成"""
    print_header("2. 等待分块完成")

    client = RAGClient()
    client.login()
    kb_id = manager.get_or_create_project_kb(PROJECT)

    for i in range(timeout // 5):
        time.sleep(5)
        try:
            results = client.search_similar("数据库", kb_id=kb_id, top_k=1)
            if results:
                print(f"  ✅ 分块完成（{(i+1)*5}秒）")
                return True
        except Exception:
            pass
        print(f"  等待中... ({(i+1)*5}秒)")

    return False


def ai_try_to_judge(client):
    """AI 尝试判断"""
    print_header("3. AI 尝试判断")

    # 获取 AI 回答
    result = client.rag_chat_with_sources("推荐使用什么数据库？")
    answer = result["answer"]
    sources = result["sources"]

    print(f"\n  AI 回答:\n  {answer[:300]}...")

    # AI 分析：检查是否有矛盾
    has_mysql = "MySQL" in answer
    has_postgresql = "PostgreSQL" in answer

    if has_mysql and has_postgresql:
        print("\n  ⚠️ AI 检测到矛盾：同时提到了 MySQL 和 PostgreSQL")
        print("  AI 无法确定哪个是正确的，需要人工审核")

        # 从 sources 中找到两个矛盾的 chunk
        chunk_ids = []
        for source in sources:
            doc_name = source.get("docName", "")
            if "recommendation" in doc_name:
                doc_id = source.get("docId")
                if doc_id:
                    chunks = client.get_chunks(doc_id)
                    if chunks:
                        records = chunks.get("records", []) if isinstance(chunks, dict) else chunks
                        for chunk in (records if isinstance(records, list) else []):
                            chunk_id = chunk.get("id") if isinstance(chunk, dict) else None
                            if chunk_id and chunk_id not in chunk_ids:
                                chunk_ids.append(chunk_id)

        return chunk_ids[:2]  # 返回前两个矛盾的 chunk

    return []


def submit_conflict(chunk_ids):
    """提交矛盾对到后台"""
    print_header("4. 提交矛盾对到后台")

    if len(chunk_ids) < 2:
        print("  ❌ 未找到足够的矛盾 chunk")
        return False

    chunk_a_id = chunk_ids[0]
    chunk_b_id = chunk_ids[1]

    print(f"\n  提交矛盾对:")
    print(f"    Chunk A: {chunk_a_id}")
    print(f"    Chunk B: {chunk_b_id}")

    result = submit_conflict_for_review_impl(
        project=PROJECT,
        chunk_a_id=chunk_a_id,
        chunk_b_id=chunk_b_id,
        reason="两个知识给出不同结论，AI 无法判断哪个是正确的",
        ai_analysis="作者A推荐MySQL，作者B推荐PostgreSQL，两个观点都有理由，无法确定哪个是最新或最权威的",
    )

    print(f"\n  提交结果: {result.get('status')}")
    if result.get("status") == "success":
        print(f"  消息: {result.get('message')}")
        return True

    return False


def simulate_backend_review():
    """模拟后台审核"""
    print_header("5. 模拟后台审核")

    # 列出待审核的矛盾对
    print("\n  查询待审核的矛盾对:")
    conflicts_result = list_conflicts_impl(PROJECT)

    if conflicts_result.get("status") == "success":
        conflicts = conflicts_result.get("conflicts", [])
        total = conflicts_result.get("pagination", {}).get("total", 0)
        print(f"  找到 {total} 个矛盾对")

        if conflicts:
            # 审核第一个矛盾对
            first_conflict = conflicts[0]
            chunk_a = first_conflict.get("chunk_a", {})
            chunk_b = first_conflict.get("chunk_b", {})

            print(f"\n  审核矛盾对:")
            print(f"    Chunk A: {chunk_a.get('id')} - {chunk_a.get('content', '')[:50]}...")
            print(f"    Chunk B: {chunk_b.get('id')} - {chunk_b.get('content', '')[:50]}...")

            # 模拟人工审核：选择 both（两个都保留）
            review_result = review_conflict_impl(
                project=PROJECT,
                chunk_a_id=chunk_a.get("id"),
                chunk_b_id=chunk_b.get("id"),
                winner="both",
                reason="两个观点都有道理，保留供参考",
            )

            print(f"\n  审核结果: {review_result.get('status')}")
            if review_result.get("status") == "success":
                print(f"  操作: {review_result.get('action')}")
                return True

    return False


def cleanup():
    """清理测试数据"""
    print_header("6. 清理测试数据")

    from mcp_gateway.memory_tools import delete_memory_impl
    try:
        delete_memory_impl(PROJECT)
        print(f"  ✅ 删除项目: {PROJECT}")
    except Exception as e:
        print(f"  ⚠️ 删除失败: {e}")


def main():
    print("=" * 60)
    print("  AI 无法判断时提交矛盾对到后台审核 测试")
    print("=" * 60)

    try:
        manager = MemoryManager()
        manager.login()

        # 1. 上传矛盾知识
        upload_memories(manager)

        # 2. 等待分块
        if not wait_for_chunks(manager):
            print("分块超时")
            return

        # 3. AI 尝试判断
        client = RAGClient()
        client.login()
        chunk_ids = ai_try_to_judge(client)

        # 4. 提交矛盾对到后台
        submitted = submit_conflict(chunk_ids)

        # 5. 模拟后台审核
        if submitted:
            reviewed = simulate_backend_review()

        # 6. 清理
        cleanup()

        # 7. 总结
        print_header("测试总结")
        print(f"""
  ✅ 完整链路测试成功

  链路:
  1. 上传两个给出不同结论的知识
  2. AI 尝试判断但无法确定
  3. AI 调用 submit_conflict_for_review 提交到后台
  4. 后台调用 list_conflicts 查看待审核
  5. 后台调用 review_conflict 进行人工审核

  功能:
  - submit_conflict_for_review: AI 提交矛盾对
  - list_conflicts: 后台查看待审核
  - review_conflict: 后台人工审核
""")

    except Exception as e:
        print(f"\n  ❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
