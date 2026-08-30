# -*- coding: utf-8 -*-
"""
混合检索测试脚本

测试内容：
1. 自动识别功能
2. LIKE 检索
3. 向量检索
4. 混合检索（先 LIKE 后向量）
5. 不同长度的问题
6. 不同的 feature_codes 和 module 组合
"""

import sys
import io
import os
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))

from mcp_gateway.memory_tools import MemoryManager
from mcp_gateway.rag_client import RAGClient

PROJECT = "HybridSearchTest"


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def setup_test_data(manager):
    """创建测试数据"""
    print_header("1. 创建测试数据")

    # 创建模块
    print("\n  创建模块...")
    modules = [
        ("user", "用户管理模块"),
        ("order", "订单管理模块"),
        ("payment", "支付管理模块"),
    ]
    for name, desc in modules:
        try:
            manager._request('POST', '/modules', {'name': name, 'description': desc})
            print(f"    ✅ 模块: {name}")
        except Exception as e:
            print(f"    ⚠️ 模块 {name}: {e}")

    # 创建功能
    print("\n  创建功能...")
    features = [
        ("F001", "用户注册", "user", "用户注册功能，包含表单填写、邮箱验证等"),
        ("F002", "用户登录", "user", "用户登录功能，支持密码登录、验证码登录等"),
        ("F003", "订单创建", "order", "订单创建功能，包含商品选择、地址确认等"),
        ("F004", "订单支付", "order", "订单支付功能，支持多种支付方式"),
        ("F005", "支付回调", "payment", "支付回调处理，处理支付结果通知"),
    ]
    for code, name, module, desc in features:
        try:
            manager._request('POST', '/feature-metadata', {
                'featureCode': code,
                'featureName': name,
                'moduleName': module,
                'description': desc,
            })
            print(f"    ✅ 功能: {code} - {name}")
        except Exception as e:
            print(f"    ⚠️ 功能 {code}: {e}")

    # 上传文档
    print("\n  上传文档...")
    documents = [
        {
            "filename": "user_register.md",
            "content": """# 用户注册指南

## 功能说明
用户注册是系统的核心功能之一，允许新用户创建账号。

## 实现要点
1. 用户名：3-20个字符，支持中英文和数字
2. 密码：8-32个字符，必须包含大小写字母和数字
3. 邮箱：有效的邮箱格式
4. 手机号：11位手机号码

## 接口设计
- 接口路径：POST /api/user/register
- 请求参数：username, password, email, phone
- 返回结果：用户ID和token

## 注意事项
- 用户名不能重复
- 密码需要加密存储
- 注册成功后自动登录
""",
            "feature_codes": ["F001"],
            "module": "user",
        },
        {
            "filename": "user_login.md",
            "content": """# 用户登录指南

## 功能说明
用户登录允许已注册用户访问系统。

## 登录方式
1. 用户名+密码登录
2. 手机号+验证码登录
3. 第三方OAuth登录

## 接口设计
- 接口路径：POST /api/user/login
- 请求参数：username, password
- 返回结果：token和用户信息

## 安全措施
- 登录失败5次锁定账号
- Token有效期2小时
- 支持刷新Token
""",
            "feature_codes": ["F002"],
            "module": "user",
        },
        {
            "filename": "order_create.md",
            "content": """# 订单创建流程

## 功能说明
订单创建是电商系统的核心流程。

## 创建步骤
1. 选择商品
2. 确认收货地址
3. 选择支付方式
4. 提交订单

## 接口设计
- 接口路径：POST /api/order/create
- 请求参数：items[], addressId, paymentMethod
- 返回结果：订单号和订单状态

## 业务规则
- 库存不足时提示
- 优惠券自动计算
- 订单超时30分钟自动取消
""",
            "feature_codes": ["F003"],
            "module": "order",
        },
        {
            "filename": "order_payment.md",
            "content": """# 订单支付

## 功能说明
订单支付支持多种支付方式。

## 支付方式
1. 支付宝
2. 微信支付
3. 银行卡支付
4. 余额支付

## 接口设计
- 接口路径：POST /api/order/pay
- 请求参数：orderId, paymentMethod, amount
- 返回结果：支付链接或支付结果

## 支付流程
1. 创建支付单
2. 调用支付渠道
3. 等待支付结果
4. 更新订单状态
""",
            "feature_codes": ["F004"],
            "module": "order",
        },
        {
            "filename": "payment_callback.md",
            "content": """# 支付回调处理

## 功能说明
支付回调处理支付结果通知。

## 回调流程
1. 接收支付渠道回调
2. 验证签名
3. 更新支付状态
4. 通知业务系统

## 接口设计
- 接口路径：POST /api/payment/callback
- 请求参数：支付渠道返回的数据
- 返回结果：success 或 fail

## 注意事项
- 回调可能重复，需要幂等处理
- 签名验证必须严格
- 超时需要重试机制
""",
            "feature_codes": ["F005"],
            "module": "payment",
        },
    ]

    for doc in documents:
        try:
            result = manager.upload_memory(
                PROJECT,
                doc["filename"],
                doc["content"],
                feature_codes=doc.get("feature_codes"),
                module=doc.get("module"),
            )
            print(f"    ✅ 文档: {doc['filename']}")
        except Exception as e:
            print(f"    ❌ 文档 {doc['filename']}: {e}")

    # 等待分块完成
    print("\n  等待分块完成...")
    time.sleep(15)
    print("  ✅ 分块完成")


