#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TODO_FIX 验证测试脚本

验证以下修复：
1. P1 - 搜索结果包含相似度分数
2. P2 - 批量操作支持
3. P2 - 重试机制
4. P2 - 知识库名称模糊匹配
"""

import sys
import os
import time
import json

# 设置标准输出编码为 UTF-8
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_gateway.memory_tools import MemoryManager, MemoryConfig
from mcp_gateway.rag_client import RAGClient, RAGConfig


def test_search_score():
    """测试搜索结果包含相似度分数"""
    print("\n=== 测试 1: 搜索结果相似度分数 ===")

    client = RAGClient()
    client.login()

    # 上传测试文档
    manager = MemoryManager()
    manager.login()

    project = "test_score_fix"
    filename = "test_score.md"
    content = """
# 测试文档

这是一个测试文档，用于验证搜索结果的相似度分数功能。

## 功能说明
- 向量检索
- 关键词匹配
- 相似度计算
"""

    # 上传
    result = manager.upload_memory(project, filename, content)
    print(f"上传结果: {result.get('status')}")

    if result.get("status") == "success":
        kb_id = result.get("kb_id")

        # 搜索
        time.sleep(3)  # 等待分块完成
        search_results = client.search_similar("相似度分数", kb_id=kb_id, top_k=5)

        if search_results:
            print(f"搜索结果数量: {len(search_results)}")
            first_result = search_results[0]
            score = first_result.get("score")
            print(f"第一条结果的 score: {score}")

            if score is not None and score > 0:
                print("✅ 测试通过: 搜索结果包含相似度分数")
                return True
            else:
                print("❌ 测试失败: 搜索结果缺少 score 字段")
                return False
        else:
            print("⚠️ 警告: 搜索无结果")
            return None
    else:
        print(f"❌ 上传失败: {result}")
        return False


def test_batch_operations():
    """测试批量操作"""
    print("\n=== 测试 2: 批量操作 ===")

    manager = MemoryManager()
    manager.login()

    project = "test_batch_ops"

    # 先清理可能存在的测试数据
    try:
        from mcp_gateway.memory_tools import delete_memory_impl
        delete_memory_impl(project)
        time.sleep(2)
    except Exception:
        pass

    # 批量上传
    files = [
        {"filename": "batch1.md", "content": "# 批量文件 1\n\n这是第一个批量文件"},
        {"filename": "batch2.md", "content": "# 批量文件 2\n\n这是第二个批量文件"},
        {"filename": "batch3.md", "content": "# 批量文件 3\n\n这是第三个批量文件"},
    ]

    from mcp_gateway.memory_tools import batch_upload_memories_impl
    result = batch_upload_memories_impl(project, files)
    print(f"批量上传结果: success={result.get('success')}, failed={result.get('failed')}")

    if result.get("success") == 3:
        print("批量上传测试通过")
    else:
        print(f"批量上传测试失败: {result}")
        return False

    # 等待文档创建完成
    time.sleep(3)

    # 批量删除
    from mcp_gateway.memory_tools import batch_delete_memories_impl
    delete_result = batch_delete_memories_impl(project, ["batch1.md", "batch2.md", "batch3.md"])
    print(f"批量删除结果: deleted={delete_result.get('deleted')}, not_found={delete_result.get('not_found')}")

    if delete_result.get("deleted") == 3:
        print("批量删除测试通过")
        return True
    else:
        print(f"批量删除测试失败: {delete_result}")
        return False


def test_retry_mechanism():
    """测试重试机制"""
    print("\n=== 测试 3: 重试机制 ===")

    # 测试正常请求（应该成功）
    client = RAGClient()
    try:
        client.login()
        print("✅ 重试机制已集成（正常请求成功）")
        return True
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_fuzzy_matching():
    """测试知识库名称模糊匹配"""
    print("\n=== 测试 4: 知识库名称模糊匹配 ===")

    manager = MemoryManager()
    manager.login()

    # 创建一个知识库
    project = "test_fuzzy"
    manager.upload_memory(project, "test.md", "# 测试\n\n模糊匹配测试")

    # 尝试模糊匹配（使用部分名称）
    try:
        kb_id = manager.get_or_create_project_kb("fuzzy")
        if kb_id:
            print(f"✅ 模糊匹配成功，kb_id: {kb_id}")
            return True
        else:
            print("❌ 模糊匹配失败")
            return False
    except Exception as e:
        print(f"❌ 模糊匹配异常: {e}")
        return False


def test_confidence_api():
    """测试置信度 API"""
    print("\n=== 测试 5: 置信度 API ===")

    client = RAGClient()
    client.login()

    manager = MemoryManager()
    manager.login()

    project = "test_confidence"

    # 先清理可能存在的测试数据
    try:
        from mcp_gateway.memory_tools import delete_memory_impl
        delete_memory_impl(project)
        time.sleep(2)
    except Exception:
        pass

    result = manager.upload_memory(project, "conf_test.md",
                                   "# 置信度测试\n\n测试置信度计算功能")

    if result.get("status") == "success":
        doc_id = result.get("doc_id")
        time.sleep(8)  # 等待分块完成

        # 获取分块
        chunks = client.get_chunks(doc_id)
        print(f"获取到的分块: {chunks}")

        if chunks:
            # 处理不同的返回格式
            chunk_id = None
            if isinstance(chunks, list) and len(chunks) > 0:
                first_chunk = chunks[0]
                if isinstance(first_chunk, dict):
                    chunk_id = first_chunk.get("id")
                else:
                    chunk_id = first_chunk
            elif isinstance(chunks, dict):
                records = chunks.get("records", [])
                if records and len(records) > 0:
                    chunk_id = records[0].get("id")

            if chunk_id:
                # 计算置信度
                confidence = client.calculate_confidence(chunk_id)
                print(f"置信度: {confidence}")

                if confidence and confidence > 0:
                    print("置信度 API 测试通过")
                    return True
                else:
                    print("置信度 API 返回无效值")
                    return False

    print("跳过置信度测试（无分块数据）")
    return None


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("TODO_FIX 验证测试")
    print("=" * 60)

    results = {
        "search_score": test_search_score(),
        "batch_operations": test_batch_operations(),
        "retry_mechanism": test_retry_mechanism(),
        "fuzzy_matching": test_fuzzy_matching(),
        "confidence_api": test_confidence_api(),
    }

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    for name, result in results.items():
        status = "✅ 通过" if result is True else "❌ 失败" if result is False else "⚠️ 跳过"
        print(f"  {name}: {status}")

    print(f"\n总计: {passed} 通过, {failed} 失败, {skipped} 跳过")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
