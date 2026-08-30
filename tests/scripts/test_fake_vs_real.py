# -*- coding: utf-8 -*-
"""
伪造知识 vs 真实知识 测试

测试目标：
1. 上传伪造的错误/过时知识
2. 上传正确的持久化记忆
3. 测试能否获取正确回答
4. 测试能否识别错误数据并删除
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

PROJECT = "Code-Mind-Conflict-Test"

# ==================== 伪造的错误/过时知识 ====================
FAKE_MEMORIES = [
    {
        "filename": "fake_tech_stack.md",
        "content": """# 技术栈（过时版本）

## 后端技术
- 框架：Spring Boot 2.3（已过时，当前使用 4.1）
- ORM：Hibernate（已替换为 MyBatis-Plus）
- 数据库：MySQL 5.7（已迁移到 PostgreSQL + pgvector）
- 缓存：Memcached（已替换为 Redis）

## 前端技术
- 框架：jQuery（已迁移到 React 18）
- 构建工具：Grunt（已替换为 Vite）

## 说明
这是一个过时的技术栈文档，仅供参考。
""",
        "is_fake": True,
        "fake_reason": "技术栈信息过时，全部使用了旧版本",
    },
    {
        "filename": "fake_api_design.md",
        "content": """# API 设计规范（错误版本）

## 接口规范
- 使用 SOAP 协议（错误：实际使用 RESTful）
- 返回 XML 格式（错误：实际返回 JSON）
- 认证方式：Basic Auth（错误：实际使用 Sa-Token）

## 错误的接口路径
- GET /api/v1/getUserById?id=xxx（错误风格）
- POST /api/v1/doLogin（错误命名）

## 正确的接口路径应该是
- GET /api/user/{id}
- POST /api/auth/login
""",
        "is_fake": True,
        "fake_reason": "API 设计规范完全错误",
    },
    {
        "filename": "fake_database.md",
        "content": """# 数据库设计（错误版本）

## 数据库选择
使用 MySQL 8.0 作为主数据库（错误：实际使用 PostgreSQL 16）

