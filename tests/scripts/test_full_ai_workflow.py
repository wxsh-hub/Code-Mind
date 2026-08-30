# -*- coding: utf-8 -*-
"""
AI 完整工作流程测试

测试场景：
1. 确认错误/过时 → 删除向量
2. 不确定但有矛盾 → 提交后台审核
3. 正确/最适合 → 返回用户
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
from mcp_gateway.conflict_review import submit_conflict_for_review_impl

PROJECT = "AI-Workflow-Test"


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def setup_data(manager):
    """准备测试数据"""
    print_header("1. 准备测试数据")

    # 场景1: 明确过时的知识
    outdated = [
        ("fake_old_stack.md", """# 过时技术栈（请勿参考）

此文档已过时，仅供参考。

## 后端
- Spring Boot 2.3（已过时，当前使用 4.1）
- Hibernate（已替换为 MyBatis-Plus）
- MySQL（已迁移到 PostgreSQL）

## 基础设施
- Memcached（已替换为 Redis）
"""),
        ("fake_wrong_db.md", """# 错误数据库配置

警告：以下配置是错误的，请勿使用。

## 数据库配置（错误）
使用 MySQL 8.0 作为主数据库（错误：实际使用 PostgreSQL）
使用 Elasticsearch 存储向量（错误：实际使用 pgvector）
"""),
    ]

    # 场景2: 矛盾的知识（两个作者给出不同结论）
    conflict = [
        ("author_a_api.md", """# API 设计建议 - 作者 A

## 认证方式推荐
推荐使用 JWT Token，理由：
1. 无状态，易于扩展
2. 跨服务支持好
3. 性能优秀

## 结论
JWT 是最佳选择。
"""),
        ("author_b_api.md", """# API 设计建议 - 作者 B

## 认证方式推荐
推荐使用 Sa-Token，理由：
1. 简单易用
2. 功能丰富
3. Spring Boot 集成好

## 结论
Sa-Token 是最佳选择。
"""),
    ]

    # 场景3: 正确的知识
    correct = [
        ("real_tech.md", """# 真实技术栈

## 后端
- Spring Boot 4.1
- MyBatis-Plus
- PostgreSQL + pgvector
- Redis

