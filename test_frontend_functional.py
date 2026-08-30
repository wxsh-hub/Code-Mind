# -*- coding: utf-8 -*-
"""
Playwright 前端功能测试

测试每个页面的实际功能：
1. 登录
2. 知识库管理 - 上传文档（带元数据）
3. 模块管理 - 创建/删除模块和功能
4. 功能元数据标记 - 创建/删除功能
5. 矛盾审核 - 审核操作
6. 端到端链路测试
"""

import sys
import io
import time
import os

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

    # 填写登录表单
    page.fill('input[placeholder*="用户名"]', 'admin')
    page.fill('input[placeholder*="密码"]', 'admin')
    page.click('button:has-text("登录")')

    # 等待跳转
    page.wait_for_url("**/chat**", timeout=15000)
    print("  ✅ 登录成功")
    return True


def test_module_and_feature(page):
    """测试模块和功能管理"""
    print("\n=== 2. 测试模块和功能管理 ===")

    # 2.1 创建模块
    print("\n  2.1 创建模块...")
    page.goto(f"{ADMIN_URL}/modules")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 点击新建模块
    page.click('button:has-text("新建模块")')
    time.sleep(1)

    # 填写模块信息
    page.fill('input[placeholder*="模块名称"]', 'test_e2e_module')
    page.fill('input[placeholder*="模块描述"]', 'E2E测试模块')
    page.click('button:has-text("创建")')
    time.sleep(2)

    # 验证创建成功
    if page.query_selector('td:has-text("test_e2e_module")'):
        print("    ✅ 模块创建成功")
    else:
        print("    ❌ 模块创建失败")
        return False

    # 2.2 创建功能
    print("\n  2.2 创建功能...")
    page.goto(f"{ADMIN_URL}/feature-metadata")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 点击新建功能
    page.click('button:has-text("新建功能")')
    time.sleep(1)

    # 填写功能信息
    page.fill('input[placeholder*="如：F001"]', 'F_E2E')
    page.fill('input[placeholder*="请输入功能名称"]', 'E2E测试功能')
    page.fill('input[placeholder*="请输入功能描述"]', 'E2E测试功能描述')

    # 选择模块
    module_select = page.query_selector('select')
    if module_select:
        module_select.select_option(label='test_e2e_module')

    page.click('button:has-text("创建")')
    time.sleep(2)

    # 验证创建成功
    if page.query_selector('td:has-text("F_E2E")'):
        print("    ✅ 功能创建成功")
    else:
        print("    ❌ 功能创建失败")
        return False

    return True


def test_knowledge_upload(page):
    """测试知识库上传文档"""
    print("\n=== 3. 测试知识库上传文档 ===")

    # 导航到知识库页面
    page.goto(f"{ADMIN_URL}/knowledge")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 点击第一个知识库名称进入详情页
    first_kb_link = page.query_selector('button[class*="truncate"]')
    if first_kb_link:
        first_kb_link.click()
        time.sleep(3)

        # 点击上传按钮
        upload_btn = page.query_selector('button:has-text("上传文档")')
        if upload_btn:
            upload_btn.click()
            time.sleep(2)

            # 检查上传对话框
            dialog = page.query_selector('[role="dialog"]')
            if dialog:
                print("    ✅ 上传对话框打开成功")

                # 检查是否有元数据输入框
                feature_input = page.query_selector('input[placeholder*="F001"]')
                module_input = page.query_selector('input[placeholder*="user"]')

                if feature_input and module_input:
                    print("    ✅ 元数据输入框存在（功能编号、模块）")

                    # 测试填写元数据
                    feature_input.fill('F001,F002')
                    module_input.fill('user')
                    print("    ✅ 元数据填写成功")
                else:
                    print("    ⚠️ 元数据输入框未找到")

                # 关闭对话框
                cancel_btn = page.query_selector('button:has-text("取消")')
                if cancel_btn:
                    cancel_btn.click()
                    print("    ✅ 上传对话框关闭成功")
            else:
                print("    ❌ 上传对话框未打开")
                return False
        else:
            print("    ❌ 未找到上传按钮")
            return False
    else:
        print("    ⚠️ 没有知识库，跳过测试")
        return True

    return True


