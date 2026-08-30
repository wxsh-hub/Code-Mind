# -*- coding: utf-8 -*-
"""
全链路端到端测试
"""

import sys
import io
import time
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.path.insert(0, '.')

from mcp_gateway.memory_tools import MemoryManager, MemoryConfig
from mcp_gateway.rag_client import RAGClient, RAGConfig

PROJECT = "E2ETest_" + str(int(time.time()))


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(label, result):
    if isinstance(result, dict):
        status = result.get("status", "unknown")
        icon = "✅" if status == "success" else "❌"
        print(f"    {icon} {label}: {status}")
        if "error" in result:
            print(f"       error: {result['error']}")
    else:
        print(f"    {label}: {result}")


def setup(manager):
    print_section("1. 初始化：创建模块和功能")

    print("\n  创建模块...")
    for name, desc in [("user", "用户管理模块"), ("order", "订单管理模块")]:
        try:
            result = manager._request("POST", "/modules", {"name": name, "description": desc})
            code = result.get("code", "")
            if code == "0":
                print(f"    ✅ create_module({name})")
            else:
                print(f"    ⚠️ create_module({name}): {result.get('message', code)}")
        except Exception as e:
            print(f"    ⚠️ create_module({name}): {e}")

    print("\n  创建功能...")
    features = [
        ("F001", "用户注册", "user"),
        ("F002", "用户登录", "user"),
        ("F003", "订单创建", "order"),
    ]
    for code, fname, mod in features:
        try:
            result = manager._request("POST", "/feature-metadata", {
                "featureCode": code, "featureName": fname, "moduleName": mod,
            })
            rcode = result.get("code", "")
            if rcode == "0":
                print(f"    ✅ create_feature({code}: {fname})")
            else:
                print(f"    ⚠️ create_feature({code}): {result.get('message', rcode)}")
        except Exception as e:
            print(f"    ⚠️ create_feature({code}): {e}")


def upload_memories(manager):
    print_section("2. 上传项目记忆")

    memories = [
        {
            "filename": "用户注册指南.md",
            "content": "# 用户注册指南\n\n## 功能说明\n用户注册是系统的核心功能之一，允许新用户创建账号。\n\n## 实现要点\n1. 用户名：3-20个字符\n2. 密码：8-32个字符，必须包含大小写字母和数字\n3. 邮箱：有效的邮箱格式\n4. 手机号：11位手机号码\n\n## 接口设计\n- 接口路径：POST /api/user/register\n- 请求参数：username, password, email, phone\n- 返回结果：用户ID和token\n\n## 注意事项\n- 用户名不能重复\n- 密码需要加密存储\n- 注册成功后自动登录\n",
            "feature_codes": ["F001"],
            "module": "user",
        },
        {
            "filename": "用户登录指南.md",
            "content": "# 用户登录指南\n\n## 功能说明\n用户登录允许已注册用户访问系统。\n\n## 登录方式\n1. 用户名+密码登录\n2. 手机号+验证码登录\n3. 第三方OAuth登录\n\n## 接口设计\n- 接口路径：POST /api/user/login\n- 请求参数：username, password\n- 返回结果：token和用户信息\n\n## 安全措施\n- 登录失败5次锁定账号\n- Token有效期2小时\n- 支持刷新Token\n",
            "feature_codes": ["F002"],
            "module": "user",
        },
        {
            "filename": "订单创建流程.md",
            "content": "# 订单创建流程\n\n## 功能说明\n订单创建是电商系统的核心流程。\n\n## 创建步骤\n1. 选择商品\n2. 确认收货地址\n3. 选择支付方式\n4. 提交订单\n\n## 接口设计\n- 接口路径：POST /api/order/create\n- 请求参数：items[], addressId, paymentMethod\n- 返回结果：订单号和订单状态\n\n## 业务规则\n- 库存不足时提示\n- 优惠券自动计算\n- 订单超时30分钟自动取消\n",
            "feature_codes": ["F003"],
            "module": "order",
        },
        {
            "filename": "项目架构说明.md",
            "content": "# Code-Mind 项目架构\n\n## 技术栈\n- 后端：Spring Boot 4.1 + MyBatis-Plus\n- 数据库：PostgreSQL + pgvector\n- 缓存：Redis\n- 消息队列：RocketMQ\n- AI模型：Qwen3-Embedding-8B\n\n## 模块划分\n- agent：Agent执行架构\n- bootstrap：启动装配层\n- framework：通用基础能力\n- infra-ai：AI模型客户端\n- rag：RAG检索与知识库管理\n- system：用户认证与审计\n",
            "feature_codes": [],
            "module": None,
        },
    ]

    for mem in memories:
        print(f"\n  上传: {mem['filename']}")
        result = manager.upload_memory(
            PROJECT, mem["filename"], mem["content"],
            feature_codes=mem.get("feature_codes"), module=mem.get("module"),
        )
        print_result(f"upload({mem['filename']})", result)

    # 等待分块完成（轮询检查）
    print("\n  等待分块完成...")
    client = RAGClient()
    client.login()
    kb_id = manager.get_or_create_project_kb(PROJECT)

    for i in range(12):
        time.sleep(5)
        try:
            results = client.search_similar("用户注册", kb_id=kb_id, top_k=1)
            if results:
                print(f"  ✅ 分块完成（{(i+1)*5}秒），找到 {len(results)} 条结果")
                return True
        except Exception:
            pass
        print(f"  等待中... ({(i+1)*5}秒)")

    print("  ⚠️ 等待超时")
    return False


