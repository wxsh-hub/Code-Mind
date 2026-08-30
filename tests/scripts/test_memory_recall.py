# -*- coding: utf-8 -*-
"""
持久化记忆召回测试脚本

测试目标：
1. 上传项目持久化记忆到 RAG
2. 测试短关键词搜索召回率
3. 测试贴近内容问题搜索召回率
4. 对比改动前后的效果

提交的持久化记忆：
- MEMORY.md: 项目总览（功能、技术栈、目录结构、MCP 工具清单）
- QUICK_START.md: 快速入门指南
- integration-design.md: 集成设计状态
- mcp-gateway-status.md: MCP Gateway 模块状态
- mcp-gateway-files.md: 文件位置索引
- chunk-api-status.md: Chunk API 状态
- metadata-status.md: 元数据标记系统状态
- rag-status.md: RAG 模块状态
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

PROJECT = "Code-Mind-Recall-Test"

# ==================== 持久化记忆文件清单 ====================
MEMORY_FILES = [
    "MEMORY.md",
    "QUICK_START.md",
    "integration-design.md",
    "mcp-gateway-status.md",
    "mcp-gateway-files.md",
    "chunk-api-status.md",
    "metadata-status.md",
    "rag-status.md",
]

# ==================== 测试问题 ====================
# 短关键词：直接从内容中提取的关键词
SHORT_KEYWORD_TESTS = [
    {"keyword": "MCP", "expect_in": ["MCP", "mcp"], "source": "MEMORY.md"},
    {"keyword": "RAG", "expect_in": ["RAG", "rag"], "source": "MEMORY.md/rag-status.md"},
    {"keyword": "pgvector", "expect_in": ["pgvector"], "source": "MEMORY.md"},
    {"keyword": "Redis", "expect_in": ["Redis", "redis"], "source": "MEMORY.md"},
    {"keyword": "RocketMQ", "expect_in": ["RocketMQ"], "source": "MEMORY.md"},
    {"keyword": "置信度", "expect_in": ["置信度", "confidence"], "source": "chunk-api-status.md"},
    {"keyword": "向量", "expect_in": ["向量", "vector"], "source": "MEMORY.md"},
    {"keyword": "矛盾", "expect_in": ["矛盾", "conflict"], "source": "MEMORY.md"},
    {"keyword": "模块", "expect_in": ["模块", "module"], "source": "metadata-status.md"},
    {"keyword": "功能", "expect_in": ["功能", "feature"], "source": "metadata-status.md"},
]

# 贴近内容问题：模拟用户实际提问
CONTENT_BASED_TESTS = [
    {"question": "集成设计", "expect_keywords": ["集成", "设计", "架构"], "source": "integration-design.md"},
    {"question": "Chunk API", "expect_keywords": ["chunk", "API"], "source": "chunk-api-status.md"},
    {"question": "MCP Gateway", "expect_keywords": ["MCP", "Gateway"], "source": "mcp-gateway-status.md"},
    {"question": "文件位置", "expect_keywords": ["文件", "位置"], "source": "mcp-gateway-files.md"},
    {"question": "metadata", "expect_keywords": ["metadata", "元数据"], "source": "metadata-status.md"},
    {"question": "快速入门", "expect_keywords": ["快速", "入门", "开始"], "source": "QUICK_START.md"},
    {"question": "RAG 状态", "expect_keywords": ["RAG", "状态"], "source": "rag-status.md"},
    {"question": "技术栈", "expect_keywords": ["技术", "Spring", "Java"], "source": "MEMORY.md"},
    {"question": "MCP 工具", "expect_keywords": ["MCP", "工具"], "source": "MEMORY.md"},
    {"question": "数据库表", "expect_keywords": ["数据库", "表"], "source": "MEMORY.md"},
]


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def upload_memories(manager):
    """上传持久化记忆"""
    print_header("1. 上传持久化记忆")

    memory_dir = os.path.join(os.path.dirname(__file__), "docs", "memory")
    if not os.path.exists(memory_dir):
        print(f"  ❌ 记忆目录不存在: {memory_dir}")
        return False

    uploaded = 0
    for filename in MEMORY_FILES:
        filepath = os.path.join(memory_dir, filename)
        if not os.path.exists(filepath):
            print(f"  ⚠️ 文件不存在: {filename}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        result = manager.upload_memory(PROJECT, filename, content)
        status = result.get("status", "unknown")
        icon = "✅" if status == "success" else "❌"
        print(f"  {icon} {filename} ({len(content)} 字符)")
        uploaded += 1

    print(f"\n  共上传 {uploaded}/{len(MEMORY_FILES)} 个文件")
    return uploaded > 0


def wait_for_chunks(manager, timeout=60):
    """等待分块完成"""
    print_header("2. 等待分块完成")

    client = RAGClient()
    client.login()
    kb_id = manager.get_or_create_project_kb(PROJECT)

    for i in range(timeout // 5):
        time.sleep(5)
        try:
            results = client.search_similar("MCP", kb_id=kb_id, top_k=1)
            if results:
                print(f"  ✅ 分块完成（{(i+1)*5}秒）")
                return True
        except Exception:
            pass
        print(f"  等待中... ({(i+1)*5}秒)")

    print("  ❌ 等待超时")
    return False


def test_short_keywords(manager):
    """测试短关键词搜索"""
    print_header("3. 短关键词测试")

    passed = 0
    failed = 0
    results = []

    for tc in SHORT_KEYWORD_TESTS:
        keyword = tc["keyword"]
        expect = tc["expect_in"]

        result = manager.ask_project(PROJECT, keyword, top_k=3)
        search_results = result.get("results", [])

        if search_results:
            content = search_results[0].get("content", "")
            hit = any(e.lower() in content.lower() for e in expect)
            if hit:
                print(f"  ✅ \"{keyword}\" → 命中 (来源: {tc['source']})")
                passed += 1
                results.append({"keyword": keyword, "status": "PASS", "found": True})
            else:
                print(f"  ⚠️ \"{keyword}\" → 找到结果但未命中期望关键词")
                failed += 1
                results.append({"keyword": keyword, "status": "PARTIAL", "found": True})
        else:
            print(f"  ❌ \"{keyword}\" → 未找到结果")
            failed += 1
            results.append({"keyword": keyword, "status": "FAIL", "found": False})

    print(f"\n  短关键词测试: {passed}/{len(SHORT_KEYWORD_TESTS)} 通过")
    return results, passed, failed


def test_content_based(manager):
    """测试贴近内容问题"""
    print_header("4. 贴近内容问题测试")

    passed = 0
    failed = 0
    results = []

    for tc in CONTENT_BASED_TESTS:
        question = tc["question"]
        expect = tc["expect_keywords"]

        result = manager.ask_project(PROJECT, question, top_k=3)
        search_results = result.get("results", [])
        level = result.get("level", "?")

        if search_results:
            content = search_results[0].get("content", "")
            hits = [e for e in expect if e.lower() in content.lower()]
            hit_rate = len(hits) / len(expect) if expect else 0

            if hit_rate > 0:
                print(f"  ✅ \"{question}\" → 命中 {hits} ({hit_rate:.0%}) [级别: {level}]")
                passed += 1
                results.append({"question": question, "status": "PASS", "hit_rate": hit_rate})
            else:
                print(f"  ⚠️ \"{question}\" → 找到结果但未命中关键词 [级别: {level}]")
                failed += 1
                results.append({"question": question, "status": "PARTIAL", "hit_rate": 0})
        else:
            print(f"  ❌ \"{question}\" → 未找到结果")
            failed += 1
            results.append({"question": question, "status": "FAIL", "hit_rate": 0})

    print(f"\n  贴近内容问题测试: {passed}/{len(CONTENT_BASED_TESTS)} 通过")
    return results, passed, failed


def cleanup(manager):
    """清理测试数据"""
    print_header("5. 清理测试数据")

    from mcp_gateway.memory_tools import delete_memory_impl
    try:
        result = delete_memory_impl(PROJECT)
        print(f"  ✅ 删除项目: {PROJECT}")
    except Exception as e:
        print(f"  ⚠️ 删除项目失败: {e}")


def print_summary(short_results, short_passed, short_failed,
                  content_results, content_passed, content_failed):
    """打印测试总结"""
    print_header("测试总结")

    total_passed = short_passed + content_passed
    total_failed = short_failed + content_failed
    total = total_passed + total_failed

    print(f"""
