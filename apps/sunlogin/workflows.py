"""向日葵工作流定义

工作流由多个可复用的 step 组成
"""
from actions import Actions
from . import steps


def open_scan(actions: Actions) -> dict:
    """打开扫码功能

    步骤：
    1. 启动向日葵应用
    2. 确保在"我的"页面
    3. 点击左上角的扫码按钮
    """
    try:
        print("\n" + "=" * 60)
        print("工作流: 打开向日葵扫码功能")
        print("=" * 60 + "\n")

        # 执行步骤
        if not steps.open_app(actions):
            return {"success": False, "error": "启动应用失败"}

        # 使用 ensure_on_my_page 替代直接 goto_my_tab
        # 这样会先检查是否已在目标页面，避免重复点击
        if not steps.ensure_on_my_page(actions):
            return {"success": False, "error": "切换到'我的'标签失败"}

        if not steps.click_scan_button(actions):
            return {"success": False, "error": "点击扫码按钮失败"}

        # 等待并验证是否成功进入扫码页面
        if not steps.wait_for_scan_page(actions, timeout=5):
            return {"success": False, "error": "未能进入扫码页面"}

        print("\n" + "=" * 60)
        print("✅ 工作流执行成功")
        print("=" * 60 + "\n")

        return {
            "success": True,
            "app": "sunlogin",
            "workflow": "open_scan",
            "message": "已打开扫码功能",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def scan_from_album(actions: Actions, image_index: int = 0) -> dict:
    """从相册扫描二维码

    步骤：
    1. 启动向日葵应用
    2. 确保在"我的"页面
    3. 点击左上角的扫码按钮
    4. 点击相册按钮
    5. 选择图片
    """
    try:
        print("\n" + "=" * 60)
        print("工作流: 向日葵从相册扫码")
        print("=" * 60 + "\n")

        # 执行步骤
        if not steps.open_app(actions):
            return {"success": False, "error": "启动应用失败"}

        if not steps.ensure_on_my_page(actions):
            return {"success": False, "error": "切换到'我的'标签失败"}

        if not steps.click_scan_button(actions):
            return {"success": False, "error": "点击扫码按钮失败"}

        # 等待并验证是否成功进入扫码页面
        if not steps.wait_for_scan_page(actions, timeout=5):
            return {"success": False, "error": "未能进入扫码页面"}

        if not steps.click_album(actions):
            return {"success": False, "error": "点击相册按钮失败"}

        if not steps.select_image(actions, image_index):
            return {"success": False, "error": "选择图片失败"}

        print("\n" + "=" * 60)
        print("✅ 工作流执行成功")
        print("=" * 60 + "\n")

        return {
            "success": True,
            "app": "sunlogin",
            "workflow": "scan_from_album",
            "message": "从相册扫码流程已执行完成",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# 导出所有工作流
WORKFLOWS = {
    "open_scan": open_scan,
    "scan_from_album": scan_from_album,
}
