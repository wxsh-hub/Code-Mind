# -*- coding: utf-8 -*-
"""
近似词匹配 + AI 判断测试

测试内容：
1. 近似词匹配（大部分）- 测试语义相近的词能否找到正确内容
2. 关键词匹配（小部分）- 测试精确匹配
3. AI 判断 - 获取多个结果让 AI 判断哪个是正确的
4. AI 删除 - AI 标记并删除过时知识
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

PROJECT = "Code-Mind-AI-Judge"

# ==================== 近似词匹配测试（大部分） ====================
# 用户问的是近似词，期望找到包含精确技术词的内容
SIMILARITY_TESTS = [
    {
        "query": "数据库",
        "expected_keywords": ["PostgreSQL", "pgvector"],
        "wrong_keywords": ["MySQL", "Elasticsearch"],
        "description": "问'数据库'应该找到 PostgreSQL",
    },
    {
        "query": "认证",
        "expected_keywords": ["Sa-Token", "token"],
        "wrong_keywords": ["Basic Auth", "SOAP"],
        "description": "问'认证'应该找到 Sa-Token",
    },
    {
        "query": "前端",
        "expected_keywords": ["React"],
        "wrong_keywords": ["jQuery"],
        "description": "问'前端'应该找到 React",
    },
    {
        "query": "缓存",
        "expected_keywords": ["Redis"],
        "wrong_keywords": ["Memcached"],
        "description": "问'缓存'应该找到 Redis",
    },
    {
        "query": "消息队列",
        "expected_keywords": ["RocketMQ"],
        "wrong_keywords": ["Kafka", "RabbitMQ"],
        "description": "问'消息队列'应该找到 RocketMQ",
    },
    {
        "query": "向量存储",
        "expected_keywords": ["pgvector", "PostgreSQL"],
        "wrong_keywords": ["Elasticsearch", "Milvus"],
        "description": "问'向量存储'应该找到 pgvector",
    },
    {
        "query": "对象存储",
        "expected_keywords": ["RustFS", "S3"],
        "wrong_keywords": ["OSS", "MinIO"],
        "description": "问'对象存储'应该找到 RustFS",
    },
    {
        "query": "构建工具",
        "expected_keywords": ["Vite", "npm"],
        "wrong_keywords": ["Grunt", "Webpack"],
        "description": "问'构建工具'应该找到 Vite",
    },
    {
        "query": "ORM框架",
        "expected_keywords": ["MyBatis", "MyBatis-Plus"],
        "wrong_keywords": ["Hibernate"],
        "description": "问'ORM框架'应该找到 MyBatis-Plus",
    },
    {
        "query": "网关",
        "expected_keywords": ["MCP Gateway", "FastMCP"],
        "wrong_keywords": ["Spring Cloud Gateway"],
        "description": "问'网关'应该找到 MCP Gateway",
    },
]

# ==================== 关键词匹配测试（小部分） ====================
KEYWORD_TESTS = [
    {
        "query": "PostgreSQL",
        "expected_keywords": ["PostgreSQL"],
        "description": "精确匹配 PostgreSQL",
    },
    {
        "query": "pgvector",
        "expected_keywords": ["pgvector"],
        "description": "精确匹配 pgvector",
    },
    {
        "query": "Sa-Token",
        "expected_keywords": ["Sa-Token"],
        "description": "精确匹配 Sa-Token",
    },
    {
        "query": "RocketMQ",
        "expected_keywords": ["RocketMQ"],
        "description": "精确匹配 RocketMQ",
    },
    {
        "query": "Redis",
        "expected_keywords": ["Redis"],
        "description": "精确匹配 Redis",
    },
]

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
        "filename": "fake_wrong_config.md",
        "content": """# 错误配置示例

警告：以下配置是错误的，请勿使用。

## 数据库配置（错误）
```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/ragent
    driver-class-name: com.mysql.cj.jdbc.Driver
```

正确配置应该是 PostgreSQL：
```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/ragent
    driver-class-name: org.postgresql.Driver
```