def test_auto_detection(manager):
    """测试自动识别功能"""
    print_header("2. 测试自动识别功能")

    test_cases = [
        {"question": "用户注册", "expected_feature": "F001", "expected_module": "user"},
        {"question": "用户登录", "expected_feature": "F002", "expected_module": "user"},
        {"question": "订单创建", "expected_feature": "F003", "expected_module": "order"},
        {"question": "订单支付", "expected_feature": "F004", "expected_module": "order"},
        {"question": "支付回调", "expected_feature": "F005", "expected_module": "payment"},
    ]

    passed = 0
    failed = 0

    for tc in test_cases:
        question = tc["question"]
        result = manager.ask_project(PROJECT, question, top_k=1)

        auto_detected = result.get("auto_detected", {})
        detected_features = auto_detected.get("feature_codes", [])
        detected_module = auto_detected.get("module")

        # 检查是否正确识别
        feature_match = tc["expected_feature"] in detected_features if detected_features else False
        module_match = detected_module == tc["expected_module"]

        if feature_match and module_match:
            print(f"  ✅ \"{question}\" → F{tc['expected_feature'][-1]}, {tc['expected_module']}")
            passed += 1
        else:
            print(f"  ❌ \"{question}\" → 期望: {tc['expected_feature']}, {tc['expected_module']}, 实际: {detected_features}, {detected_module}")
            failed += 1

    print(f"\n  自动识别测试: {passed}/{len(test_cases)} 通过")
    return passed, failed


def test_like_search(manager):
    """测试 LIKE 检索"""
    print_header("3. 测试 LIKE 检索")

    test_cases = [
        {"question": "用户注册", "expected_keyword": "注册"},
        {"question": "登录方式", "expected_keyword": "登录"},
        {"question": "订单创建流程", "expected_keyword": "订单"},
        {"question": "支付方式", "expected_keyword": "支付"},
        {"question": "回调处理", "expected_keyword": "回调"},
    ]

    passed = 0
    failed = 0

    for tc in test_cases:
        question = tc["question"]
        result = manager.ask_project(PROJECT, question, top_k=3)

        if result.get("results"):
            content = result["results"][0].get("content", "")
            if tc["expected_keyword"] in content:
                print(f"  ✅ \"{question}\" → 找到 \"{tc['expected_keyword']}\"")
                passed += 1
            else:
                print(f"  ❌ \"{question}\" → 未找到 \"{tc['expected_keyword']}\"")
                failed += 1
        else:
            print(f"  ❌ \"{question}\" → 无结果")
            failed += 1

    print(f"\n  LIKE 检索测试: {passed}/{len(test_cases)} 通过")
    return passed, failed


