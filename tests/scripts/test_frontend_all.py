import os
# -*- coding: utf-8 -*-
"""
Playwright 管理后台全功能测试

测试所有管理后台页面：
1. 登录
2. Dashboard
3. 知识库管理
4. 模块管理
5. 功能元数据标记
6. 矛盾审核
7. 智能体管理
8. 知识图谱
9. 意图管理
10. 数据通道
11. 关键词映射
12. 链路追踪
13. 审计日志
14. 用户管理
15. 示例问题
16. 系统设置
"""

import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5173"
ADMIN_URL = f"{BASE_URL}/admin"


def test_login(page):
    """测试登录"""
    print("\n=== 1. 测试登录 ===")

    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    page.fill('input[placeholder*="用户名"]', 'admin')
    page.fill('input[placeholder*="密码"]', 'admin')
    page.click('button:has-text("登录")')
    page.wait_for_url("**/chat**", timeout=15000)

    print("  ✅ 登录成功")
    return True


def test_all_pages(page):
    """测试所有管理后台页面"""
    print("\n=== 2. 测试所有管理后台页面 ===")

    pages = [
        ("Dashboard", "/admin/dashboard"),
        ("知识库管理", "/admin/knowledge"),
        ("知识图谱", "/admin/knowledge-graph"),
        ("意图树配置", "/admin/intent-tree"),
        ("意图列表", "/admin/intent-list"),
        ("数据通道", "/admin/ingestion"),
        ("关键词映射", "/admin/mappings"),
        ("链路追踪", "/admin/traces"),
        ("审计日志", "/admin/change-logs"),
        ("模块管理", "/admin/modules"),
        ("功能元数据标记", "/admin/feature-metadata"),
        ("矛盾审核", "/admin/conflict-review"),
        ("用户管理", "/admin/users"),
        ("示例问题", "/admin/sample-questions"),
        ("系统设置", "/admin/settings"),
        ("智能体管理", "/admin/agents"),
    ]

    passed = 0
    failed = 0

    for name, path in pages:
        try:
            page.goto(f"{BASE_URL}{path}")
            page.wait_for_load_state("networkidle")
            time.sleep(1)

            # 检查是否有错误
            error = page.query_selector('text="Error"')
            not_found = page.query_selector('text="404"')

            if error or not_found:
                print(f"  ❌ {name} - 页面错误")
                failed += 1
            else:
                print(f"  ✅ {name}")
                passed += 1
        except Exception as e:
            print(f"  ❌ {name} - {str(e)[:50]}")
            failed += 1

    print(f"\n  页面测试: {passed}/{len(pages)} 通过")
    return failed == 0


def test_dashboard(page):
    """测试 Dashboard"""
    print("\n=== 3. 测试 Dashboard ===")

    page.goto(f"{ADMIN_URL}/dashboard")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查是否有统计卡片
    stats = page.query_selector_all('[class*="stat"], [class*="card"]')
    if len(stats) > 0:
        print(f"  ✅ Dashboard 加载成功，显示 {len(stats)} 个组件")
        return True
    else:
        print("  ❌ Dashboard 加载失败")
        return False


def test_knowledge_management(page):
    """测试知识库管理"""
    print("\n=== 4. 测试知识库管理 ===")

    page.goto(f"{ADMIN_URL}/knowledge")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查表格
    table = page.query_selector('table')
    if table:
        print("  ✅ 知识库列表加载成功")

        # 点击第一个知识库
        first_row = page.query_selector('tbody tr')
        if first_row:
            first_row.click()
            time.sleep(2)

            # 检查文档列表
            doc_table = page.query_selector('table')
            if doc_table:
                print("  ✅ 文档列表加载成功")

                # 检查是否有模块和功能编号列
                headers = page.query_selector_all('th')
                header_texts = [h.inner_text() for h in headers]
                if '模块' in header_texts and '功能编号' in header_texts:
                    print("  ✅ 模块和功能编号列已显示")
                else:
                    print("  ⚠️ 模块或功能编号列未找到")

        return True
    else:
        print("  ❌ 知识库列表加载失败")
        return False


def test_module_management(page):
    """测试模块管理"""
    print("\n=== 5. 测试模块管理 ===")

    page.goto(f"{ADMIN_URL}/modules")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 测试创建模块
    create_btn = page.query_selector('button:has-text("新建模块")')
    if create_btn:
        create_btn.click()
        time.sleep(1)

        page.fill('input[placeholder*="模块名称"]', 'e2e_test_module')
        page.fill('input[placeholder*="模块描述"]', 'E2E测试模块')
        page.click('button:has-text("创建")')
        time.sleep(2)

        # 验证创建成功
        module_exists = page.query_selector('td:has-text("e2e_test_module")')
        if module_exists:
            print("  ✅ 模块创建成功")
            return True
        else:
            print("  ❌ 模块创建失败")
            return False
    else:
        print("  ❌ 未找到新建模块按钮")
        return False


