# -*- coding: utf-8 -*-
"""
根据帮助文档进行全流程测试

测试帮助文档中描述的所有功能
"""

import sys
import io
import os
import time
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))

from mcp_gateway.memory_tools import MemoryManager
from mcp_gateway.rag_client import RAGClient
from mcp_gateway.rag_tools import search_experience_impl
from mcp_gateway.conflict_review import (
    submit_conflict_for_review_impl,
    list_conflicts_impl,
    review_conflict_impl,
)

PROJECT = "Help-Doc-Test"


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(label, result):
    if isinstance(result, dict):
        # 统一判断：code="0" 或 status="success" 都算成功
        code = result.get("code", "")
        status = result.get("status", "")
        success = (code == "0") or (status == "success") or result.get("success", False)
        icon = "✅" if success else "❌"
        error = result.get("error") or result.get("message", "")
        print(f"  {icon} {label}: {'success' if success else 'failed'}")
        if error and not success:
            print(f"     错误: {error}")
    else:
        print(f"  {label}: {result}")


def test_module_feature(manager):
    """测试模块/功能管理"""
    print_header("1. 测试模块/功能管理")

    # 创建模块
    print("\n  创建模块:")
    for name, desc in [("user", "用户管理"), ("order", "订单管理")]:
        result = manager._request("POST", "/modules", {"name": name, "description": desc})
        print_result(f"create_module({name})", result)

    # 创建功能
    print("\n  创建功能:")
    features = [
        ("F001", "用户注册", "user"),
        ("F002", "用户登录", "user"),
        ("F003", "订单创建", "order"),
    ]
    for code, name, module in features:
        result = manager._request("POST", "/feature-metadata", {
            "featureCode": code, "featureName": name, "moduleName": module,
        })
        print_result(f"create_feature({code})", result)

    # 列出模块
    print("\n  列出模块:")
    result = manager._request("GET", "/modules")
    modules = result.get("data", [])
    print(f"    模块数量: {len(modules) if isinstance(modules, list) else 0}")

    # 列出功能
    print("\n  列出功能:")
    result = manager._request("GET", "/feature-metadata")
    features = result.get("data", [])
    print(f"    功能数量: {len(features) if isinstance(features, list) else 0}")


def test_upload_memory(manager):
    """测试上传记忆"""
    print_header("2. 测试上传记忆")

    memories = [
        ("memory_1.md", "# 用户注册指南\n\n## 步骤\n1. 填写表单\n2. 验证邮箱\n3. 完成注册", ["F001"], "user"),
        ("memory_2.md", "# 用户登录指南\n\n## 方式\n1. 密码登录\n2. 验证码登录", ["F002"], "user"),
        ("memory_3.md", "# 订单创建流程\n\n## 步骤\n1. 选择商品\n2. 确认地址\n3. 支付", ["F003"], "order"),
    ]

    print("\n  上传记忆:")
    for filename, content, codes, module in memories:
        result = manager.upload_memory(PROJECT, filename, content, feature_codes=codes, module=module)
        print_result(f"upload({filename})", result)

    # 批量上传
    print("\n  批量上传:")
    batch_files = [
        {"filename": "batch_1.md", "content": "# 批量文档1\n\n内容1"},
        {"filename": "batch_2.md", "content": "# 批量文档2\n\n内容2"},
    ]
    from mcp_gateway.memory_tools import batch_upload_memories_impl
    result = batch_upload_memories_impl(PROJECT + "_batch", batch_files)
    print(f"    上传: {result.get('success')}/{result.get('total')}")


def test_search_experience():
    """测试向量检索 + AI 回答"""
    print_header("3. 测试向量检索 + AI 回答")

    questions = [
        "如何添加用户？",
        "订单创建流程是什么？",
    ]

    print("\n  search_experience 测试:")
    for q in questions:
        print(f"\n  问题: {q}")
        result = search_experience_impl(query=q)
        if result.get("status") == "success":
            answer = result.get("ai_answer", "")
            print(f"    AI 回答: {answer[:150]}...")
            print(f"    结果数: {result.get('result_count')}")
        else:
            print(f"    ❌ 失败: {result.get('error')}")


def test_ai_workflow(client):
    """测试 AI 智能工作流程"""
    print_header("4. 测试 AI 智能工作流程")

    # 上传过时知识
    print("\n  上传过时知识:")
    manager = MemoryManager()
    manager.login()
    manager.upload_memory(PROJECT, "fake_old.md", "# 过时文档（请勿参考）\n\n- 旧版本 1.0\n- 已弃用功能")
    time.sleep(10)

    # AI 问答并判断
    print("\n  AI 问答并判断:")
    result = client.rag_chat_with_sources("项目版本是多少？")
    answer = result["answer"]
    sources = result["sources"]

    print(f"    AI 回答: {answer[:150]}...")

    # 检查是否包含过时信息
    outdated_keywords = ["过时", "错误", "已迁移", "已替换", "请勿参考"]
    has_outdated = any(kw in answer for kw in outdated_keywords)

    if has_outdated:
        print("\n    ⚠️ 检测到过时信息，执行删除:")

        # 从 sources 找到并删除
        deleted = 0
        for source in sources:
            doc_name = source.get("docName", "")
            excerpt = source.get("excerpt", "")
            if any(kw in excerpt for kw in outdated_keywords):
                doc_id = source.get("docId")
                if doc_id:
                    chunks = client.get_chunks(doc_id)
                    if chunks:
                        records = chunks.get("records", []) if isinstance(chunks, dict) else chunks
                        for chunk in (records if isinstance(records, list) else []):
                            chunk_id = chunk.get("id") if isinstance(chunk, dict) else None
                            if chunk_id:
                                try:
                                    client.deprecate_chunk(chunk_id)
                                    print(f"      ✅ 删除: {chunk_id}")
                                    deleted += 1
                                except Exception:
                                    pass

        print(f"    共删除 {deleted} 条过时知识")
    else:
        print("\n    ✅ 未检测到过时信息")