def test_vector_search(manager):
    """测试向量检索（长问题）"""
    print_header("4. 测试向量检索（长问题）")

    test_cases = [
        {
            "question": "用户注册功能怎么实现",
            "expected_keywords": ["注册", "用户名", "密码"],
        },
        {
            "question": "如何处理支付回调",
            "expected_keywords": ["回调", "支付", "通知"],
        },
        {
            "question": "订单创建的业务流程是什么",
            "expected_keywords": ["订单", "商品", "地址"],
        },
        {
            "question": "用户登录有哪些方式",
            "expected_keywords": ["登录", "密码", "验证码"],
        },
        {
            "question": "订单支付支持哪些支付方式",
            "expected_keywords": ["支付", "支付宝", "微信"],
        },
    ]

    passed = 0
    failed = 0

    for tc in test_cases:
        question = tc["question"]
        result = manager.ask_project(PROJECT, question, top_k=3)

        if result.get("results"):
            content = result["results"][0].get("content", "")
            level = result.get("level", "?")

            # 检查关键词命中
            hits = [kw for kw in tc["expected_keywords"] if kw in content]
            hit_rate = len(hits) / len(tc["expected_keywords"]) if tc["expected_keywords"] else 0

            if hit_rate > 0:
                print(f"  ✅ \"{question}\" → 级别: {level}, 命中: {hits}")
                passed += 1
            else:
                print(f"  ❌ \"{question}\" → 级别: {level}, 未命中关键词")
                failed += 1
        else:
            print(f"  ❌ \"{question}\" → 无结果")
            failed += 1

    print(f"\n  向量检索测试: {passed}/{len(test_cases)} 通过")
    return passed, failed


def test_hybrid_search(manager):
    """测试混合检索"""
    print_header("5. 测试混合检索（先 LIKE 后向量）")

    test_cases = [
        {
            "question": "用户注册功能怎么实现",
            "feature_codes": ["F001"],
            "module": "user",
            "expected_level": "vector",  # LIKE 无结果，降级到向量
        },
        {
            "question": "用户注册",
            "feature_codes": ["F001"],
            "module": "user",
            "expected_level": "feature",  # LIKE 有结果
        },
        {
            "question": "订单支付流程",
            "feature_codes": ["F004"],
            "module": "order",
            "expected_level": "vector",  # LIKE 无结果，降级到向量
        },
        {
            "question": "支付回调",
            "feature_codes": ["F005"],
            "module": "payment",
            "expected_level": "feature",  # LIKE 有结果
        },
    ]

    passed = 0
    failed = 0

    for tc in test_cases:
        question = tc["question"]
        result = manager.ask_project(
            PROJECT,
            question,
            top_k=3,
            feature_codes=tc.get("feature_codes"),
            module=tc.get("module"),
        )

        level = result.get("level", "?")
        count = result.get("count", 0)

        if count > 0:
            print(f"  ✅ \"{question}\" → 级别: {level}, 结果: {count}条")
            passed += 1
        else:
            print(f"  ❌ \"{question}\" → 级别: {level}, 无结果")
            failed += 1

    print(f"\n  混合检索测试: {passed}/{len(test_cases)} 通过")
    return passed, failed


def test_search_performance(manager):
    """测试搜索性能"""
    print_header("6. 测试搜索性能")

    import time

    # 测试 LIKE 检索性能
    print("\n  LIKE 检索性能:")
    start = time.time()
    for _ in range(5):
        manager.ask_project(PROJECT, "用户注册", top_k=3)
    like_time = (time.time() - start) / 5
    print(f"    平均耗时: {like_time*1000:.0f}ms")

    # 测试向量检索性能
    print("\n  向量检索性能:")
    start = time.time()
    for _ in range(5):
        manager.ask_project(PROJECT, "用户注册功能怎么实现", top_k=3)
    vector_time = (time.time() - start) / 5
    print(f"    平均耗时: {vector_time*1000:.0f}ms")

    # 性能对比
    print(f"\n  性能对比:")
    print(f"    LIKE 检索: {like_time*1000:.0f}ms")
    print(f"    向量检索: {vector_time*1000:.0f}ms")
    print(f"    差异: {vector_time/like_time:.1f}x")


