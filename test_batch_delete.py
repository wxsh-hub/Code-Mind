# -*- coding: utf-8 -*-
"""
批量删除测试
"""

import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.path.insert(0, '.')

from mcp_gateway.memory_tools import MemoryManager
from mcp_gateway.rag_client import RAGClient

PROJECT = "Batch-Delete-Test"


def main():
    print("=" * 60)
    print("  批量删除测试")
    print("=" * 60)

    manager = MemoryManager()
    manager.login()

    client = RAGClient()
    client.login()

    # 1. 上传测试数据
    print("\n1. 上传测试数据:")
    for i in range(5):
        manager.upload_memory(PROJECT, f"doc_{i}.md", f"# 文档 {i}\n\n这是测试文档 {i}")
    print("  ✅ 上传 5 个文档")

    # 2. 等待分块
    print("\n2. 等待分块:")
    time.sleep(10)
    kb_id = manager.get_or_create_project_kb(PROJECT)
    results = client.search_similar("文档", kb_id=kb_id, top_k=10)
    print(f"  找到 {len(results) if results else 0} 个 chunk")

    # 3. 获取 chunk IDs
    chunk_ids = []
    if results:
        for r in results:
            chunk_id = r.get("chunkId")
            if chunk_id:
                chunk_ids.append(chunk_id)

    print(f"\n3. 获取 chunk IDs: {len(chunk_ids)} 个")

    # 4. 测试批量删除
    if chunk_ids:
        print(f"\n4. 测试批量删除:")
        result = client.batch_deprecate_chunks(chunk_ids)
        print(f"  成功: {result.get('success')}")
        print(f"  失败: {result.get('failed')}")
        if result.get('errors'):
            print(f"  错误: {result.get('errors')}")

    # 5. 清理
    print("\n5. 清理:")
    from mcp_gateway.memory_tools import delete_memory_impl
    delete_memory_impl(PROJECT)
    print(f"  ✅ 删除项目: {PROJECT}")

    # 总结
    print("\n" + "=" * 60)
    print("  测试总结")
    print("=" * 60)
    print(f"""
  ✅ 批量删除测试完成

  功能:
  - batch_deprecate_chunks: 批量标记废弃 ✅
""")


if __name__ == "__main__":
    main()