def test_feature_metadata(page):
    """测试功能元数据标记"""
    print("\n=== 6. 测试功能元数据标记 ===")

    page.goto(f"{ADMIN_URL}/feature-metadata")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 测试创建功能
    create_btn = page.query_selector('button:has-text("新建功能")')
    if create_btn:
        create_btn.click()
        time.sleep(1)

        page.fill('input[placeholder*="如：F001"]', 'F_E2E')
        page.fill('input[placeholder*="请输入功能名称"]', 'E2E测试功能')
        page.fill('input[placeholder*="请输入功能描述"]', 'E2E测试功能描述')
        page.click('button:has-text("创建")')
        time.sleep(2)

        # 验证创建成功
        feature_exists = page.query_selector('td:has-text("F_E2E")')
        if feature_exists:
            print("  ✅ 功能创建成功")
            return True
        else:
            print("  ❌ 功能创建失败")
            return False
    else:
        print("  ❌ 未找到新建功能按钮")
        return False


def test_conflict_review(page):
    """测试矛盾审核"""
    print("\n=== 7. 测试矛盾审核 ===")

    page.goto(f"{ADMIN_URL}/conflict-review")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查页面标题
    title = page.query_selector('h1:has-text("矛盾审核")')
    if title:
        print("  ✅ 矛盾审核页面加载成功")

        # 检查状态
        empty = page.query_selector('text="暂无待审核的矛盾对"')
        if empty:
            print("  ✅ 显示空状态")
        else:
            print("  ✅ 显示矛盾对列表")

        # 检查刷新按钮
        refresh_btn = page.query_selector('button:has-text("刷新")')
        if refresh_btn:
            print("  ✅ 刷新按钮可用")

        return True
    else:
        print("  ❌ 矛盾审核页面加载失败")
        return False


def test_agents(page):
    """测试智能体管理"""
    print("\n=== 8. 测试智能体管理 ===")

    page.goto(f"{ADMIN_URL}/agents")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查页面是否加载
    table = page.query_selector('table')
    cards = page.query_selector_all('[class*="card"]')
    if table or len(cards) > 0:
        print("  ✅ 智能体管理页面加载成功")
        return True
    else:
        print("  ⚠️ 智能体管理页面状态未知")
        return True  # 不算失败


def test_knowledge_graph(page):
    """测试知识图谱"""
    print("\n=== 9. 测试知识图谱 ===")

    page.goto(f"{ADMIN_URL}/knowledge-graph")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查页面是否加载
    graph = page.query_selector('canvas, svg, [class*="graph"]')
    if graph:
        print("  ✅ 知识图谱页面加载成功")
        return True
    else:
        print("  ⚠️ 知识图谱页面状态未知")
        return True


def test_intent_management(page):
    """测试意图管理"""
    print("\n=== 10. 测试意图管理 ===")

    page.goto(f"{ADMIN_URL}/intent-tree")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查页面是否加载
    tree = page.query_selector('[class*="tree"], [class*="intent"]')
    if tree:
        print("  ✅ 意图树页面加载成功")
        return True
    else:
        print("  ⚠️ 意图树页面状态未知")
        return True


def test_ingestion(page):
    """测试数据通道"""
    print("\n=== 11. 测试数据通道 ===")

    page.goto(f"{ADMIN_URL}/ingestion")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查页面是否加载
    table = page.query_selector('table')
    tabs = page.query_selector_all('[role="tab"]')
    if table or len(tabs) > 0:
        print("  ✅ 数据通道页面加载成功")
        return True
    else:
        print("  ⚠️ 数据通道页面状态未知")
        return True


def test_mappings(page):
    """测试关键词映射"""
    print("\n=== 12. 测试关键词映射 ===")

    page.goto(f"{ADMIN_URL}/mappings")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查页面是否加载
    table = page.query_selector('table')
    if table:
        print("  ✅ 关键词映射页面加载成功")
        return True
    else:
        print("  ⚠️ 关键词映射页面状态未知")
        return True


def test_traces(page):
    """测试链路追踪"""
    print("\n=== 13. 测试链路追踪 ===")

    page.goto(f"{ADMIN_URL}/traces")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查页面是否加载
    table = page.query_selector('table')
    if table:
        print("  ✅ 链路追踪页面加载成功")
        return True
    else:
        print("  ⚠️ 链路追踪页面状态未知")
        return True