## 缓存配置（错误）
使用 Memcached（错误：应该使用 Redis）
""",
    },
]

# ==================== AI 判断测试问题 ====================
AI_JUDGE_QUESTIONS = [
    {
        "question": "项目使用什么数据库？请说明正确的技术选型。",
        "context": "需要判断哪个是当前使用的技术，哪个是过时的",
        "expected_correct": "PostgreSQL + pgvector",
        "expected_wrong": "MySQL",
    },
    {
        "question": "项目使用什么缓存？请说明正确的技术选型。",
        "context": "需要判断哪个是当前使用的技术",
        "expected_correct": "Redis",
        "expected_wrong": "Memcached",
    },
    {
        "question": "项目使用什么前端框架？请说明正确的技术选型。",
        "context": "需要判断哪个是当前使用的技术",
        "expected_correct": "React",
        "expected_wrong": "jQuery",
    },
]


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def upload_memories(manager):
    """上传所有记忆"""
    print_header("1. 上传记忆")

    # 上传伪造知识
    print("\n  上传伪造知识:")
    for fake in FAKE_MEMORIES:
        result = manager.upload_memory(PROJECT, fake["filename"], fake["content"])
        print(f"    ✅ {fake['filename']}")

    # 上传真实记忆
    print("\n  上传真实记忆:")
    memory_dir = os.path.join(os.path.dirname(__file__), "docs", "memory")
    real_files = ["MEMORY.md", "QUICK_START.md", "integration-design.md",
                  "mcp-gateway-status.md", "chunk-api-status.md", "metadata-status.md"]

    for filename in real_files:
        filepath = os.path.join(memory_dir, filename)
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


def test_similarity_search(manager):
    """测试近似词匹配"""
    print_header("3. 近似词匹配测试（10个）")

    passed = 0
    failed = 0
    results = []

    for tc in SIMILARITY_TESTS:
        query = tc["query"]
        expected = tc["expected_keywords"]
        wrong = tc["wrong_keywords"]

        result = manager.ask_project(PROJECT, query, top_k=5)
        search_results = result.get("results", [])

        if not search_results:
            print(f"\n  ❌ \"{query}\" → 无结果")
            failed += 1
            results.append({"query": query, "status": "NO_RESULT"})
            continue

        # 检查前3条结果
        found_correct = False
        found_wrong = False
        best_content = ""

        for r in search_results[:3]:
            content = r.get("content", "")
            if any(kw.lower() in content.lower() for kw in expected):
                found_correct = True
                best_content = content
            if any(kw.lower() in content.lower() for kw in wrong):
                found_wrong = True

        if found_correct:
            preview = best_content[:80].replace("\n", " ")
            print(f"\n  ✅ \"{query}\" → 找到正确答案")
            print(f"     期望: {expected}, 命中: {[kw for kw in expected if kw.lower() in best_content.lower()]}")
            passed += 1
            results.append({"query": query, "status": "CORRECT", "found_correct": True, "found_wrong": found_wrong})
        elif found_wrong:
            print(f"\n  ⚠️ \"{query}\" → 只找到错误答案")
            failed += 1
            results.append({"query": query, "status": "WRONG_ONLY", "found_correct": False, "found_wrong": True})
        else:
            print(f"\n  ❓ \"{query}\" → 未命中关键词")
            failed += 1
            results.append({"query": query, "status": "MISS", "found_correct": False, "found_wrong": False})

    print(f"\n  近似词匹配: {passed}/{len(SIMILARITY_TESTS)} 通过")
    return results, passed, failed


def test_keyword_search(manager):
    """测试关键词匹配"""
    print_header("4. 关键词匹配测试（5个）")

    passed = 0
    failed = 0
    results = []

    for tc in KEYWORD_TESTS:
        query = tc["query"]
        expected = tc["expected_keywords"]

        result = manager.ask_project(PROJECT, query, top_k=3)
        search_results = result.get("results", [])

        if not search_results:
            print(f"\n  ❌ \"{query}\" → 无结果")
            failed += 1
            results.append({"query": query, "status": "NO_RESULT"})
            continue

        content = search_results[0].get("content", "")
        found = any(kw.lower() in content.lower() for kw in expected)

        if found:
            print(f"\n  ✅ \"{query}\" → 命中")
            passed += 1
            results.append({"query": query, "status": "PASS"})
        else:
            print(f"\n  ❌ \"{query}\" → 未命中")
            failed += 1
            results.append({"query": query, "status": "FAIL"})

    print(f"\n  关键词匹配: {passed}/{len(KEYWORD_TESTS)} 通过")
    return results, passed, failed


def test_ai_judge(manager):
    """测试 AI 判断"""
    print_header("5. AI 判断测试")

    client = RAGClient()
    client.login()
    kb_id = manager.get_or_create_project_kb(PROJECT)

    results = []

    for tc in AI_JUDGE_QUESTIONS:
        question = tc["question"]
        print(f"\n  问题: {question}")
        print(f"  上下文: {tc['context']}")

        # 获取多个结果
        search_results = client.search_similar(tc["expected_correct"].split()[0], kb_id=kb_id, top_k=5)

        if not search_results:
            print(f"  ❌ 无搜索结果")
            results.append({"question": question, "status": "NO_RESULT"})
            continue

        # 模拟 AI 判断逻辑
        correct_found = False
        wrong_found = False
        correct_content = ""
        wrong_content = ""

        for r in search_results:
            content = r.get("content", "")

            # 检查是否包含正确答案
            if tc["expected_correct"].lower() in content.lower():
                correct_found = True
                correct_content = content

            # 检查是否包含错误答案
            if tc["expected_wrong"].lower() in content.lower():
                wrong_found = True
                wrong_content = content

        # AI 判断结果
        if correct_found and not wrong_found:
            print(f"  ✅ AI 判断: 正确答案是 {tc['expected_correct']}")
            print(f"     来源: {correct_content[:80]}...")
            results.append({"question": question, "status": "CORRECT_ONLY"})
        elif correct_found and wrong_found:
            print(f"  ⚠️ AI 判断: 同时找到正确和错误信息")
            print(f"     正确: {tc['expected_correct']} (在 {correct_content[:50]}...)")
            print(f"     错误: {tc['expected_wrong']} (在 {wrong_content[:50]}...)")
            results.append({"question": question, "status": "MIXED"})
        elif wrong_found:
            print(f"  ❌ AI 判断: 只找到错误信息 {tc['expected_wrong']}")
            results.append({"question": question, "status": "WRONG_ONLY"})
        else:
            print(f"  ❓ AI 判断: 未找到相关信息")
            results.append({"question": question, "status": "NOT_FOUND"})

    return results


def test_ai_delete_fake(manager):
    """测试 AI 删除伪造知识"""
    print_header("6. AI 删除伪造知识")

    client = RAGClient()
    client.login()
    kb_id = manager.get_or_create_project_kb(PROJECT)

    # 搜索可能包含伪造知识的关键词
    fake_indicators = ["过时", "错误", "请勿参考", "已替换", "已迁移", "警告"]

    deleted_chunks = set()
    total_checked = 0

    for indicator in fake_indicators:
        results = client.search_similar(indicator, kb_id=kb_id, top_k=10)

        for r in results:
            content = r.get("content", "")
            chunk_id = r.get("chunkId")

            # AI 判断：检查是否包含伪造知识特征
            is_fake = False
            reasons = []

            if "过时" in content:
                is_fake = True
                reasons.append("包含'过时'")
            if "错误" in content:
                is_fake = True
                reasons.append("包含'错误'")
            if "请勿参考" in content:
                is_fake = True
                reasons.append("包含'请勿参考'")
            if "已替换" in content:
                is_fake = True
                reasons.append("包含'已替换'")
            if "已迁移" in content:
                is_fake = True
                reasons.append("包含'已迁移'")
            if "警告" in content:
                is_fake = True
                reasons.append("包含'警告'")

            if is_fake and chunk_id and chunk_id not in deleted_chunks:
                total_checked += 1
                preview = content[:60].replace("\n", " ")
                print(f"\n  🔍 发现伪造知识: {preview}...")
                print(f"     原因: {', '.join(reasons)}")

                # AI 决定删除
                try:
                    client.deprecate_chunk(chunk_id)
                    deleted_chunks.add(chunk_id)
                    print(f"     ✅ AI 已标记为废弃: {chunk_id}")
                except Exception as e:
                    print(f"     ❌ 标记失败: {e}")

    print(f"\n  AI 检查了 {total_checked} 条知识，标记了 {len(deleted_chunks)} 条为废弃")
    return len(deleted_chunks)


def cleanup(manager):
    """清理测试数据"""
    print_header("7. 清理测试数据")

    from mcp_gateway.memory_tools import delete_memory_impl
    try:
        result = delete_memory_impl(PROJECT)
        print(f"  ✅ 删除项目: {PROJECT}")
    except Exception as e:
        print(f"  ⚠️ 删除失败: {e}")


def print_summary(sim_results, sim_passed, sim_failed,
                  kw_results, kw_passed, kw_failed,
                  ai_results, deleted_count):
    """打印测试总结"""
    print_header("测试总结")

    total_passed = sim_passed + kw_passed
    total_failed = sim_failed + kw_failed
    total = total_passed + total_failed

    print(f"""