┌─────────────────────────────────────────────────┐
│  测试类型           │  通过  │  失败  │  通过率  │
├─────────────────────────────────────────────────┤
│  短关键词测试       │  {short_passed:3d}   │  {short_failed:3d}   │  {short_passed/len(SHORT_KEYWORD_TESTS)*100:5.1f}% │
│  贴近内容问题测试   │  {content_passed:3d}   │  {content_failed:3d}   │  {content_passed/len(CONTENT_BASED_TESTS)*100:5.1f}% │
├─────────────────────────────────────────────────┤
│  总计               │  {total_passed:3d}   │  {total_failed:3d}   │  {total/total*100 if total else 0:5.1f}% │
└─────────────────────────────────────────────────┘
""")

    # 输出详细结果 JSON
    detail = {
        "short_keyword_tests": short_results,
        "content_based_tests": content_results,
        "summary": {
            "short_keyword": {"passed": short_passed, "failed": short_failed, "total": len(SHORT_KEYWORD_TESTS)},
            "content_based": {"passed": content_passed, "failed": content_failed, "total": len(CONTENT_BASED_TESTS)},
            "total": {"passed": total_passed, "failed": total_failed},
        }
    }

    # 保存结果到文件
    result_file = os.path.join(os.path.dirname(__file__), "test_memory_recall_result.json")
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(detail, f, ensure_ascii=False, indent=2)
    print(f"  详细结果已保存到: {result_file}")


def main():
    print("=" * 60)
    print("  Code-Mind 持久化记忆召回测试")
    print("=" * 60)

    print(f"""
  测试项目: {PROJECT}
  记忆文件: {len(MEMORY_FILES)} 个
  短关键词测试: {len(SHORT_KEYWORD_TESTS)} 个
  贴近内容问题测试: {len(CONTENT_BASED_TESTS)} 个
""")

    try:
        manager = MemoryManager()
        manager.login()

        # 1. 上传记忆
        if not upload_memories(manager):
            print("上传失败，终止测试")
            return

        # 2. 等待分块
        if not wait_for_chunks(manager):
            print("分块超时，终止测试")
            return

        # 3. 短关键词测试
        short_results, short_passed, short_failed = test_short_keywords(manager)

        # 4. 贴近内容问题测试
        content_results, content_passed, content_failed = test_content_based(manager)

        # 5. 清理
        cleanup(manager)

        # 6. 总结
        print_summary(short_results, short_passed, short_failed,
                      content_results, content_passed, content_failed)

    except Exception as e:
        print(f"\n  ❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
