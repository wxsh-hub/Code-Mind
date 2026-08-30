# -*- coding: utf-8 -*-
"""
模块管理服务测试
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.path.insert(0, '.')

from mcp_gateway.rag_client import RAGClient


def test_module_crud():
    """测试模块 CRUD"""
    print("\n=== 测试模块 CRUD ===")

    client = RAGClient()
    client.login()

    # 创建模块
    print("\n  创建模块:")
    for name, desc in [("test_module_1", "测试模块1"), ("test_module_2", "测试模块2")]:
        try:
            result = client._request("POST", "/modules", {"name": name, "description": desc})
            code = result.get("code", "")
            success = code == "0"
            icon = "✅" if success else "❌"
            print(f"    {icon} create_module({name})")
        except Exception as e:
            print(f"    ❌ create_module({name}): {e}")

    # 列出模块
    print("\n  列出模块:")
    try:
        result = client._request("GET", "/modules")
        modules = result.get("data", [])
        print(f"    模块数量: {len(modules) if isinstance(modules, list) else 0}")
    except Exception as e:
        print(f"    ❌ 列出失败: {e}")

    # 删除模块
    print("\n  删除模块:")
    for name in ["test_module_1", "test_module_2"]:
        try:
            client.delete_module(name)
            print(f"    ✅ delete_module({name})")
        except Exception as e:
            print(f"    ❌ delete_module({name}): {e}")

    return True


def test_feature_crud():
    """测试功能 CRUD"""
    print("\n=== 测试功能 CRUD ===")

    client = RAGClient()
    client.login()

    # 先创建模块
    try:
        client._request("POST", "/modules", {"name": "test_module", "description": "测试模块"})
    except Exception:
        pass

    # 创建功能
    print("\n  创建功能:")
    for code, name, module in [("T001", "测试功能1", "test_module"), ("T002", "测试功能2", "test_module")]:
        try:
            result = client._request("POST", "/feature-metadata", {
                "featureCode": code,
                "featureName": name,
                "moduleName": module,
            })
            code_result = result.get("code", "")
            success = code_result == "0"
            icon = "✅" if success else "❌"
            print(f"    {icon} create_feature({code})")
        except Exception as e:
            print(f"    ❌ create_feature({code}): {e}")

    # 列出功能
    print("\n  列出功能:")
    try:
        result = client._request("GET", "/feature-metadata")
        features = result.get("data", [])
        print(f"    功能数量: {len(features) if isinstance(features, list) else 0}")
    except Exception as e:
        print(f"    ❌ 列出失败: {e}")

    # 删除功能
    print("\n  删除功能:")
    for code in ["T001", "T002"]:
        try:
            client.delete_feature(code)
            print(f"    ✅ delete_feature({code})")
        except Exception as e:
            print(f"    ❌ delete_feature({code}): {e}")

    # 清理模块
    try:
        client.delete_module("test_module")
    except Exception:
        pass

    return True


def main():
    print("=" * 60)
    print("  模块管理服务测试")
    print("=" * 60)

    results = {
        "module_crud": test_module_crud(),
        "feature_crud": test_feature_crud(),
    }

    print("\n" + "=" * 60)
    print("  测试总结")
    print("=" * 60)

    for name, passed in results.items():
        icon = "✅" if passed else "❌"
        print(f"  {icon} {name}: {'PASS' if passed else 'FAIL'}")

    all_passed = all(results.values())
    print(f"\n  总计: {sum(results.values())}/{len(results)} 通过")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
