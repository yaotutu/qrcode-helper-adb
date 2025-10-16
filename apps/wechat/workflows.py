"""微信工作流定义"""
from actions import Actions
from .config import PACKAGE_NAME, TEXTS


def scan_from_album(actions: Actions, image_index: int = 0) -> dict:
    """
    从相册扫描二维码工作流

    Args:
        actions: 操作对象
        image_index: 选择相册中第几张图片（从 0 开始）

    Returns:
        执行结果字典
    """
    try:
        print("=" * 50)
        print("开始执行微信扫码工作流")
        print("=" * 50)

        # 1. 启动微信
        actions.launch_app(PACKAGE_NAME, wait_time=3)

        # 2. 点击"发现"标签
        if not actions.click_by_text(TEXTS["discover"], timeout=5):
            return {"success": False, "error": f"未找到'{TEXTS['discover']}'按钮"}

        actions.sleep(1)

        # 3. 点击"扫一扫"
        if not actions.click_by_text(TEXTS["scan"], timeout=5):
            return {"success": False, "error": f"未找到'{TEXTS['scan']}'按钮"}

        actions.sleep(2)

        # 4. 点击右上角相册图标或"相册"按钮
        # 注意：不同版本的微信界面可能不同，这里提供两种方式
        if not actions.click_by_text(TEXTS["album"], timeout=3):
            # 如果没有文字按钮，尝试点击右上角区域（需要根据实际屏幕调整坐标）
            width, height = actions.get_screen_size()
            actions.click_coordinate(int(width * 0.9), int(height * 0.1))

        actions.sleep(2)

        # 5. 选择相册中的图片
        # 这里使用坐标点击，实际使用时需要根据设备调整
        # 通常第一张图在左上角
        width, height = actions.get_screen_size()
        # 假设图片网格布局，第一张图大概在 (width/6, height/4) 位置
        x = int(width / 6)
        y = int(height / 4) + image_index * int(height / 6)
        actions.click_coordinate(x, y)

        actions.sleep(3)

        # 6. 等待扫码结果
        # 这里只是简单等待，实际项目中可能需要识别扫码结果
        print("等待扫码结果...")
        actions.sleep(2)

        print("=" * 50)
        print("微信扫码工作流执行完成")
        print("=" * 50)

        return {
            "success": True,
            "app": "wechat",
            "workflow": "scan_from_album",
            "message": "扫码流程已执行完成",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def send_message(actions: Actions, contact_name: str, message: str) -> dict:
    """
    发送消息工作流示例

    Args:
        actions: 操作对象
        contact_name: 联系人名称
        message: 消息内容

    Returns:
        执行结果字典
    """
    try:
        print("=" * 50)
        print(f"开始执行微信发送消息工作流: 发送给 {contact_name}")
        print("=" * 50)

        # 1. 启动微信
        actions.launch_app(PACKAGE_NAME, wait_time=3)

        # 2. 点击搜索框
        # 注意：这个 ID 可能因微信版本不同而变化，需要根据实际情况调整
        search_box_id = "com.tencent.mm:id/f8y"
        if not actions.click_by_id(search_box_id, timeout=5):
            return {"success": False, "error": "未找到搜索框"}

        actions.sleep(1)

        # 3. 输入联系人名称
        actions.input_text(contact_name)
        actions.sleep(1)

        # 4. 点击搜索结果
        if not actions.click_by_text(contact_name, timeout=5):
            return {"success": False, "error": f"未找到联系人: {contact_name}"}

        actions.sleep(1)

        # 5. 点击输入框并输入消息
        # 这里需要根据实际界面调整
        actions.click_coordinate(200, actions.get_screen_size()[1] - 100)
        actions.sleep(0.5)
        actions.input_text(message)

        # 6. 点击发送按钮
        if not actions.click_by_text(TEXTS["send"], timeout=3):
            return {"success": False, "error": "未找到发送按钮"}

        print("=" * 50)
        print("微信发送消息工作流执行完成")
        print("=" * 50)

        return {
            "success": True,
            "app": "wechat",
            "workflow": "send_message",
            "message": f"已发送消息给 {contact_name}",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# 导出所有工作流
WORKFLOWS = {
    "scan_from_album": scan_from_album,
    "send_message": send_message,
}