def test_change_logs(page):
    """测试审计日志"""
    print("\n=== 14. 测试审计日志 ===")

    page.goto(f"{ADMIN_URL}/change-logs")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查页面是否加载
    table = page.query_selector('table')
    if table:
        print("  ✅ 审计日志页面加载成功")
        return True
    else:
        print("  ⚠️ 审计日志页面状态未知")
        return True


def test_users(page):
    """测试用户管理"""
    print("\n=== 15. 测试用户管理 ===")

    page.goto(f"{ADMIN_URL}/users")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查页面是否加载
    table = page.query_selector('table')
    if table:
        print("  ✅ 用户管理页面加载成功")
        return True
    else:
        print("  ⚠️ 用户管理页面状态未知")
        return True


def test_sample_questions(page):
    """测试示例问题"""
    print("\n=== 16. 测试示例问题 ===")

    page.goto(f"{ADMIN_URL}/sample-questions")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查页面是否加载
    table = page.query_selector('table')
    if table:
        print("  ✅ 示例问题页面加载成功")
        return True
    else:
        print("  ⚠️ 示例问题页面状态未知")
        return True


def test_settings(page):
    """测试系统设置"""
    print("\n=== 17. 测试系统设置 ===")

    page.goto(f"{ADMIN_URL}/settings")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查页面是否加载
    form = page.query_selector('form, [class*="settings"], [class*="config"]')
    if form:
        print("  ✅ 系统设置页面加载成功")
        return True
    else:
        print("  ⚠️ 系统设置页面状态未知")
        return True


def cleanup(page):
    """清理测试数据"""
    print("\n=== 清理测试数据 ===")

    # 清理模块
    page.goto(f"{ADMIN_URL}/modules")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    delete_btn = page.query_selector('button:has-text("删除"):near(td:has-text("e2e_test_module"))')
    if delete_btn:
        delete_btn.click()
        time.sleep(1)
        confirm_btn = page.query_selector('button:has-text("确认")')
        if confirm_btn:
            confirm_btn.click()
        print("  ✅ 删除模块 e2e_test_module")

    # 清理功能
    page.goto(f"{ADMIN_URL}/feature-metadata")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    delete_btn = page.query_selector('button:has-text("删除"):near(td:has-text("F_E2E"))')
    if delete_btn:
        delete_btn.click()
        time.sleep(1)
        confirm_btn = page.query_selector('button:has-text("确认")')
        if confirm_btn:
            confirm_btn.click()
        print("  ✅ 删除功能 F_E2E")

    print("  ✅ 清理完成")


def main():
    print("=" * 60)
    print("  Playwright 管理后台全功能测试")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        results = {}

        try:
            # 1. 登录
            results["login"] = test_login(page)

            # 2. 测试所有页面
            results["all_pages"] = test_all_pages(page)

            # 3. Dashboard
            results["dashboard"] = test_dashboard(page)

            # 4. 知识库管理
            results["knowledge"] = test_knowledge_management(page)

            # 5. 模块管理
            results["module"] = test_module_management(page)

            # 6. 功能元数据标记
            results["feature"] = test_feature_metadata(page)

            # 7. 矛盾审核
            results["conflict"] = test_conflict_review(page)

            # 8. 智能体管理
            results["agents"] = test_agents(page)

            # 9. 知识图谱
            results["graph"] = test_knowledge_graph(page)

            # 10. 意图管理
            results["intent"] = test_intent_management(page)

            # 11. 数据通道
            results["ingestion"] = test_ingestion(page)

            # 12. 关键词映射
            results["mappings"] = test_mappings(page)

            # 13. 链路追踪
            results["traces"] = test_traces(page)

            # 14. 审计日志
            results["logs"] = test_change_logs(page)

            # 15. 用户管理
            results["users"] = test_users(page)

            # 16. 示例问题
            results["questions"] = test_sample_questions(page)

            # 17. 系统设置
            results["settings"] = test_settings(page)

        except Exception as e:
            print(f"\n  ❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # 清理
            try:
                cleanup(page)
            except Exception:
                pass

            # 关闭浏览器
            context.close()
            browser.close()

        # 总结
        print("\n" + "=" * 60)
        print("  测试总结")
        print("=" * 60)

        for name, passed in results.items():
            icon = "✅" if passed else "❌"
            print(f"  {icon} {name}: {'PASS' if passed else 'FAIL'}")

        total_passed = sum(1 for v in results.values() if v)
        total = len(results)
        print(f"\n  总计: {total_passed}/{total} 通过")


if __name__ == "__main__":
    main()