def test_search_recall(manager):
    print_section("3. 测试搜索召回率")

    # 使用短查询词（LIKE 搜索需要精确匹配子串）
    test_cases = [
        {"q": "用户注册", "fc": ["F001"], "mod": "user", "kw": ["注册", "用户"]},
        {"q": "用户登录", "fc": ["F002"], "mod": "user", "kw": ["登录", "密码"]},
        {"q": "订单创建", "fc": ["F003"], "mod": "order", "kw": ["订单", "商品"]},
        {"q": "技术栈", "fc": None, "mod": None, "kw": ["Spring", "PostgreSQL"]},
        {"q": "密码", "fc": None, "mod": "user", "kw": ["密码"]},
    ]

    passed = 0
    failed = 0

    for tc in test_cases:
        print(f"\n  问题: {tc['q']}")
        fc_str = f"feature={tc['fc']}, module={tc['mod']}" if tc.get('fc') else f"module={tc['mod']}" if tc.get('mod') else "全库"
        print(f"  检索范围: {fc_str}")

        result = manager.ask_project(
            PROJECT, tc["q"], top_k=3,
            feature_codes=tc.get("fc"), module=tc.get("mod"),
        )

        results = result.get("results", [])
        level = result.get("level", "?")
        print(f"  检索级别: {level}, 返回数量: {len(results)}")

        if results:
            content = results[0].get("content", "")
            score = results[0].get("score", 0)
            hits = [kw for kw in tc["kw"] if kw in content]
            hit_rate = len(hits) / len(tc["kw"]) if tc["kw"] else 1
            print(f"    score={score}, 关键词命中={hits} ({hit_rate:.0%})")
            print(f"    内容: {content[:80]}...")
            if hit_rate > 0:
                print(f"  ✅ 通过")
                passed += 1
            else:
                print(f"  ❌ 失败: 未命中关键词")
                failed += 1
        else:
            print(f"  ❌ 失败: 无结果")
            failed += 1

    print(f"\n  总结: {passed} 通过, {failed} 失败")
    return failed == 0


def test_score_and_confidence(manager):
    print_section("4. 测试分数和置信度")

    client = RAGClient()
    client.login()
    kb_id = manager.get_or_create_project_kb(PROJECT)

    print("\n  搜索并检查分数...")
    results = client.search_similar("用户注册", kb_id=kb_id, top_k=3)
    print(f"  返回 {len(results)} 条结果")
    for i, r in enumerate(results[:3]):
        print(f"  [{i+1}] score={r.get('score', 'N/A')}, confidence={r.get('confidence', 'N/A')}")
        print(f"      {r.get('content', '')[:60]}...")
    return len(results) > 0


def test_batch_ops():
    print_section("5. 测试批量操作")

    from mcp_gateway.memory_tools import batch_upload_memories_impl, batch_delete_memories_impl

    batch_project = PROJECT + "_batch"

    print("\n  批量上传...")
    files = [
        {"filename": "doc1.md", "content": "# 文档1\n\n批量测试文档一"},
        {"filename": "doc2.md", "content": "# 文档2\n\n批量测试文档二"},
        {"filename": "doc3.md", "content": "# 文档3\n\n批量测试文档三"},
    ]
    result = batch_upload_memories_impl(batch_project, files)
    print(f"    上传: {result.get('success')}/{result.get('total')} 成功")

    time.sleep(5)

    print("\n  批量删除...")
    result = batch_delete_memories_impl(batch_project, ["doc1.md", "doc2.md", "doc3.md"])
    print(f"    删除: {result.get('deleted')} 个")
    return result.get("deleted", 0) == 3


def test_list_projects():
    print_section("6. 测试列出项目")

    from mcp_gateway.memory_tools import list_projects_impl
    result = list_projects_impl()
    projects = result.get("projects", [])
    print(f"\n  共 {len(projects)} 个项目:")
    for p in projects:
        print(f"    - {p.get('project')}")
    return len(projects) > 0


def cleanup(manager):
    print_section("7. 清理测试数据")

    from mcp_gateway.memory_tools import delete_memory_impl

    for suffix in ["", "_batch"]:
        project = PROJECT + suffix
        try:
            result = delete_memory_impl(project)
            print(f"    ✅ delete({project})")
        except Exception as e:
            print(f"    ⚠️ delete({project}): {e}")

    print("\n  清理模块和功能...")
    client = RAGClient()
    client.login()
    for code in ["F001", "F002", "F003"]:
        try:
            client.delete_feature(code)
            print(f"    ✅ delete_feature({code})")
        except Exception:
            pass
    for mod in ["user", "order"]:
        try:
            client.delete_module(mod)
            print(f"    ✅ delete_module({mod})")
        except Exception:
            pass


def main():
    print("=" * 60)
    print(f"  Code-Mind 全链路端到端测试")
    print(f"  项目名: {PROJECT}")
    print("=" * 60)

    try:
        manager = MemoryManager()
        manager.login()

        setup(manager)
        chunks_ready = upload_memories(manager)
        search_ok = test_search_recall(manager) if chunks_ready else False
        score_ok = test_score_and_confidence(manager)
        batch_ok = test_batch_ops()
        list_ok = test_list_projects()
        cleanup(manager)

        print_section("测试总结")
        tests = {
            "模块/功能创建": "⚠️ 需检查",
            "文档上传": "✅" if chunks_ready else "❌",
            "搜索召回": "✅" if search_ok else "❌",
            "分数/置信度": "✅" if score_ok else "❌",
            "批量操作": "✅" if batch_ok else "❌",
            "列出项目": "✅" if list_ok else "❌",
        }
        for name, status in tests.items():
            print(f"  {name}: {status}")

        if search_ok and score_ok:
            print("\n  ✅ 全链路测试通过！")
        else:
            print("\n  ⚠️ 部分测试未通过")

    except Exception as e:
        print(f"\n  ❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