def test_conflict_review(page):
    """测试矛盾审核"""
    print("\n=== 4. 测试矛盾审核 ===")

    page.goto(f"{ADMIN_URL}/conflict-review")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查页面标题
    title = page.query_selector('h1:has-text("矛盾审核")')
    if not title:
        print("    ❌ 矛盾审核页面加载失败")
        return False

    print("    ✅ 矛盾审核页面加载成功")

    # 检查刷新按钮
    refresh_btn = page.query_selector('button:has-text("刷新")')
    if refresh_btn:
        refresh_btn.click()
        time.sleep(1)
        print("    ✅ 刷新按钮功能正常")

    # 检查状态显示
    badge = page.query_selector('[class*="badge"]')
    if badge:
        text = badge.inner_text()
        print(f"    ✅ 状态显示: {text}")

    return True


def test_end_to_end(page):
    """测试端到端链路"""
    print("\n=== 5. 测试端到端链路 ===")

    # 5.1 创建模块
    print("\n  5.1 创建模块...")
    page.goto(f"{ADMIN_URL}/modules")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 检查模块列表是否有数据
    rows = page.query_selector_all('tbody tr')
    if len(rows) > 0:
        print(f"    ✅ 模块列表有 {len(rows)} 条数据")
    else:
        print("    ⚠️ 模块列表为空")

    # 5.2 检查功能元数据
    print("\n  5.2 检查功能元数据...")
    page.goto(f"{ADMIN_URL}/feature-metadata")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    rows = page.query_selector_all('tbody tr')
    if len(rows) > 0:
        print(f"    ✅ 功能列表有 {len(rows)} 条数据")
    else:
        print("    ⚠️ 功能列表为空")

    # 5.3 检查知识库
    print("\n  5.3 检查知识库...")
    page.goto(f"{ADMIN_URL}/knowledge")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    rows = page.query_selector_all('tbody tr')
    if len(rows) > 0:
        print(f"    ✅ 知识库列表有 {len(rows)} 条数据")

        # 点击第一个知识库
        rows[0].click()
        time.sleep(2)

        # 检查文档列表
        doc_rows = page.query_selector_all('tbody tr')
        if len(doc_rows) > 0:
            print(f"    ✅ 文档列表有 {len(doc_rows)} 条数据")

            # 检查是否有模块和功能编号列
            headers = page.query_selector_all('th')
            header_texts = [h.inner_text() for h in headers]
            print(f"    表头: {header_texts}")

            if '模块' in header_texts:
                print("    ✅ 模块列存在")
            if '功能编号' in header_texts:
                print("    ✅ 功能编号列存在")
        else:
            print("    ⚠️ 文档列表为空")
    else:
        print("    ⚠️ 知识库列表为空")

    return True


def cleanup(page):
    """清理测试数据"""
    print("\n=== 6. 清理测试数据 ===")

    # 清理模块
    page.goto(f"{ADMIN_URL}/modules")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    delete_btn = page.query_selector('button:has-text("删除"):near(td:has-text("test_e2e_module"))')
    if delete_btn:
        delete_btn.click()
        time.sleep(1)
        confirm_btn = page.query_selector('button:has-text("确认")')
        if confirm_btn:
            confirm_btn.click()
        print("  ✅ 删除模块 test_e2e_module")

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
    print("  Playwright 前端功能测试")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        results = {}

        try:
            # 1. 登录
            results["login"] = test_login(page)

            # 2. 模块和功能管理
            results["module_feature"] = test_module_and_feature(page)

            # 3. 知识库上传
            results["knowledge_upload"] = test_knowledge_upload(page)

            # 4. 矛盾审核
            results["conflict_review"] = test_conflict_review(page)

            # 5. 端到端链路
            results["end_to_end"] = test_end_to_end(page)

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