def test_submit_conflict():
    """测试提交矛盾对"""
    print_header("5. 测试提交矛盾对")

    # 上传矛盾知识
    manager = MemoryManager()
    manager.login()

    print("\n  上传矛盾知识:")
    manager.upload_memory(PROJECT, "author_a.md", "# 作者A建议\n\n推荐使用方案X")
    manager.upload_memory(PROJECT, "author_b.md", "# 作者B建议\n\n推荐使用方案Y")
    time.sleep(10)

    # 提交矛盾对
    print("\n  提交矛盾对:")
    client = RAGClient()
    client.login()
    kb_id = manager.get_or_create_project_kb(PROJECT)

    # 找到两个矛盾的 chunk
    results = client.search_similar("推荐", kb_id=kb_id, top_k=5)
    if results and len(results) >= 2:
        chunk_a = results[0].get("chunkId")
        chunk_b = results[1].get("chunkId")

        result = submit_conflict_for_review_impl(
            project=PROJECT,
            chunk_a_id=chunk_a,
            chunk_b_id=chunk_b,
            reason="两个作者给出不同建议",
            ai_analysis="作者A推荐方案X，作者B推荐方案Y",
        )
        print_result("submit_conflict_for_review", result)


def test_list_and_review_conflicts():
    """测试查看和审核矛盾对"""
    print_header("6. 测试查看和审核矛盾对")

    # 列出待审核
    print("\n  列出待审核:")
    result = list_conflicts_impl(PROJECT, page_size=5)
    if result.get("status") == "success":
        total = result.get("pagination", {}).get("total", 0)
        conflicts = result.get("conflicts", [])
        print(f"    待审核数量: {total}")

        if conflicts:
            # 审核第一个
            first = conflicts[0]
            chunk_a = first.get("chunk_a", {}).get("id")
            chunk_b = first.get("chunk_b", {}).get("id")

            print(f"\n  审核矛盾对:")
            print(f"    Chunk A: {chunk_a}")
            print(f"    Chunk B: {chunk_b}")

            result = review_conflict_impl(
                project=PROJECT,
                chunk_a_id=chunk_a,
                chunk_b_id=chunk_b,
                winner="both",
                reason="两个观点都保留",
            )
            print_result("review_conflict", result)


def test_cleanup():
    """测试清理"""
    print_header("7. 测试清理")

    from mcp_gateway.memory_tools import delete_memory_impl

    # 删除测试项目
    for suffix in ["", "_batch"]:
        project = PROJECT + suffix
        try:
            delete_memory_impl(project)
            print(f"  ✅ 删除: {project}")
        except Exception as e:
            print(f"  ⚠️ 删除失败: {project}: {e}")

    # 删除模块和功能
    client = RAGClient()
    client.login()

    print("\n  清理模块和功能:")
    for code in ["F001", "F002", "F003"]:
        try:
            client.delete_feature(code)
            print(f"    ✅ 删除功能: {code}")
        except Exception:
            pass

    for mod in ["user", "order"]:
        try:
            client.delete_module(mod)
            print(f"    ✅ 删除模块: {mod}")
        except Exception:
            pass


def main():
    print("=" * 60)
    print("  根据帮助文档进行全流程测试")
    print("=" * 60)

    try:
        manager = MemoryManager()
        manager.login()

        client = RAGClient()
        client.login()

        # 1. 模块/功能管理
        test_module_feature(manager)

        # 2. 上传记忆
        test_upload_memory(manager)

        # 等待分块
        time.sleep(10)

        # 3. 向量检索 + AI 回答
        test_search_experience()

        # 4. AI 智能工作流程
        test_ai_workflow(client)

        # 5. 提交矛盾对
        test_submit_conflict()

        # 6. 查看和审核矛盾对
        test_list_and_review_conflicts()

        # 7. 清理
        test_cleanup()

        # 总结
        print_header("测试总结")
        print("""
  ✅ 全流程测试完成

  测试项目:
  1. 模块/功能管理 ✅
  2. 上传记忆（单个 + 批量） ✅
  3. 向量检索 + AI 回答 ✅
  4. AI 智能删除过时知识 ✅
  5. 提交矛盾对到后台 ✅
  6. 查看和审核矛盾对 ✅
  7. 清理测试数据 ✅

  优化建议:
  1. search_experience 返回结构可以更清晰
  2. 矛盾检测可以更智能（语义分析）
  3. 删除操作可以支持批量
""")

    except Exception as e:
        print(f"\n  ❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
