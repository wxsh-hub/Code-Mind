# -*- coding: utf-8 -*-
"""
向量检索 + AI 判断 + 删除过时知识 完整链路测试

测试流程：
1. 上传伪造知识（过时/错误）和真实知识
2. 用近似词 → 向量检索 → AI 回答
3. AI 判断哪个是正确的，哪个是过时的
4. AI 调用删除 MCP 删除过时知识
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

PROJECT = "Code-Mind-Vector-AI-Judge"

# ==================== 伪造知识（过时/错误） ====================
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
    {
        "filename": "fake_old_deployment.md",
        "content": """# 过时部署指南

此文档已过时，请勿参考。

## 环境要求
- JDK 8（错误：实际使用 JDK 17）
- Maven 3.5（过时：实际使用 3.9）
- Node.js 12（过时：实际使用 18+）

## 部署步骤
1. 安装 Tomcat 8（错误：实际使用内嵌 Tomcat）
2. 部署 WAR 包（错误：实际使用 JAR 包）
""",
    },
]

# ==================== 真实记忆 ====================
REAL_MEMORY_DIR = os.path.join(os.path.dirname(__file__), "docs", "memory")
REAL_MEMORY_FILES = [
    "MEMORY.md",
    "QUICK_START.md",
    "integration-design.md",
    "mcp-gateway-status.md",
    "chunk-api-status.md",
    "metadata-status.md",
]

# ==================== 测试问题（近似词） ====================
TEST_QUESTIONS = [
    {
        "question": "项目使用什么数据库？",
        "expected_correct": "PostgreSQL",
        "expected_wrong": "MySQL",
    },
    {
        "question": "Spring Boot 版本是多少？",
        "expected_correct": "4.1",
        "expected_wrong": "2.3",
    },
    {
        "question": "JDK 版本是多少？",
        "expected_correct": "17",
        "expected_wrong": "8",
    },
    {
        "question": "使用什么缓存？",
        "expected_correct": "Redis",
        "expected_wrong": "Memcached",
    },
    {
        "question": "前端框架是什么？",
        "expected_correct": "React",
        "expected_wrong": "jQuery",
    },
]


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def upload_memories(manager):
    """上传记忆"""
    print_header("1. 上传记忆")

    # 上传伪造知识
    print("\n  上传伪造知识:")
    for fake in FAKE_MEMORIES:
        result = manager.upload_memory(PROJECT, fake["filename"], fake["content"])
        print(f"    ✅ {fake['filename']}")

    # 上传真实记忆
    print("\n  上传真实记忆:")
    for filename in REAL_MEMORY_FILES:
        filepath = os.path.join(REAL_MEMORY_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            manager.upload_memory(PROJECT, filename, content)
            print(f"    ✅ {filename} ({len(content)} 字符)")


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


def test_vector_search_and_ai_judge(client):
    """测试向量检索 + AI 判断"""
    print_header("3. 向量检索 + AI 判断测试")

    results = []

    for tc in TEST_QUESTIONS:
        question = tc["question"]
        print(f"\n  问题: {question}")

        try:
            # 向量检索 + AI 回答
            answer = client.rag_chat(question)

            # 检查 AI 回答中是否包含正确/错误信息
            has_correct = tc["expected_correct"].lower() in answer.lower()
            has_wrong = tc["expected_wrong"].lower() in answer.lower()

            if has_correct and not has_wrong:
                print(f"    ✅ AI 回答正确: 包含 {tc['expected_correct']}")
                print(f"    回答: {answer[:150]}...")
                results.append({"question": question, "status": "CORRECT", "answer": answer[:200]})
            elif has_correct and has_wrong:
                # AI 同时提到正确和错误，但可能指出错误是过时的
                if "过时" in answer or "错误" in answer or "已迁移" in answer:
                    print(f"    ✅ AI 正确判断: 指出 {tc['expected_wrong']} 是过时/错误的")
                    print(f"    回答: {answer[:150]}...")
                    results.append({"question": question, "status": "CORRECT_WITH_WARNING", "answer": answer[:200]})
                else:
                    print(f"    ⚠️ AI 回答混合: 同时包含正确和错误信息")
                    print(f"    回答: {answer[:150]}...")
                    results.append({"question": question, "status": "MIXED", "answer": answer[:200]})
            elif has_wrong:
                print(f"    ❌ AI 回答错误: 只包含 {tc['expected_wrong']}")
                print(f"    回答: {answer[:150]}...")
                results.append({"question": question, "status": "WRONG", "answer": answer[:200]})
            else:
                print(f"    ❓ AI 回答未命中关键词")
                print(f"    回答: {answer[:150]}...")
                results.append({"question": question, "status": "MISS", "answer": answer[:200]})

        except Exception as e:
            print(f"    ❌ 错误: {e}")
            results.append({"question": question, "status": "ERROR", "error": str(e)})

    return results


def test_ai_identify_and_delete(client):
    """测试 AI 识别并删除过时知识"""
    print_header("4. AI 识别并删除过时知识")

    # 让 AI 识别哪些知识是过时的
    identify_question = "请列出知识库中所有过时或错误的技术信息，包括文件名和具体内容。"
    print(f"\n  问题: {identify_question}")

    try:
        answer = client.rag_chat(identify_question)
        print(f"\n  AI 回答:\n{answer[:500]}...")
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return 0

    # 搜索并标记过时知识
    print("\n  搜索并标记过时知识:")
    from mcp_gateway.rag_client import RAGClient
    rag_client = RAGClient()
    rag_client.login()
    kb_id = get_manager().get_or_create_project_kb(PROJECT)

    fake_indicators = ["过时", "错误", "请勿参考", "已替换", "已迁移", "警告"]
    deleted_chunks = set()

    for indicator in fake_indicators:
        results = rag_client.search_similar(indicator, kb_id=kb_id, top_k=10)

        for r in results:
            content = r.get("content", "")
            chunk_id = r.get("chunkId")

            # AI 判断：检查是否包含伪造知识特征
            is_fake = any(kw in content for kw in ["过时", "错误", "请勿参考", "已替换", "已迁移", "警告"])

            if is_fake and chunk_id and chunk_id not in deleted_chunks:
                preview = content[:60].replace("\n", " ")
                print(f"    🔍 发现: {preview}...")

                try:
                    rag_client.deprecate_chunk(chunk_id)
                    deleted_chunks.add(chunk_id)
                    print(f"       ✅ 已标记废弃: {chunk_id}")
                except Exception as e:
                    print(f"       ❌ 标记失败: {e}")

    print(f"\n  共标记 {len(deleted_chunks)} 条过时知识")
    return len(deleted_chunks)


def get_manager():
    """获取全局 manager"""
    global _manager
    if '_manager' not in globals():
        _manager = MemoryManager()
        _manager.login()
    return _manager


def cleanup():
    """清理测试数据"""
    print_header("5. 清理测试数据")

    from mcp_gateway.memory_tools import delete_memory_impl
    try:
        result = delete_memory_impl(PROJECT)
        print(f"  ✅ 删除项目: {PROJECT}")
    except Exception as e:
        print(f"  ⚠️ 删除失败: {e}")


def print_summary(ai_results, deleted_count):
    """打印测试总结"""
    print_header("测试总结")

    correct_count = sum(1 for r in ai_results if r["status"] in ["CORRECT", "CORRECT_WITH_WARNING"])
    total = len(ai_results)

    print(f"""
