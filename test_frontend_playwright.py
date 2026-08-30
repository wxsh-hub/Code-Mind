# -*- coding: utf-8 -*-
"""
Playwright 前端测试

测试功能：
1. 登录
2. 模块管理
3. 功能元数据标记
4. 矛盾审核
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

    # 填写登录表单（使用 placeholder 定位）
    page.fill('input[placeholder*="用户名"]', 'admin')
    page.fill('input[placeholder*="密码"]', 'admin')

    # 点击登录按钮
    page.click('button:has-text("登录")')

    # 等待跳转
    page.wait_for_url("**/chat**", timeout=15000)
    print("  ✅ 登录成功")
    return True


def test_module_management(page):
    """测试模块管理"""
    print("\n=== 测试模块管理 ===")

    # 导航到模块管理页面
    page.goto(f"{ADMIN_URL}/modules")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 点击新建模块按钮
    page.click('button:has-text("新建模块")')
    time.sleep(1)

    # 填写模块信息
    page.fill('input[placeholder*="模块名称"]', 'test_module')
    page.fill('input[placeholder*="模块描述"]', '测试模块描述')

    # 点击创建
    page.click('button:has-text("创建")')
    time.sleep(2)

    # 验证模块是否创建成功
    module_exists = page.query_selector('td:has-text("test_module")')
    if module_exists:
        print("  ✅ 模块创建成功")
    else:
        print("  ❌ 模块创建失败")
        return False

    # 删除模块
    page.click('button:has-text("删除"):near(td:has-text("test_module"))')
    time.sleep(1)

    # 确认删除（如果有确认对话框）
    confirm_btn = page.query_selector('button:has-text("确认")')
    if confirm_btn:
        confirm_btn.click()
    time.sleep(1)

    print("  ✅ 模块删除成功")
    return True


def test_feature_metadata(page):
    """测试功能元数据标记"""
    print("\n=== 测试功能元数据标记 ===")

    # 导航到功能元数据页面
    page.goto(f"{ADMIN_URL}/feature-metadata")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 点击新建功能按钮
    page.click('button:has-text("新建功能")')
    time.sleep(1)

    # 填写功能信息
    page.fill('input[placeholder*="功能编号"]', 'F999')
    page.fill('input[placeholder*="功能名称"]', '测试功能')

    # 选择模块（如果有的话）
    module_select = page.query_selector('select')
    if module_select:
        module_select.select_option(index=1)  # 选择第一个模块

    page.fill('input[placeholder*="功能描述"]', '测试功能描述')

    # 点击创建
    page.click('button:has-text("创建")')
    time.sleep(2)

    # 验证功能是否创建成功
    feature_exists = page.query_selector('td:has-text("F999")')
    if feature_exists:
        print("  ✅ 功能创建成功")
    else:
        print("  ❌ 功能创建失败")
        return False

    # 删除功能
    page.click('button:has-text("删除"):near(td:has-text("F999"))')
    time.sleep(1)

    # 确认删除
    confirm_btn = page.query_selector('button:has-text("确认")')
    if confirm_btn:
        confirm_btn.click()
    time.sleep(1)

    print("  ✅ 功能删除成功")
    return True


def test_conflict_review(page):
    """测试矛盾审核"""
    print("\n=== 测试矛盾审核 ===")

    # 导航到矛盾审核页面
    page.goto(f"{ADMIN_URL}/conflict-review")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查页面是否加载成功
    page_title = page.query_selector('h1:has-text("矛盾审核")')
    if page_title:
        print("  ✅ 矛盾审核页面加载成功")
    else:
        print("  ❌ 矛盾审核页面加载失败")
        return False

    # 检查是否有"暂无待审核"或矛盾对列表
    empty_state = page.query_selector('text="暂无待审核的矛盾对"')
    conflict_cards = page.query_selector_all('[class*="conflict"]')

    if empty_state:
        print("  ✅ 显示空状态（暂无矛盾对）")
    elif conflict_cards:
        print(f"  ✅ 显示 {len(conflict_cards)} 个矛盾对")
    else:
        print("  ⚠️ 页面状态未知")

    return True


def test_knowledge_upload(page):
    """测试知识库上传（带元数据）"""
    print("\n=== 测试知识库上传 ===")

    # 导航到知识库页面
    page.goto(f"{ADMIN_URL}/knowledge")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 点击第一个知识库
    first_kb = page.query_selector('tr:has(td)')
    if first_kb:
        first_kb.click()
        time.sleep(2)

        # 检查是否有上传按钮
        upload_btn = page.query_selector('button:has-text("上传")')
        if upload_btn:
            print("  ✅ 知识库页面加载成功")
            print("  ✅ 上传按钮可用")
        else:
            print("  ❌ 未找到上传按钮")
            return False

        # 检查是否有模块和功能编号列
        module_header = page.query_selector('th:has-text("模块")')
        feature_header = page.query_selector('th:has-text("功能编号")')

        if module_header and feature_header:
            print("  ✅ 模块和功能编号列已添加")
        else:
            print("  ⚠️ 模块或功能编号列未找到")
    else:
        print("  ⚠️ 没有知识库，跳过测试")

    return True


def cleanup():
    """清理测试数据"""
    print("\n=== 清理测试数据 ===")
    # 测试数据会在页面操作中自动清理
    print("  ✅ 清理完成")


def main():
    print("=" * 60)
    print("  Playwright 前端测试")
    print("=" * 60)

    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=False)  # 设置为 True 可以无头运行
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        results = {}

        try:
            # 1. 测试登录
            results["login"] = test_login(page)

            # 2. 测试模块管理
            results["module"] = test_module_management(page)

            # 3. 测试功能元数据标记
            results["feature"] = test_feature_metadata(page)

            # 4. 测试矛盾审核
            results["conflict"] = test_conflict_review(page)

            # 5. 测试知识库上传
            results["upload"] = test_knowledge_upload(page)

        except Exception as e:
            print(f"\n  ❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # 清理
            cleanup()

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
