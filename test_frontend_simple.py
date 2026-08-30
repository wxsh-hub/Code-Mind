# -*- coding: utf-8 -*-
"""
Playwright 前端测试（简化版）

测试功能：
1. 登录
2. 导航到各页面
3. 模块管理
4. 功能元数据标记
5. 矛盾审核
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
    print("\n=== 测试登录 ===")

    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 填写登录表单
    page.fill('input[placeholder*="用户名"]', 'admin')
    page.fill('input[placeholder*="密码"]', 'admin')
    page.click('button:has-text("登录")')

    # 等待跳转
    page.wait_for_url("**/chat**", timeout=15000)
    print("  ✅ 登录成功")
    return True


def test_navigation(page):
    """测试页面导航"""
    print("\n=== 测试页面导航 ===")

    pages = [
        ("模块管理", f"{ADMIN_URL}/modules"),
        ("功能元数据标记", f"{ADMIN_URL}/feature-metadata"),
        ("矛盾审核", f"{ADMIN_URL}/conflict-review"),
        ("知识库管理", f"{ADMIN_URL}/knowledge"),
        ("Dashboard", f"{ADMIN_URL}/dashboard"),
    ]

    passed = 0
    for name, url in pages:
        try:
            page.goto(url)
            page.wait_for_load_state("networkidle")
            time.sleep(1)

            # 检查页面是否加载成功（没有错误）
            error = page.query_selector('text="Error"')
            if not error:
                print(f"  ✅ {name} 页面加载成功")
                passed += 1
            else:
                print(f"  ❌ {name} 页面加载失败")
        except Exception as e:
            print(f"  ❌ {name} 页面异常: {e}")

    print(f"\n  导航测试: {passed}/{len(pages)} 通过")
    return passed == len(pages)


def test_module_management(page):
    """测试模块管理"""
    print("\n=== 测试模块管理 ===")

    page.goto(f"{ADMIN_URL}/modules")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 点击新建模块按钮
    create_btn = page.query_selector('button:has-text("新建模块")')
    if create_btn:
        create_btn.click()
        time.sleep(1)

        # 填写模块信息
        page.fill('input[placeholder*="模块名称"]', 'playwright_test')
        page.fill('input[placeholder*="模块描述"]', 'Playwright 测试模块')

        # 点击创建
        page.click('button:has-text("创建")')
        time.sleep(2)

        # 验证模块是否创建成功
        module_exists = page.query_selector('td:has-text("playwright_test")')
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
    print("\n=== 测试功能元数据标记 ===")

    page.goto(f"{ADMIN_URL}/feature-metadata")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 点击新建功能按钮
    create_btn = page.query_selector('button:has-text("新建功能")')
    if create_btn:
        create_btn.click()
        time.sleep(1)

        # 填写功能信息（使用实际的 placeholder）
        page.fill('input[placeholder*="如：F001"]', 'F_PLAYWRIGHT')
        page.fill('input[placeholder*="请输入功能名称"]', 'Playwright测试功能')
        page.fill('input[placeholder*="请输入功能描述"]', 'Playwright 测试功能描述')

        # 点击创建
        page.click('button:has-text("创建")')
        time.sleep(2)

        # 验证功能是否创建成功
        feature_exists = page.query_selector('td:has-text("F_PLAYWRIGHT")')
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
    print("\n=== 测试矛盾审核 ===")

    page.goto(f"{ADMIN_URL}/conflict-review")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查页面标题
    title = page.query_selector('h1:has-text("矛盾审核")')
    if title:
        print("  ✅ 矛盾审核页面加载成功")

        # 检查是否有"暂无待审核"或矛盾对列表
        empty_state = page.query_selector('text="暂无待审核的矛盾对"')
        if empty_state:
            print("  ✅ 显示空状态（暂无矛盾对）")
        else:
            print("  ✅ 显示矛盾对列表")

        return True
    else:
        print("  ❌ 矛盾审核页面加载失败")
        return False


def test_knowledge_list(page):
    """测试知识库列表"""
    print("\n=== 测试知识库列表 ===")

    page.goto(f"{ADMIN_URL}/knowledge")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查页面是否加载成功
    table = page.query_selector('table')
    if table:
        print("  ✅ 知识库列表加载成功")
        return True
    else:
        print("  ❌ 知识库列表加载失败")
        return False


def cleanup(page):
    """清理测试数据"""
    print("\n=== 清理测试数据 ===")

    # 清理模块
    page.goto(f"{ADMIN_URL}/modules")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    # 删除 playwright_test 模块
    delete_btn = page.query_selector('button:has-text("删除"):near(td:has-text("playwright_test"))')
    if delete_btn:
        delete_btn.click()
        time.sleep(1)
        confirm_btn = page.query_selector('button:has-text("确认")')
        if confirm_btn:
            confirm_btn.click()
        print("  ✅ 删除模块 playwright_test")

    # 清理功能
    page.goto(f"{ADMIN_URL}/feature-metadata")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    # 删除 F_PLAYWRIGHT 功能
    delete_btn = page.query_selector('button:has-text("删除"):near(td:has-text("F_PLAYWRIGHT"))')
    if delete_btn:
        delete_btn.click()
        time.sleep(1)
        confirm_btn = page.query_selector('button:has-text("确认")')
        if confirm_btn:
            confirm_btn.click()
        print("  ✅ 删除功能 F_PLAYWRIGHT")

    print("  ✅ 清理完成")


def main():
    print("=" * 60)
    print("  Playwright 前端测试（简化版）")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        results = {}

        try:
            # 1. 测试登录
            results["login"] = test_login(page)

            # 2. 测试页面导航
            results["navigation"] = test_navigation(page)

            # 3. 测试模块管理
            results["module"] = test_module_management(page)

            # 4. 测试功能元数据标记
            results["feature"] = test_feature_metadata(page)

            # 5. 测试矛盾审核
            results["conflict"] = test_conflict_review(page)

            # 6. 测试知识库列表
            results["knowledge"] = test_knowledge_list(page)

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
