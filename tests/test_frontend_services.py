# -*- coding: utf-8 -*-
"""
前端服务测试

测试矛盾审核和智能问答的后端接口
"""

import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.path.insert(0, '.')

from mcp_gateway.memory_tools import MemoryManager
from mcp_gateway.rag_client import RAGClient
from mcp_gateway.rag_tools import search_experience_impl
from mcp_gateway.conflict_review import (
    list_conflicts_impl,
    review_conflict_impl,
    submit_conflict_for_review_impl,
)


def test_search_experience():
    """测试智能问答接口"""
    print("\n=== 测试智能问答接口 ===")

    # 上传测试数据
    manager = MemoryManager()
    manager.login()

    project = "Frontend-Test-QA"
    manager.upload_memory(project, "test.md", "# 测试文档\n\n这是一个测试文档，用于验证智能问答功能。")

    time.sleep(10)

    # 测试搜索
    result = search_experience_impl(query="测试文档")
    print(f"  状态: {result.get('status')}")
    print(f"  AI 回答: {result.get('ai_answer', '')[:100]}...")
    print(f"  结果数: {result.get('result_count')}")

    # 清理
    from mcp_gateway.memory_tools import delete_memory_impl
    delete_memory_impl(project)

    return result.get("status") == "success"


def test_list_conflicts():
    """测试列出矛盾对接口"""
    print("\n=== 测试列出矛盾对接口 ===")

    result = list_conflicts_impl("default", page=1, page_size=5)
    print(f"  状态: {result.get('status')}")
    print(f"  矛盾对数: {result.get('pagination', {}).get('total', 0)}")

    return result.get("status") == "success"


def test_submit_conflict():
    """测试提交矛盾对接口"""
    print("\n=== 测试提交矛盾对接口 ===")

    manager = MemoryManager()
    manager.login()

    project = "Frontend-Test-Conflict"
    manager.upload_memory(project, "author_a.md", "# 作者A建议\n\n推荐使用方案X")
    manager.upload_memory(project, "author_b.md", "# 作者B建议\n\n推荐使用方案Y")

    time.sleep(10)

    # 获取 chunk IDs
    client = RAGClient()
    client.login()
    kb_id = manager.get_or_create_project_kb(project)

    results = client.search_similar("推荐", kb_id=kb_id, top_k=5)
    if results and len(results) >= 2:
        chunk_a = results[0].get("chunkId")
        chunk_b = results[1].get("chunkId")

        result = submit_conflict_for_review_impl(
            project=project,
            chunk_a_id=chunk_a,
            chunk_b_id=chunk_b,
            reason="测试提交矛盾对",
            ai_analysis="作者A推荐方案X，作者B推荐方案Y",
        )
        print(f"  状态: {result.get('status')}")
        print(f"  消息: {result.get('message')}")

        # 清理
        from mcp_gateway.memory_tools import delete_memory_impl
        delete_memory_impl(project)

        return result.get("status") == "success"

    return False


def main():
    print("=" * 60)
    print("  前端服务测试")
    print("=" * 60)

    results = {
        "search_experience": test_search_experience(),
        "list_conflicts": test_list_conflicts(),
        "submit_conflict": test_submit_conflict(),
    }

    print("\n" + "=" * 60)
    print("  测试总结")
    print("=" * 60)

    for name, passed in results.items():
        icon = "✅" if passed else "❌"
        print(f"  {icon} {name}: {'PASS' if passed else 'FAIL'}")

    all_passed = all(results.values())
    print(f"\n  总计: {sum(results.values())}/{len(results)} 通过")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
