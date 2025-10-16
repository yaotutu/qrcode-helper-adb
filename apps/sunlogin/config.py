"""向日葵配置"""

# 向日葵包名
PACKAGE_NAME = "com.oray.sunlogin"

# 常用元素文本
TEXTS = {
    "my_tab": "我的",  # 底部导航的"我的"标签
    "device_tab": "设备",  # 底部导航的"设备"标签
    "discover_tab": "发现",  # 底部导航的"发现"标签
}

# 资源 ID
RESOURCE_IDS = {
    # 扫码相关
    "scan_button": None,  # 扫码按钮的 ID（在"我的"页面左上角）- 需要从 uiautodev 获取
    "scan_view": "com.oray.sunlogin:id/scan_view",  # 扫码页面的视图
    # 相册相关
    "album_button": "com.oray.sunlogin:id/iv_scan_pic",  # 从相册选择图片的按钮
    "album_grid": "com.google.android.documentsui:id/dir_list",  # 相册的 GridView
}

# 扫码按钮坐标（备用方案：如果没有 resource-id，使用坐标点击）
# 不同分辨率的设备坐标可能不同，需要根据实际情况调整
SCAN_BUTTON_POSITION = {
    "ratio_x": 0.1,  # 屏幕宽度的 10% 位置
    "ratio_y": 0.08,  # 屏幕高度的 8% 位置
}
