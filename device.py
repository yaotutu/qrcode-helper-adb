"""设备管理模块"""
import uiautomator2 as u2
from typing import Optional


class DeviceManager:
    """Android 设备管理器"""

    def __init__(self, device_id: Optional[str] = None):
        """
        初始化设备管理器

        Args:
            device_id: 设备 ID，如果为 None 则自动连接第一个设备
        """
        self.device_id = device_id
        self.device: Optional[u2.Device] = None

    def connect(self) -> u2.Device:
        """连接设备"""
        try:
            if self.device_id:
                self.device = u2.connect(self.device_id)
            else:
                self.device = u2.connect()  # 连接第一个可用设备

            print(f"设备已连接: {self.device.info}")
            return self.device
        except Exception as e:
            raise Exception(f"连接设备失败: {e}")

    def disconnect(self):
        """断开设备连接"""
        if self.device:
            self.device = None
            print("设备已断开")

    def get_device(self) -> u2.Device:
        """获取设备对象"""
        if not self.device:
            return self.connect()
        return self.device

    def is_connected(self) -> bool:
        """检查设备是否已连接"""
        try:
            if self.device:
                self.device.info  # 尝试获取设备信息
                return True
        except:
            pass
        return False


# 全局设备管理器实例
_device_manager: Optional[DeviceManager] = None


def get_device_manager(device_id: Optional[str] = None) -> DeviceManager:
    """获取全局设备管理器实例"""
    global _device_manager
    if _device_manager is None:
        _device_manager = DeviceManager(device_id)
    return _device_manager
