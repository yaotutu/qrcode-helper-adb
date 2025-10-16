"""支付宝工作流定义"""
from actions import Actions
from .config import PACKAGE_NAME, TEXTS


def scan_from_album(actions: Actions, image_index: int = 0) -> dict:
    """
    从相册扫描二维码工作流（示例，需要根据实际界面调整）

    Args:
        actions: 操作对象
        image_index: 选择相册中第几张图片（从 0 开始）

    Returns:
        执行结果字典
    """
    try:
        print("=" * 50)
        print("开始执行支付宝扫码工作流")
        print("=" * 50)

        # 1. 启动支付宝
        actions.launch_app(PACKAGE_NAME, wait_time=3)

        # 2. 点击"扫一扫"
        # 注意：这里需要根据实际界面调整
        if not actions.click_by_text(TEXTS["scan"], timeout=5):
            return {"success": False, "error": f"未找到'{TEXTS['scan']}'按钮"}

        actions.sleep(2)

        # 3. 点击相册
        if not actions.click_by_text(TEXTS["album"], timeout=3):
            # 如果没有文字按钮，可能需要使用坐标点击
            width, height = actions.get_screen_size()
            actions.click_coordinate(int(width * 0.9), int(height * 0.1))

        actions.sleep(2)

        # 4. 选择图片
        width, height = actions.get_screen_size()
        x = int(width / 6)
        y = int(height / 4) + image_index * int(height / 6)
        actions.click_coordinate(x, y)

        actions.sleep(3)

        print("=" * 50)
        print("支付宝扫码工作流执行完成")
        print("=" * 50)

        return {
            "success": True,
            "app": "alipay",
            "workflow": "scan_from_album",
            "message": "扫码流程已执行完成",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# 导出所有工作流
WORKFLOWS = {
    "scan_from_album": scan_from_album,
}