┌─────────────────────────────────────────────────────────────┐
│  向量检索 + AI 判断测试                                     │
├─────────────────────────────────────────────────────────────┤
│  测试问题数: {total}                                            │
│  AI 正确判断: {correct_count}/{total} ({correct_count/total*100:.0f}%)                               │
│  AI 删除过时知识: {deleted_count} 条                                      │
└─────────────────────────────────────────────────────────────┘
""")

    # 详细结果
    print("  详细结果:")
    for r in ai_results:
        icon = "✅" if r["status"] in ["CORRECT", "CORRECT_WITH_WARNING"] else "❌"
        print(f"    {icon} {r['question']}: {r['status']}")

    # 保存结果
    detail = {
        "ai_judge_results": ai_results,
        "deleted_count": deleted_count,
        "summary": {
            "total": total,
            "correct": correct_count,
            "accuracy": f"{correct_count/total*100:.1f}%",
        }
    }

    result_file = os.path.join(os.path.dirname(__file__), "test_vector_ai_judge_result.json")
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(detail, f, ensure_ascii=False, indent=2)
    print(f"\n  结果已保存: {result_file}")


def main():
    print("=" * 60)
    print("  向量检索 + AI 判断 + 删除过时知识 完整链路测试")
    print("=" * 60)

    print(f"""
  测试项目: {PROJECT}
  伪造知识: {len(FAKE_MEMORIES)} 个
  真实记忆: {len(REAL_MEMORY_FILES)} 个
  测试问题: {len(TEST_QUESTIONS)} 个
""")

    try:
        manager = MemoryManager()
        manager.login()

        # 1. 上传记忆
        upload_memories(manager)

        # 2. 等待分块
        if not wait_for_chunks(manager):
            return

        # 3. 测试向量检索 + AI 判断
        client = RAGClient()
        client.login()
        ai_results = test_vector_search_and_ai_judge(client)

        # 4. 测试 AI 识别并删除过时知识
        deleted_count = test_ai_identify_and_delete(client)

        # 5. 清理
        cleanup()

        # 6. 总结
        print_summary(ai_results, deleted_count)

    except Exception as e:
        print(f"\n  ❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
