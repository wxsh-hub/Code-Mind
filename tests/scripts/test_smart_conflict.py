import os
# -*- coding: utf-8 -*-
"""
智能化矛盾检测测试
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))

from mcp_gateway.conflict_review import detect_negation


def main():
    print("=" * 60)
    print("  智能化矛盾检测测试")
    print("=" * 60)

    # 测试用例
    test_cases = [
        # 否定词对
        {
            "a": "应该使用 Redis",
            "b": "不应该使用 Redis",
            "expected": True,
            "description": "否定词对：应该 vs 不应该",
        },
        {
            "a": "启用缓存",
            "b": "禁用缓存",
            "expected": True,
            "description": "否定词对：启用 vs 禁用",
        },
        # 技术选型矛盾
        {
            "a": "推荐使用 MySQL",
            "b": "推荐使用 PostgreSQL",
            "expected": True,
            "description": "技术矛盾：MySQL vs PostgreSQL",
        },
        {
            "a": "使用 JWT Token 认证",
            "b": "使用 Sa-Token 认证",
            "expected": True,
            "description": "技术矛盾：JWT vs Sa-Token",
        },
        {
            "a": "前端使用 jQuery",
            "b": "前端使用 React",
            "expected": True,
            "description": "技术矛盾：jQuery vs React",
        },
        {
            "a": "缓存使用 Memcached",
            "b": "缓存使用 Redis",
            "expected": True,
            "description": "技术矛盾：Memcached vs Redis",
        },
        {
            "a": "使用 JDK 8",
            "b": "使用 JDK 17",
            "expected": True,
            "description": "技术矛盾：JDK 8 vs JDK 17",
        },
        # 非矛盾
        {
            "a": "使用 PostgreSQL",
            "b": "使用 Redis",
            "expected": False,
            "description": "非矛盾：PostgreSQL vs Redis（不同组件）",
        },
        {
            "a": "用户注册功能",
            "b": "用户登录功能",
            "expected": False,
            "description": "非矛盾：注册 vs 登录（不同功能）",
        },
    ]

    # 运行测试
    passed = 0
    failed = 0

    print("\n测试结果:")
    for tc in test_cases:
        result = detect_negation(tc["a"], tc["b"])
        success = result == tc["expected"]

        icon = "✅" if success else "❌"
        status = "PASS" if success else "FAIL"

        print(f"\n  {icon} {tc['description']}")
        print(f"     文本A: {tc['a']}")
        print(f"     文本B: {tc['b']}")
        print(f"     期望: {tc['expected']}, 实际: {result}, 结果: {status}")

        if success:
            passed += 1
        else:
            failed += 1

    # 总结
    print("\n" + "=" * 60)
    print("  测试总结")
    print("=" * 60)
    print(f"""
  总计: {len(test_cases)} 个
  通过: {passed} 个
  失败: {failed} 个
  通过率: {passed/len(test_cases)*100:.1f}%
""")

    if failed == 0:
        print("  ✅ 所有测试通过！")
    else:
        print(f"  ❌ 有 {failed} 个测试失败")


if __name__ == "__main__":
    main()
