"""向日葵的可复用步骤（Steps）"""
from actions import Actions
from .config import PACKAGE_NAME, TEXTS, RESOURCE_IDS, SCAN_BUTTON_POSITION


# ==================== 页面判断 ====================

def is_on_my_page(actions: Actions) -> bool:
    """检查是否在"我的"页面

    通过查找"我的"页面特有的元素来判断
    根据截图，可以查找：用户名、福利、订单、兑换等元素
    """
    # 方法1：检查是否有"我的福利"、"我的订单"等文本
    if actions.element_exists(text="我的福利"):
        return True
    if actions.element_exists(text="我的订单"):
        return True
    if actions.element_exists(text="阳光小店"):
        return True

    # 方法2：检查是否有用户名显示
    # 如果有其他特征元素，可以继续添加

    return False


def is_on_device_page(actions: Actions) -> bool:
    """检查是否在"设备"页面

    通过查找"设备"页面特有的元素来判断
    根据截图，可以查找：开机设备、设备列表等元素
    """
    # 检查是否有"开机设备"文本
    if actions.element_exists(text="开机设备"):
        return True

    # 检查是否有"排序"按钮（设备页面右上角）
    if actions.element_exists(text="排序"):
        return True

    return False


def ensure_on_my_page(actions: Actions) -> bool:
    """确保当前在"我的"页面，如果不在则切换过去"""
    print("→ 检查并确保在'我的'页面")

    if is_on_my_page(actions):
        print("  ✓ 已在'我的'页面")
        return True

    print("  当前不在'我的'页面，切换中...")
    return goto_my_tab(actions)


def ensure_on_device_page(actions: Actions) -> bool:
    """确保当前在"设备"页面，如果不在则切换过去"""
    print("→ 检查并确保在'设备'页面")

    if is_on_device_page(actions):
        print("  ✓ 已在'设备'页面")
        return True

    print("  当前不在'设备'页面，切换中...")
    return goto_device_tab(actions)


def is_on_scan_page(actions: Actions) -> bool:
    """检查是否在扫码页面

    通过查找扫码页面特有的元素来判断
    使用 resource-id: com.oray.sunlogin:id/scan_view
    """
    # 通过 resource-id 判断（最可靠的方式）
    if actions.element_exists(resource_id="com.oray.sunlogin:id/scan_view"):
        return True

    return False


def wait_for_scan_page(actions: Actions, timeout: float = 5.0) -> bool:
    """等待扫码页面加载

    Args:
        timeout: 超时时间（秒）

    Returns:
        是否成功进入扫码页面
    """
    print(f"→ 等待扫码页面加载（最多 {timeout} 秒）")

    if actions.wait_for_element(resource_id="com.oray.sunlogin:id/scan_view", timeout=timeout):
        print("  ✓ 扫码页面已加载")
        return True
    else:
        print("  ✗ 扫码页面加载超时")
        return False


# ==================== 基础操作 ====================

def open_app(actions: Actions) -> bool:
    """步骤：启动向日葵应用"""
    print("→ 启动向日葵应用")
    actions.launch_app(PACKAGE_NAME, wait_time=3)
    return True


def goto_my_tab(actions: Actions) -> bool:
    """步骤：点击底部"我的"标签"""
    print("→ 点击底部'我的'标签")
    if not actions.click_by_text(TEXTS["my_tab"], timeout=5):
        print(f"  ✗ 未找到'{TEXTS['my_tab']}'标签")
        return False
    actions.sleep(1)
    return True


def goto_device_tab(actions: Actions) -> bool:
    """步骤：点击底部"设备"标签"""
    print("→ 点击底部'设备'标签")
    if not actions.click_by_text(TEXTS["device_tab"], timeout=5):
        print(f"  ✗ 未找到'{TEXTS['device_tab']}'标签")
        return False
    actions.sleep(1)
    return True