┌─────────────────────────────────────────────────────────────┐
│  测试类型              │  通过  │  失败  │  通过率          │
├─────────────────────────────────────────────────────────────┤
│  近似词匹配（10个）    │  {sim_passed:3d}   │  {sim_failed:3d}   │  {sim_passed/len(SIMILARITY_TESTS)*100:5.1f}%          │
│  关键词匹配（5个）     │  {kw_passed:3d}   │  {kw_failed:3d}   │  {kw_passed/len(KEYWORD_TESTS)*100:5.1f}%          │
├─────────────────────────────────────────────────────────────┤
│  总计                  │  {total_passed:3d}   │  {total_failed:3d}   │  {total/(total or 1)*100:5.1f}%          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  AI 判断测试                                                │
├─────────────────────────────────────────────────────────────┤
│  AI 判断问题: {len(ai_results)} 个                                          │
│  AI 删除伪造知识: {deleted_count} 条                                      │
└─────────────────────────────────────────────────────────────┘
""")

    # AI 判断详情
    print("  AI 判断详情:")
    for r in ai_results:
        icon = "✅" if r["status"] == "CORRECT_ONLY" else "⚠️" if r["status"] == "MIXED" else "❌"
        print(f"    {icon} {r['question'][:40]}... → {r['status']}")

    # 保存结果
    detail = {
        "similarity_tests": {"results": sim_results, "passed": sim_passed, "failed": sim_failed},
        "keyword_tests": {"results": kw_results, "passed": kw_passed, "failed": kw_failed},
        "ai_judge_tests": ai_results,
        "ai_deleted_count": deleted_count,
    }

    result_file = os.path.join(os.path.dirname(__file__), "test_ai_judge_result.json")
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(detail, f, ensure_ascii=False, indent=2)
    print(f"  结果已保存: {result_file}")


def main():
    print("=" * 60)
    print("  近似词匹配 + AI 判断测试")
    print("=" * 60)

    print(f"""
  测试项目: {PROJECT}
  近似词测试: {len(SIMILARITY_TESTS)} 个
  关键词测试: {len(KEYWORD_TESTS)} 个
  AI 判断问题: {len(AI_JUDGE_QUESTIONS)} 个
  伪造知识: {len(FAKE_MEMORIES)} 个
""")

    try:
        manager = MemoryManager()
        manager.login()

        # 1. 上传记忆
        upload_memories(manager)

        # 2. 等待分块
        if not wait_for_chunks(manager):
            return

        # 3. 近似词匹配测试
        sim_results, sim_passed, sim_failed = test_similarity_search(manager)

        # 4. 关键词匹配测试
        kw_results, kw_passed, kw_failed = test_keyword_search(manager)

        # 5. AI 判断测试
        ai_results = test_ai_judge(manager)

        # 6. AI 删除伪造知识
        deleted_count = test_ai_delete_fake(manager)

        # 7. 清理
        cleanup(manager)

        # 8. 总结
        print_summary(sim_results, sim_passed, sim_failed,
                      kw_results, kw_passed, kw_failed,
                      ai_results, deleted_count)

    except Exception as e:
        print(f"\n  ❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
