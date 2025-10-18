"""通用操作模块 - 提供基础的 UI 自动化操作"""
import time
from typing import Optional, Tuple
import uiautomator2 as u2


class Actions:
    """通用操作类，封装常用的 UI 自动化操作"""

    def __init__(self, device: u2.Device):
        """
        初始化操作类

        Args:
            device: UIAutomator2 设备对象
        """
        self.device = device

    def launch_app(self, package_name: str, wait_time: float = 2.0):
        """
        启动应用

        Args:
            package_name: 应用包名
            wait_time: 启动后等待时间（秒）
        """
        print(f"启动应用: {package_name}")
        self.device.app_start(package_name)
        time.sleep(wait_time)

    def stop_app(self, package_name: str):
        """
        停止应用

        Args:
            package_name: 应用包名
        """
        print(f"停止应用: {package_name}")
        self.device.app_stop(package_name)

    def click_by_text(self, text: str, timeout: float = 10.0) -> bool:
        """
        根据文本点击元素

        Args:
            text: 元素文本
            timeout: 超时时间（秒）

        Returns:
            是否点击成功
        """
        try:
            print(f"点击文本: {text}")
            element = self.device(text=text)
            if element.wait(timeout=timeout):
                element.click()
                time.sleep(0.5)
                return True
            return False
        except Exception as e:
            error_msg = str(e)
            if "INJECT_EVENTS" in error_msg or "SecurityException" in error_msg:
                print(f"❌ 点击失败: 权限不足")
                print(f"💡 请执行: uv run python -m uiautomator2 init")
            else:
                print(f"点击文本失败: {e}")
            return False

    def click_by_id(self, resource_id: str, timeout: float = 10.0) -> bool:
        """
        根据 resource-id 点击元素

        Args:
            resource_id: 资源 ID
            timeout: 超时时间（秒）

        Returns:
            是否点击成功
        """
        try:
            print(f"点击 ID: {resource_id}")
            element = self.device(resourceId=resource_id)
            if element.wait(timeout=timeout):
                element.click()
                time.sleep(0.5)
                return True
            return False
        except Exception as e:
            error_msg = str(e)
            if "INJECT_EVENTS" in error_msg or "SecurityException" in error_msg:
                print(f"❌ 点击失败: 权限不足")
                print(f"💡 请执行: uv run python -m uiautomator2 init")
            else:
                print(f"点击 ID 失败: {e}")
            return False

    def click_coordinate(self, x: int, y: int):
        """
        根据坐标点击

        Args:
            x: X 坐标
            y: Y 坐标
        """
        try:
            print(f"点击坐标: ({x}, {y})")
            self.device.click(x, y)
            time.sleep(0.5)
        except Exception as e:
            error_msg = str(e)
            if "INJECT_EVENTS" in error_msg or "SecurityException" in error_msg:
                print(f"❌ 点击失败: 权限不足")
                print(f"💡 请执行: uv run python -m uiautomator2 init")
                raise
            else:
                raise

    def swipe(self, direction: str = "up", scale: float = 0.8):
        """
        滑动屏幕

        Args:
            direction: 滑动方向 (up/down/left/right)
            scale: 滑动距离占屏幕的比例
        """
        print(f"滑动: {direction}")
        if direction == "up":
            self.device.swipe_ext("up", scale=scale)
        elif direction == "down":
            self.device.swipe_ext("down", scale=scale)
        elif direction == "left":
            self.device.swipe_ext("left", scale=scale)
        elif direction == "right":
            self.device.swipe_ext("right", scale=scale)
        time.sleep(0.5)

    def wait_for_element(
        self, text: Optional[str] = None, resource_id: Optional[str] = None, timeout: float = 10.0
    ) -> bool:
        """
        等待元素出现

        Args:
            text: 元素文本
            resource_id: 资源 ID
            timeout: 超时时间（秒）

        Returns:
            元素是否出现
        """
        try:
            if text:
                print(f"等待元素(文本): {text}")
                return self.device(text=text).wait(timeout=timeout)
            elif resource_id:
                print(f"等待元素(ID): {resource_id}")
                return self.device(resourceId=resource_id).wait(timeout=timeout)
            return False
        except Exception as e:
            print(f"等待元素失败: {e}")
            return False

    def input_text(self, text: str, clear: bool = True):
        """
        输入文字（需要先点击输入框）

        Args:
            text: 要输入的文本
            clear: 是否先清空输入框
        """
        print(f"输入文字: {text}")
        if clear:
            self.device.clear_text()
        self.device.send_keys(text)
        time.sleep(0.5)

    def press_back(self):
        """按返回键"""
        print("按返回键")
        self.device.press("back")
        time.sleep(0.5)

    def press_home(self):
        """按 Home 键"""
        print("按 Home 键")
        self.device.press("home")
        time.sleep(0.5)

    def take_screenshot(self, filename: Optional[str] = None) -> str:
        """
        截图

        Args:
            filename: 保存文件名，如果为 None 则使用时间戳

        Returns:
            截图文件路径
        """
        if not filename:
            filename = f"screenshot_{int(time.time())}.png"
        print(f"截图: {filename}")
        self.device.screenshot(filename)
        return filename

    def element_exists(self, text: Optional[str] = None, resource_id: Optional[str] = None) -> bool:
        """
        检查元素是否存在

        Args:
            text: 元素文本
            resource_id: 资源 ID

        Returns:
            元素是否存在
        """
        try:
            if text:
                return self.device(text=text).exists
            elif resource_id:
                return self.device(resourceId=resource_id).exists
            return False
        except:
            return False

    def get_screen_size(self) -> Tuple[int, int]:
        """
        获取屏幕尺寸

        Returns:
            (宽度, 高度)
        """
        info = self.device.info
        return info["displayWidth"], info["displayHeight"]

    def sleep(self, seconds: float):
        """
        等待指定时间

        Args:
            seconds: 等待秒数
        """
        print(f"等待 {seconds} 秒")
        time.sleep(seconds)