def click_scan_button(actions: Actions) -> bool:
    """步骤：点击左上角扫码按钮

    优先使用 resource-id 点击，如果没有配置则使用坐标点击
    """
    print("→ 点击左上角扫码按钮")

    # 方法1：优先使用 resource-id（更可靠）
    if RESOURCE_IDS["scan_button"]:
        print(f"  使用 resource-id: {RESOURCE_IDS['scan_button']}")
        if actions.click_by_id(RESOURCE_IDS["scan_button"], timeout=3):
            actions.sleep(2)
            return True
        else:
            print("  ✗ 通过 resource-id 点击失败，尝试坐标点击")

    # 方法2：备用方案 - 使用坐标点击
    print("  使用坐标点击")
    width, height = actions.get_screen_size()
    scan_x = int(width * SCAN_BUTTON_POSITION["ratio_x"])
    scan_y = int(height * SCAN_BUTTON_POSITION["ratio_y"])
    print(f"  坐标: ({scan_x}, {scan_y})")
    actions.click_coordinate(scan_x, scan_y)
    actions.sleep(2)
    return True


def click_album(actions: Actions) -> bool:
    """步骤：点击相册按钮（从本地相册选择图片）

    使用 resource-id: com.oray.sunlogin:id/iv_scan_pic
    """
    print("→ 点击相册按钮")

    # 使用 resource-id 点击（最可靠）
    if RESOURCE_IDS["album_button"]:
        print(f"  使用 resource-id: {RESOURCE_IDS['album_button']}")
        if actions.click_by_id(RESOURCE_IDS["album_button"], timeout=5):
            actions.sleep(1)
            return True
        else:
            print("  ✗ 通过 resource-id 点击失败")
            return False

    # 备用方案：尝试文字点击
    print("  尝试通过文字点击")
    if actions.click_by_text("相册", timeout=3):
        actions.sleep(1)
        return True

    print("  ✗ 未找到相册按钮")
    return False


def select_image(actions: Actions, image_index: int = 0) -> bool:
    """步骤：从相册选择图片

    通过定位 GridView 中的子元素来选择图片
    GridView 中每个 LinearLayout 代表一张图片

    Args:
        image_index: 图片索引（从 0 开始，0 是第一张图片）
    """
    print(f"→ 选择第 {image_index} 张图片")

    try:
        # 方法1：尝试通过 GridView 的子元素点击
        # 在 UIAutomator2 中，可以通过 child 方法访问子元素
        grid_view = actions.device(resourceId=RESOURCE_IDS["album_grid"])

        if grid_view.exists:
            print(f"  找到 GridView，尝试点击第 {image_index} 个子元素")
            # 点击 GridView 的第 image_index 个子元素
            # UIAutomator2 的语法：child(instance=index)
            child = actions.device(resourceId=RESOURCE_IDS["album_grid"]).child(
                className="android.widget.LinearLayout",
                instance=image_index
            )

            if child.exists:
                print(f"  找到第 {image_index} 张图片，点击中...")
                child.click()
                actions.sleep(2)
                return True
            else:
                print(f"  ✗ 第 {image_index} 张图片不存在，使用备用方案")

    except Exception as e:
        print(f"  通过 GridView 选择失败: {e}，使用坐标点击")

    # 方法2：备用方案 - 使用坐标点击
    print("  使用坐标点击（备用方案）")
    width, height = actions.get_screen_size()

    # 根据截图，相册图片看起来是网格布局
    # 计算图片位置（假设是 3 列布局）
    cols = 3  # 每行 3 张图片
    col = image_index % cols  # 列位置 (0, 1, 2)
    row = image_index // cols  # 行位置 (0, 1, 2...)

    # 第一张图片的大致位置
    start_x = int(width / 6)  # 第一列中心
    start_y = int(height / 4)  # 第一行中心

    # 图片间距
    spacing_x = int(width / 3)  # 列间距
    spacing_y = int(height / 6)  # 行间距

    x = start_x + col * spacing_x
    y = start_y + row * spacing_y

    print(f"  坐标: ({x}, {y}) [第{row}行第{col}列]")
    actions.click_coordinate(x, y)
    actions.sleep(2)
    return True