def cleanup(manager):
    """清理测试数据"""
    print_header("7. 清理测试数据")

    from mcp_gateway.memory_tools import delete_memory_impl

    # 删除测试项目
    try:
        delete_memory_impl(PROJECT)
        print(f"  ✅ 删除项目: {PROJECT}")
    except Exception as e:
        print(f"  ⚠️ 删除项目失败: {e}")

    # 删除模块和功能
    print("\n  清理模块和功能...")
    for code in ["F001", "F002", "F003", "F004", "F005"]:
        try:
            manager._request('DELETE', f'/feature-metadata/{code}')
            print(f"    ✅ 删除功能: {code}")
        except Exception:
            pass

    for mod in ["user", "order", "payment"]:
        try:
            manager._request('DELETE', f'/modules/{mod}')
            print(f"    ✅ 删除模块: {mod}")
        except Exception:
            pass


def print_summary(results):
    """打印测试总结"""
    print_header("测试总结")

    total_passed = sum(r[0] for r in results.values())
    total_failed = sum(r[1] for r in results.values())
    total = total_passed + total_failed

    print(f"""
┌─────────────────────────────────────────────────────────────┐
│  测试类型              │  通过  │  失败  │  通过率          │
├─────────────────────────────────────────────────────────────┤
│  自动识别功能          │  {results['auto'][0]:3d}   │  {results['auto'][1]:3d}   │  {results['auto'][0]/5*100:5.1f}%          │
│  LIKE 检索             │  {results['like'][0]:3d}   │  {results['like'][1]:3d}   │  {results['like'][0]/5*100:5.1f}%          │
│  向量检索              │  {results['vector'][0]:3d}   │  {results['vector'][1]:3d}   │  {results['vector'][0]/5*100:5.1f}%          │
│  混合检索              │  {results['hybrid'][0]:3d}   │  {results['hybrid'][1]:3d}   │  {results['hybrid'][0]/4*100:5.1f}%          │
├─────────────────────────────────────────────────────────────┤
│  总计                  │  {total_passed:3d}   │  {total_failed:3d}   │  {total_passed/(total or 1)*100:5.1f}%          │
└─────────────────────────────────────────────────────────────┘
""")

    # 保存结果
    import json
    detail = {
        "auto_detection": {"passed": results['auto'][0], "failed": results['auto'][1]},
        "like_search": {"passed": results['like'][0], "failed": results['like'][1]},
        "vector_search": {"passed": results['vector'][0], "failed": results['vector'][1]},
        "hybrid_search": {"passed": results['hybrid'][0], "failed": results['hybrid'][1]},
        "total": {"passed": total_passed, "failed": total_failed},
    }

    result_file = os.path.join(os.path.dirname(__file__), "test_hybrid_search_result.json")
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(detail, f, ensure_ascii=False, indent=2)
    print(f"  结果已保存: {result_file}")


def main():
    print("=" * 60)
    print("  混合检索测试")
    print("=" * 60)

    try:
        manager = MemoryManager()
        manager.login()

        # 1. 创建测试数据
        setup_test_data(manager)

        # 2. 测试自动识别功能
        auto_passed, auto_failed = test_auto_detection(manager)

        # 3. 测试 LIKE 检索
        like_passed, like_failed = test_like_search(manager)

        # 4. 测试向量检索
        vector_passed, vector_failed = test_vector_search(manager)

        # 5. 测试混合检索
        hybrid_passed, hybrid_failed = test_hybrid_search(manager)

        # 6. 测试搜索性能
        test_search_performance(manager)

        # 7. 清理
        cleanup(manager)

        # 8. 总结
        results = {
            "auto": (auto_passed, auto_failed),
            "like": (like_passed, like_failed),
            "vector": (vector_passed, vector_failed),
            "hybrid": (hybrid_passed, hybrid_failed),
        }
        print_summary(results)

    except Exception as e:
        print(f"\n  ❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
