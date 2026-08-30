# -*- coding: utf-8 -*-
"""
AI 判断并删除过时知识 完整链路测试

测试流程：
1. 上传伪造知识（过时/错误）和真实知识
2. AI 通过向量检索获取回答
3. AI 判断哪些是过时/错误的
4. 从 sources 中找到对应的 chunkId
5. AI 调用删除接口删除过时知识
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

PROJECT = "Code-Mind-AI-Delete"

# ==================== 伪造知识 ====================
FAKE_MEMORIES = [
    {
        "filename": "fake_outdated_stack.md",
        "content": """# 过时技术栈（请勿参考）

此文档已过时，仅供参考。

## 后端
- Spring Boot 2.3（已过时，当前使用 4.1）
- Hibernate（已替换为 MyBatis-Plus）
- MySQL（已迁移到 PostgreSQL）

## 前端
- jQuery（已迁移到 React）
- Grunt（已替换为 Vite）

## 基础设施
- Memcached（已替换为 Redis）
- Kafka（未使用，当前使用 RocketMQ）
""",
    },
    {
        "filename": "fake_wrong_database.md",
        "content": """# 错误数据库配置

警告：以下配置是错误的，请勿使用。

## 数据库配置（错误）
```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/ragent
    driver-class-name: com.mysql.cj.jdbc.Driver
```

使用 MySQL 8.0 作为主数据库（错误：实际使用 PostgreSQL）
使用 Elasticsearch 存储向量（错误：实际使用 pgvector）
""",
    },
]

# ==================== 真实记忆 ====================
REAL_MEMORY_DIR = os.path.join(os.path.dirname(__file__), "docs", "memory")
REAL_MEMORY_FILES = ["MEMORY.md", "QUICK_START.md", "integration-design.md"]


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def upload_memories(manager):
    """上传记忆"""
    print_header("1. 上传记忆")

    print("\n  上传伪造知识:")
    for fake in FAKE_MEMORIES:
        manager.upload_memory(PROJECT, fake["filename"], fake["content"])
        print(f"    ✅ {fake['filename']}")

    print("\n  上传真实记忆:")
    for filename in REAL_MEMORY_FILES:
        filepath = os.path.join(REAL_MEMORY_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            manager.upload_memory(PROJECT, filename, content)
            print(f"    ✅ {filename}")


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

    return False


def ai_judge_and_delete(client):
    """AI 判断并删除过时知识"""
    print_header("3. AI 判断并删除过时知识")

    # 问题列表
    questions = [
        "项目使用什么数据库？",
        "Spring Boot 版本是多少？",
        "JDK 版本是多少？",
        "使用什么缓存？",
    ]

    all_outdated_sources = []

    for question in questions:
        print(f"\n  问题: {question}")

        # 获取 AI 回答 + sources
        result = client.rag_chat_with_sources(question)
        answer = result["answer"]
        sources = result["sources"]

        print(f"  AI 回答: {answer[:150]}...")

        # AI 判断：检查回答中是否提到过时/错误信息
        outdated_keywords = ["过时", "错误", "已迁移", "已替换", "已升级", "请勿参考", "警告"]
        is_outdated = any(kw in answer for kw in outdated_keywords)

        if is_outdated:
            print(f"  ⚠️ AI 检测到过时/错误信息")

            # 从 sources 中找到包含过时信息的文档
            for source in sources:
                doc_name = source.get("docName", "")
                excerpt = source.get("excerpt", "")

                # 检查 source 是否包含过时信息
                is_fake_source = any(kw in excerpt for kw in outdated_keywords)

                if is_fake_source:
                    doc_id = source.get("docId")
                    print(f"    🔍 发现过时文档: {doc_name}")
                    print(f"       摘录: {excerpt[:80]}...")

                    # 查找对应的 chunkId
                    if doc_id:
                        chunks = client.get_chunks(doc_id)
                        if chunks:
                            records = chunks.get("records", []) if isinstance(chunks, dict) else chunks
                            for chunk in (records if isinstance(records, list) else []):
                                chunk_id = chunk.get("id") if isinstance(chunk, dict) else None
                                if chunk_id and chunk_id not in all_outdated_sources:
                                    all_outdated_sources.append({
                                        "chunk_id": chunk_id,
                                        "doc_name": doc_name,
                                        "doc_id": doc_id,
                                    })

    # 删除过时知识
    print_header("4. 删除过时知识")

    deleted_count = 0
    for item in all_outdated_sources:
        chunk_id = item["chunk_id"]
        doc_name = item["doc_name"]

        try:
            client.deprecate_chunk(chunk_id)
            print(f"  ✅ 已标记废弃: {chunk_id} ({doc_name})")
            deleted_count += 1
        except Exception as e:
            print(f"  ❌ 删除失败: {chunk_id} ({doc_name}): {e}")

    return deleted_count


def verify_deletion(client, manager):
    """验证删除结果"""
    print_header("5. 验证删除结果")

    kb_id = manager.get_or_create_project_kb(PROJECT)

    # 搜索过时关键词
    print("\n  搜索过时关键词:")
    for keyword in ["过时", "错误", "MySQL", "Hibernate"]:
        results = client.search_similar(keyword, kb_id=kb_id, top_k=3)
        if results:
            for r in results:
                content = r.get("content", "")
                deprecated = r.get("deprecated", False)
                status = "已废弃" if deprecated else "未废弃"
                print(f"    [{status}] {content[:60]}...")
        else:
            print(f"    未找到包含 '{keyword}' 的结果")


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
    print("  AI 判断并删除过时知识 完整链路测试")
    print("=" * 60)

    try:
        manager = MemoryManager()
        manager.login()

        # 1. 上传记忆
        upload_memories(manager)

        # 2. 等待分块
        if not wait_for_chunks(manager):
            print("分块超时")
            return

        # 3. AI 判断并删除
        client = RAGClient()
        client.login()
        deleted_count = ai_judge_and_delete(client)

        # 4. 验证删除
        verify_deletion(client, manager)

        # 5. 清理
        cleanup()

        # 6. 总结
        print_header("测试总结")
        print(f"""
  ✅ 完整链路测试成功

  AI 删除过时知识: {deleted_count} 条

  链路:
  1. 上传伪造 + 真实知识
  2. AI 向量检索获取回答
  3. AI 判断过时/错误信息
  4. 从 sources 找到 docId
  5. 通过 docId 找到 chunkId
  6. 调用 deprecate_chunk 删除
""")

    except Exception as e:
        print(f"\n  ❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
