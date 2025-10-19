"""向日葵工作流定义

完整的自动化流程：打开app → 切换到我的页面 → 点击扫码 → 选择相册 → 选择图片
"""
from actions import Actions
from . import steps


def execute(actions: Actions, image_index: int = 0) -> dict:
    """向日葵完整工作流：从相册扫描二维码

    步骤：
    1. 启动向日葵应用
    2. 切换到"我的"页面
    3. 点击扫码按钮
    4. 点击相册按钮
    5. 选择图片

    Args:
        image_index: 选择第几张图片（从 0 开始，默认第一张）

    Returns:
        执行结果字典
    """
    try:
        print("\n" + "=" * 60)
        print("🚀 向日葵工作流：从相册扫描二维码")
        print("=" * 60 + "\n")

        # 步骤 1: 启动应用
        if not steps.open_app(actions):
            return {"success": False, "error": "启动应用失败"}

        # 步骤 2: 切换到"我的"页面
        if not steps.ensure_on_my_page(actions):
            return {"success": False, "error": "切换到'我的'页面失败"}

        # 步骤 3: 点击扫码按钮
        if not steps.click_scan_button(actions):
            return {"success": False, "error": "点击扫码按钮失败"}

        # 等待扫码页面加载
        if not steps.wait_for_scan_page(actions, timeout=5):
            return {"success": False, "error": "扫码页面未能加载"}

        # 步骤 4: 点击相册按钮
        if not steps.click_album(actions):
            return {"success": False, "error": "点击相册按钮失败"}

        # 步骤 5: 选择图片
        if not steps.select_image(actions, image_index):
            return {"success": False, "error": f"选择第 {image_index} 张图片失败"}

        print("\n" + "=" * 60)
        print("✅ 工作流执行成功")
        print("=" * 60 + "\n")

        return {
            "success": True,
            "app": "sunlogin",
            "workflow": "execute",
            "message": f"已完成从相册扫码流程，选择了第 {image_index} 张图片",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# 导出工作流 - 使用 execute 作为主工作流
WORKFLOWS = {
    "execute": execute,
}