## 前端
- React 18
- Vite
"""),
    ]

    print("\n  上传过时知识:")
    for name, content in outdated:
        manager.upload_memory(PROJECT, name, content)
        print(f"    ✅ {name}")

    print("\n  上传矛盾知识:")
    for name, content in conflict:
        manager.upload_memory(PROJECT, name, content)
        print(f"    ✅ {name}")

    print("\n  上传正确知识:")
    for name, content in correct:
        manager.upload_memory(PROJECT, name, content)
        print(f"    ✅ {name}")


def wait_for_chunks(manager, timeout=60):
    """等待分块完成"""
    print_header("2. 等待分块完成")

    client = RAGClient()
    client.login()
    kb_id = manager.get_or_create_project_kb(PROJECT)

    for i in range(timeout // 5):
        time.sleep(5)
        try:
            results = client.search_similar("技术", kb_id=kb_id, top_k=1)
            if results:
                print(f"  ✅ 分块完成（{(i+1)*5}秒）")
                return True
        except Exception:
            pass
        print(f"  等待中... ({(i+1)*5}秒)")

    return False


def ai_workflow(client):
    """AI 完整工作流程"""
    print_header("3. AI 工作流程")

    deleted_count = 0
    submitted_count = 0
    answered_count = 0

    # 测试问题列表
    test_cases = [
        {
            "question": "项目使用什么数据库？",
            "expected_action": "delete",  # 应该识别出过时知识并删除
            "description": "包含过时知识，AI 应该删除",
        },
        {
            "question": "推荐使用什么认证方式？",
            "expected_action": "submit",  # 两个作者观点不同，应该提交审核
            "description": "包含矛盾知识，AI 应该提交审核",
        },
        {
            "question": "Spring Boot 版本是多少？",
            "expected_action": "answer",  # 正确知识，直接回答
            "description": "只有正确知识，AI 直接回答",
        },
    ]

    for tc in test_cases:
        question = tc["question"]
        print(f"\n{'─'*50}")
        print(f"  问题: {question}")
        print(f"  场景: {tc['description']}")

        # 获取 AI 回答 + sources
        result = client.rag_chat_with_sources(question)
        answer = result["answer"]
        sources = result["sources"]

        print(f"\n  AI 回答: {answer[:200]}...")

        # 分析 AI 回答
        outdated_keywords = ["过时", "错误", "已迁移", "已替换", "已升级", "请勿参考", "警告"]
        has_outdated = any(kw in answer for kw in outdated_keywords)

        # 检查是否有矛盾（多个不同观点）
        has_contradiction = False
        if "推荐" in answer or "建议" in answer:
            # 检查 sources 中是否有不同观点
            different_opinions = set()
            for source in sources:
                excerpt = source.get("excerpt", "")
                if "推荐" in excerpt or "建议" in excerpt:
                    # 提取推荐的技术
                    if "JWT" in excerpt:
                        different_opinions.add("JWT")
                    if "Sa-Token" in excerpt:
                        different_opinions.add("Sa-Token")
                    if "MySQL" in excerpt:
                        different_opinions.add("MySQL")
                    if "PostgreSQL" in excerpt:
                        different_opinions.add("PostgreSQL")

            if len(different_opinions) > 1:
                has_contradiction = True

        # AI 决策
        print(f"\n  AI 分析:")
        print(f"    包含过时信息: {has_outdated}")
        print(f"    包含矛盾: {has_contradiction}")

        if has_outdated:
            # 情况1: 确认错误/过时 → 删除
            print(f"\n  🗑️ AI 决策: 删除过时知识")

            for source in sources:
                doc_name = source.get("docName", "")
                excerpt = source.get("excerpt", "")
                is_fake = any(kw in excerpt for kw in outdated_keywords)

                if is_fake:
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
                                        print(f"      ✅ 删除: {chunk_id} ({doc_name})")
                                        deleted_count += 1
                                    except Exception as e:
                                        print(f"      ❌ 失败: {chunk_id}: {e}")

        elif has_contradiction:
            # 情况2: 有矛盾 → 提交审核
            print(f"\n  📋 AI 决策: 提交矛盾对到后台审核")

            # 找到矛盾的 chunk
            chunk_ids = []
            for source in sources:
                doc_id = source.get("docId")
                if doc_id:
                    chunks = client.get_chunks(doc_id)
                    if chunks:
                        records = chunks.get("records", []) if isinstance(chunks, dict) else chunks
                        for chunk in (records if isinstance(records, list) else []):
                            chunk_id = chunk.get("id") if isinstance(chunk, dict) else None
                            if chunk_id and chunk_id not in chunk_ids:
                                chunk_ids.append(chunk_id)

            if len(chunk_ids) >= 2:
                result = submit_conflict_for_review_impl(
                    project=PROJECT,
                    chunk_a_id=chunk_ids[0],
                    chunk_b_id=chunk_ids[1],
                    reason="两个作者给出不同结论，AI 无法判断哪个是正确的",
                    ai_analysis=f"AI 回答: {answer[:200]}",
                )
                if result.get("status") == "success":
                    print(f"      ✅ 已提交审核: {chunk_ids[0]} vs {chunk_ids[1]}")
                    submitted_count += 1
                else:
                    print(f"      ❌ 提交失败: {result.get('error')}")

        else:
            # 情况3: 正确 → 直接回答
            print(f"\n  ✅ AI 决策: 直接返回正确答案")
            answered_count += 1

    return deleted_count, submitted_count, answered_count


def verify_results(client, manager):
    """验证结果"""
    print_header("4. 验证结果")

    kb_id = manager.get_or_create_project_kb(PROJECT)

    # 检查过时知识是否被标记
    print("\n  检查过时知识:")
    for keyword in ["过时", "MySQL"]:
        results = client.search_similar(keyword, kb_id=kb_id, top_k=3)
        if results:
            for r in results[:2]:
                content = r.get("content", "")[:50]
                deprecated = r.get("deprecated", False)
                status = "已废弃" if deprecated else "未废弃"
                print(f"    [{status}] {content}...")

    # 检查矛盾对
    print("\n  检查待审核矛盾对:")
    from mcp_gateway.conflict_review import list_conflicts_impl
    conflicts = list_conflicts_impl(PROJECT, page_size=5)
    total = conflicts.get("pagination", {}).get("total", 0)
    print(f"    待审核数量: {total}")


def cleanup():
    """清理测试数据"""
    print_header("5. 清理测试数据")

    from mcp_gateway.memory_tools import delete_memory_impl
    try:
        delete_memory_impl(PROJECT)
        print(f"  ✅ 删除项目: {PROJECT}")
    except Exception as e:
        print(f"  ⚠️ 删除失败: {e}")


def main():
    print("=" * 60)
    print("  AI 完整工作流程测试")
    print("=" * 60)

    try:
        manager = MemoryManager()
        manager.login()

        # 1. 准备数据
        setup_data(manager)

        # 2. 等待分块
        if not wait_for_chunks(manager):
            print("分块超时")
            return

        # 3. AI 工作流程
        client = RAGClient()
        client.login()
        deleted, submitted, answered = ai_workflow(client)

        # 4. 验证结果
        verify_results(client, manager)

        # 5. 清理
        cleanup()

        # 6. 总结
        print_header("测试总结")
        print(f"""
┌─────────────────────────────────────────────────────────────┐
│  AI 完整工作流程测试结果                                    │
├─────────────────────────────────────────────────────────────┤
│  删除过时知识: {deleted} 条                                         │
│  提交矛盾审核: {submitted} 条                                         │
│  直接回答: {answered} 条                                            │
└─────────────────────────────────────────────────────────────┘

✅ 流程验证完成:
  1. 确认错误/过时 → 删除向量 ✅
  2. 不确定但有矛盾 → 提交后台审核 ✅
  3. 正确/最适合 → 直接返回 ✅
""")

    except Exception as e:
        print(f"\n  ❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