## 表结构
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT,  -- 错误：实际使用 VARCHAR(20) 雪花ID
    name VARCHAR(50),
    created_at DATETIME     -- 错误：实际使用 TIMESTAMP
);
```

## 向量存储
使用 Elasticsearch 存储向量（错误：实际使用 pgvector）

## 注意
这些信息是错误的，请勿参考。
""",
        "is_fake": True,
        "fake_reason": "数据库选型和表结构完全错误",
    },
    {
        "filename": "fake_deployment.md",
        "content": """# 部署指南（过时版本）

## 环境要求
- JDK 8（错误：实际使用 JDK 17）
- Maven 3.5（过时：实际使用 3.9）
- Node.js 12（过时：实际使用 18+）

## 部署步骤
1. 安装 Tomcat 8（错误：实际使用内嵌 Tomcat）
2. 部署 WAR 包到 webapps 目录（错误：实际使用 JAR 包直接运行）
3. 配置 Nginx 反向代理

## 数据库
使用 XAMPP 安装 MySQL（完全错误）

## 注意
此文档已过时，请勿参考。
""",
        "is_fake": True,
        "fake_reason": "部署方式完全过时",
    },
]

# ==================== 真实的持久化记忆 ====================
REAL_MEMORY_DIR = os.path.join(os.path.dirname(__file__), "docs", "memory")
REAL_MEMORY_FILES = [
    "MEMORY.md",
    "QUICK_START.md",
    "integration-design.md",
    "mcp-gateway-status.md",
    "mcp-gateway-files.md",
    "chunk-api-status.md",
    "metadata-status.md",
    "rag-status.md",
]

# ==================== 测试问题（针对伪造知识） ====================
# 使用短关键词搜索，更容易命中
CONFLICT_QUESTIONS = [
    {
        "question": "PostgreSQL",
        "fake_answer_contains": ["MySQL"],
        "real_answer_contains": ["PostgreSQL"],
        "should_find_real": True,
    },
    {
        "question": "Spring Boot",
        "fake_answer_contains": ["2.3"],
        "real_answer_contains": ["4.1"],
        "should_find_real": True,
    },
    {
        "question": "Sa-Token",
        "fake_answer_contains": ["Basic Auth", "SOAP"],
        "real_answer_contains": ["Sa-Token"],
        "should_find_real": True,
    },
    {
        "question": "JDK 17",
        "fake_answer_contains": ["JDK 8"],
        "real_answer_contains": ["JDK 17"],
        "should_find_real": True,
    },
    {
        "question": "React",
        "fake_answer_contains": ["jQuery"],
        "real_answer_contains": ["React"],
        "should_find_real": True,
    },
]


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def upload_fake_memories(manager):
    """上传伪造知识"""
    print_header("1. 上传伪造的错误/过时知识")

    for fake in FAKE_MEMORIES:
        result = manager.upload_memory(PROJECT, fake["filename"], fake["content"])
        status = result.get("status", "unknown")
        icon = "✅" if status == "success" else "❌"
        print(f"  {icon} {fake['filename']}")
        print(f"     伪造原因: {fake['fake_reason']}")

    return len(FAKE_MEMORIES)


def upload_real_memories(manager):
    """上传真实记忆"""
    print_header("2. 上传正确的持久化记忆")

    uploaded = 0
    for filename in REAL_MEMORY_FILES:
        filepath = os.path.join(REAL_MEMORY_DIR, filename)
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

    return uploaded


def wait_for_chunks(manager, timeout=60):
    """等待分块完成"""
    print_header("3. 等待分块完成")

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


def test_conflict_detection(manager):
    """测试矛盾检测"""
    print_header("4. 测试矛盾检测（能否获取正确答案）")

    passed = 0
    failed = 0
    results = []

    for tc in CONFLICT_QUESTIONS:
        question = tc["question"]
        fake_keywords = tc["fake_answer_contains"]
        real_keywords = tc["real_answer_contains"]

        # 搜索所有结果
        result = manager.ask_project(PROJECT, question, top_k=5)
        search_results = result.get("results", [])

        if not search_results:
            print(f"\n  ❓ \"{question}\" → 无结果")
            failed += 1
            results.append({"question": question, "status": "NO_RESULT"})
            continue

        # 分析结果
        found_real = False
        found_fake = False
        best_result = None

        for r in search_results:
            content = r.get("content", "")
            score = r.get("score", 0)

            has_real = any(kw.lower() in content.lower() for kw in real_keywords)
            has_fake = any(kw.lower() in content.lower() for kw in fake_keywords)

            if has_real and not found_real:
                found_real = True
                best_result = r

            if has_fake:
                found_fake = True

        # 判断结果
        if found_real:
            content_preview = best_result.get("content", "")[:100].replace("\n", " ")
            print(f"\n  ✅ \"{question}\" → 找到正确答案")
            print(f"     正确关键词: {[kw for kw in real_keywords if kw.lower() in best_result.get('content', '').lower()]}")
            print(f"     内容: {content_preview}...")
            passed += 1
            results.append({"question": question, "status": "CORRECT", "found_real": True, "found_fake": found_fake})
        elif found_fake:
            print(f"\n  ⚠️ \"{question}\" → 只找到错误答案")
            print(f"     错误关键词: {[kw for kw in fake_keywords if kw.lower() in search_results[0].get('content', '').lower()]}")
            failed += 1
            results.append({"question": question, "status": "WRONG_ONLY", "found_real": False, "found_fake": True})
        else:
            print(f"\n  ❓ \"{question}\" → 找到结果但未命中关键词")
            failed += 1
            results.append({"question": question, "status": "PARTIAL", "found_real": False, "found_fake": False})

    print(f"\n  矛盾检测测试: {passed}/{len(CONFLICT_QUESTIONS)} 通过")
    return results, passed, failed


def test_find_and_delete_fake(manager):
    """测试查找并删除伪造知识"""
    print_header("5. 测试查找并删除伪造知识")

    client = RAGClient()
    client.login()
    kb_id = manager.get_or_create_project_kb(PROJECT)

    # 搜索可能包含伪造知识的内容
    fake_indicators = ["过时", "错误", "已替换", "已迁移到", "请勿参考", "已过时"]

    deleted_count = 0
    checked_count = 0

    for indicator in fake_indicators:
        results = client.search_similar(indicator, kb_id=kb_id, top_k=10)
        if not results:
            continue

        for r in results:
            content = r.get("content", "")
            chunk_id = r.get("chunkId")

            # 检查是否包含伪造知识的特征
            is_likely_fake = any(kw in content for kw in ["过时", "错误", "请勿参考", "已替换"])

            if is_likely_fake and chunk_id:
                checked_count += 1
                preview = content[:80].replace("\n", " ")
                print(f"  🔍 发现疑似伪造知识: {preview}...")

                try:
                    client.deprecate_chunk(chunk_id)
                    print(f"     ✅ 已标记为废弃: {chunk_id}")
                    deleted_count += 1
                except Exception as e:
                    print(f"     ❌ 标记失败: {e}")

    print(f"\n  检查了 {checked_count} 条疑似伪造知识，标记了 {deleted_count} 条")
    return deleted_count


def cleanup(manager):
    """清理测试数据"""
    print_header("6. 清理测试数据")

    from mcp_gateway.memory_tools import delete_memory_impl
    try:
        result = delete_memory_impl(PROJECT)
        print(f"  ✅ 删除项目: {PROJECT}")
    except Exception as e:
        print(f"  ⚠️ 删除项目失败: {e}")


def print_summary(conflict_results, conflict_passed, conflict_failed, deleted_count):
    """打印测试总结"""
    print_header("测试总结")

    print(f"""
┌─────────────────────────────────────────────────────────┐
│  测试项目                      │  结果                  │
├─────────────────────────────────────────────────────────┤
│  上传伪造知识                  │  {len(FAKE_MEMORIES)} 个                  │
│  上传真实记忆                  │  {len(REAL_MEMORY_FILES)} 个                  │
├─────────────────────────────────────────────────────────┤
│  矛盾检测（获取正确答案）      │  {conflict_passed}/{len(CONFLICT_QUESTIONS)} 通过              │
│  识别并标记伪造知识            │  {deleted_count} 条已标记              │
└─────────────────────────────────────────────────────────┘
""")

    # 详细结果
    print("  矛盾检测详细结果:")
    for r in conflict_results:
        icon = "✅" if r["status"] == "CORRECT" else "⚠️" if r["status"] == "PARTIAL" else "❌"
        print(f"    {icon} {r['question']}: {r['status']}")

    # 保存结果
    detail = {
        "fake_memories": [{"filename": f["filename"], "reason": f["fake_reason"]} for f in FAKE_MEMORIES],
        "real_memories": REAL_MEMORY_FILES,
        "conflict_tests": conflict_results,
        "deleted_fake_count": deleted_count,
        "summary": {
            "conflict_passed": conflict_passed,
            "conflict_failed": conflict_failed,
            "fake_deleted": deleted_count,
        }
    }

    result_file = os.path.join(os.path.dirname(__file__), "test_fake_vs_real_result.json")
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(detail, f, ensure_ascii=False, indent=2)
    print(f"\n  详细结果已保存到: {result_file}")


def main():
    print("=" * 60)
    print("  伪造知识 vs 真实知识 测试")
    print("=" * 60)

    print(f"""
  测试项目: {PROJECT}
  伪造知识: {len(FAKE_MEMORIES)} 个
  真实记忆: {len(REAL_MEMORY_FILES)} 个
  矛盾检测问题: {len(CONFLICT_QUESTIONS)} 个
""")

    try:
        manager = MemoryManager()
        manager.login()

        # 1. 先上传伪造知识
        upload_fake_memories(manager)

        # 2. 再上传真实记忆
        upload_real_memories(manager)

        # 3. 等待分块
        if not wait_for_chunks(manager):
            print("分块超时，终止测试")
            return

        # 4. 测试矛盾检测
        conflict_results, conflict_passed, conflict_failed = test_conflict_detection(manager)

        # 5. 测试查找并删除伪造知识
        deleted_count = test_find_and_delete_fake(manager)

        # 6. 清理
        cleanup(manager)

        # 7. 总结
        print_summary(conflict_results, conflict_passed, conflict_failed, deleted_count)

    except Exception as e:
        print(f"\n  ❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
