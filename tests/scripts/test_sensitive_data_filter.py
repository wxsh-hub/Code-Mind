import os
#!/usr/bin/env python3
"""
敏感数据过滤测试 - 验证 RAG 搜索结果是否有脱敏处理

测试步骤：
1. 上传含模拟敏感数据的文档
2. 搜索并检查返回结果是否原样暴露敏感信息
3. 测试 MCP Gateway 的 guardrail 管线
"""

import sys
import re
import time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from mcp_gateway.rag_client import RAGClient, RAGConfig

# ========== 测试用模拟敏感数据 ==========
SENSITIVE_PATTERNS = {
    "github_pat": (r"ghp_[0-9a-zA-Z]{36}", "GitHub Token"),
    "aws_key": (r"AKIA[A-Z0-9]{16}", "AWS Access Key"),
    "jwt": (r"ey[a-zA-Z0-9]+\.[a-zA-Z0-9]+", "JWT Token"),
    "email": (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "Email"),
    "phone": (r"1[3-9]\d{9}", "手机号"),
    "id_card": (r"\d{17}[\dXx]", "身份证号"),
    "bank_card": (r"\d{16,19}", "银行卡号"),
}

# 模拟文档内容（用不会触发正则的假数据，但格式真实）
TEST_DOC = """# 测试文档 - 敏感数据过滤验证

## 数据库配置
连接地址: db.internal.company.com:3306
用户名: root
密码: MyS3cretP@ssw0rd!
连接串: mysql://root:MyS3cretP@ssw0rd!@db.internal.company.com/production

## API 密钥
GitHub Token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef1234
AWS Key: AKIAIOSFODNN7EXAMPLE
JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkhuYW1lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

## 联系方式
负责人: 张三
邮箱: zhangsan@company.internal.com
手机: 13812345678
身份证: 110101199003071234
银行卡: 6222021234567890123
"""


def test_rag_search_leaks():
    """测试 RAG 搜索是否原样返回敏感数据"""
    print("\n" + "=" * 60)
    print("测试 1: RAG 搜索敏感数据泄露检测")
    print("=" * 60)

    client = RAGClient(RAGConfig())
    client.login()

    # 上传测试文档
    print("\n[1/3] 上传含敏感数据的测试文档...")
    try:
        from mcp_gateway.memory_tools import MemoryManager, MemoryConfig
        manager = MemoryManager(MemoryConfig())
        manager.login()
        kb_id = manager.get_or_create_project_kb("SensitiveFilterTest")
        result = manager.upload_memory(
            "SensitiveFilterTest",
            "sensitive_test.md",
            TEST_DOC,
            calculate_confidence=False,
        )
        print(f"  [OK] 上传成功, kb_id={kb_id}")
    except Exception as e:
        print(f"  [FAIL] 上传失败: {e}")
        return False

    # 等待索引
    print("  等待 3 秒让索引生效...")
    time.sleep(3)

    # 搜索
    print("\n[2/3] 搜索敏感数据关键词...")
    queries = ["数据库密码", "API 密钥", "GitHub Token", "联系方式"]
    leaked = []

    for q in queries:
        try:
            results = client.search_similar(q, kb_id=kb_id, top_k=5)
            for r in results:
                text = r.get("text", "") or r.get("content", "")
                for name, (pattern, label) in SENSITIVE_PATTERNS.items():
                    matches = re.findall(pattern, text)
                    if matches:
                        for m in matches:
                            leaked.append({
                                "query": q,
                                "type": label,
                                "value": m[:20] + "..." if len(m) > 20 else m,
                            })
        except Exception as e:
            print(f"  [WARN]  搜索 '{q}' 失败: {e}")

    # 报告
    print("\n[3/3] 泄露检测结果:")
    if leaked:
        print(f"  [FAIL] 发现 {len(leaked)} 处敏感数据未过滤:\n")
        seen = set()
        for item in leaked:
            key = f"{item['type']}:{item['value']}"
            if key not in seen:
                seen.add(key)
                print(f"    - [{item['type']}] 查询 '{item['query']}' → {item['value']}")
        return False
    else:
        print("  [OK] 未发现敏感数据泄露（搜索结果已过滤或未命中）")
        return True


def test_mcp_guardrail_pipeline():
    """测试 MCP Gateway 的 guardrail 插件管线"""
    print("\n" + "=" * 60)
    print("测试 2: MCP Gateway Guardrail 管线")
    print("=" * 60)

    try:
        from mcp_gateway.plugins.manager import PluginManager
        from mcp_gateway.plugins.base import PluginContext
    except ImportError as e:
        print(f"  [WARN]  无法导入插件模块: {e}")
        return None

    # 测试 guardrail 插件
    print("\n[1/2] 加载 guardrail 插件...")
    try:
        from mcp_gateway.plugins.guardrails.basic import BasicGuardrailPlugin
        from mcp_gateway.plugins.guardrails.presidio import PresidioGuardrailPlugin
        loaded = ["basic", "presidio"]
        print(f"  [OK] 已导入 guardrail 插件: {loaded}")
    except Exception as e:
        print(f"  [WARN]  导入插件失败: {e}")
        return None

    # 测试 BasicGuardrail 对密钥的过滤
    print("\n[2/2] 测试 BasicGuardrail 密钥过滤...")
    test_cases = [
        ("github_pat", "my token is ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef1234 ok"),
        ("aws_key", "access key: AKIAIOSFODNN7EXAMPLE"),
        ("jwt", "Bearer eyJhbGciOiJIUzI1NiJ9.eyJ0ZXN0IjoxfQ.abc123"),
    ]

    from mcp_gateway.plugins.guardrails.basic import BasicGuardrailPlugin
    plugin = BasicGuardrailPlugin()
    plugin.load()

    all_clean = True
    for name, text in test_cases:
        cleaned = plugin._sanitize_text(text)
        if cleaned != text:
            print(f"  [OK] [{name}] 已过滤: '{text[:40]}...'")
        else:
            print(f"  [FAIL] [{name}] 未过滤: '{text[:40]}...'")
            all_clean = False

    return all_clean


def cleanup():
    """清理测试数据"""
    print("\n[Cleanup] 删除测试文档...")
    try:
        from mcp_gateway.memory_tools import MemoryManager, MemoryConfig
        manager = MemoryManager(MemoryConfig())
        manager.login()
        kb_id = manager.get_or_create_project_kb("SensitiveFilterTest")
        # 搜索所有 chunk 并删除
        client = RAGClient(RAGConfig())
        client.login()
        results = client.search_similar("敏感数据", kb_id=kb_id, top_k=20)
        for r in results:
            chunk_id = r.get("id") or r.get("chunkId")
            if chunk_id:
                try:
                    client.deprecate_chunk(str(chunk_id))
                except Exception:
                    pass
        print("  [OK] 清理完成")
    except Exception as e:
        print(f"  [WARN] 清理失败（可手动删除）: {e}")


if __name__ == "__main__":
    print("[TEST] 敏感数据过滤测试")
    print("  验证 RAG 搜索结果和 MCP Guardrail 管线\n")

    r1 = test_rag_search_leaks()
    r2 = test_mcp_guardrail_pipeline()

    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    print(f"  RAG 搜索过滤:  {'[FAIL] 未实现' if r1 is False else '[OK] 通过' if r1 else '[WARN] 未测试'}")
    print(f"  MCP Guardrail: {'[OK] 通过' if r2 else '[FAIL] 失败' if r2 is False else '[WARN] 未测试'}")

    if not r1:
        print("\n  [WARN]  结论: Java RAG 侧没有敏感数据过滤，搜索结果原样返回！")
        print("     MCP Gateway 的 guardrail 只保护 MCP 工具调用路径，")
        print("     直接调 RAG API / KnowledgeSearchTool 不经过 MCP 管线。")

    cleanup()
