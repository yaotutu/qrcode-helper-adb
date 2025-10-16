# 二维码助手 (QRCode Helper ADB)

基于 UIAutomator2 的 Android 自动化工具，用于远程控制手机执行特定操作，如扫描二维码、发送消息等。

## 功能特点

- 📱 支持通过 HTTP API 远程控制 Android 设备
- 🔌 插件化架构，每个 App 独立管理
- 🎯 灵活的工作流系统，轻松扩展新功能
- 🚀 简单易用，轻量级设计

## 项目结构

```
qrcode-helper-adb/
├── main.py           # HTTP 服务入口
├── cli.py            # 交互式命令行工具（用于测试）
├── device.py         # 设备管理模块
├── actions.py        # 通用操作封装
└── apps/             # 应用自动化模块（每个 app 一个文件夹）
    ├── README.md     # Apps 目录说明
    ├── wechat/       # 微信自动化
    │   ├── __init__.py
    │   ├── config.py
    │   └── workflows.py
    ├── alipay/       # 支付宝自动化
    │   ├── __init__.py
    │   ├── config.py
    │   └── workflows.py
    └── ...           # 其他应用
```

## 安装

### 1. 克隆项目

```bash
git clone <repo-url>
cd qrcode-helper-adb
```

### 2. 使用 uv 安装依赖

```bash
# 如果还没安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv sync
```

### 3. 配置 Android 设备

#### 3.1 开启 USB 调试

1. 在 Android 设备上进入「设置」->「关于手机」
2. 连续点击「版本号」7 次，开启开发者模式
3. 进入「设置」->「开发者选项」，开启「USB 调试」

#### 3.2 连接设备

**USB 连接：**
```bash
# 连接设备后检查
adb devices
```

**WiFi 连接：**
```bash
# 先通过 USB 连接，然后执行
adb tcpip 5555
adb connect <设备IP>:5555
```

#### 3.3 安装 UIAutomator2 服务

```bash
# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 在设备上安装 UIAutomator2 服务
python -m uiautomator2 init
```

## 使用方法

### 方式一：交互式命令行工具（推荐用于测试和调试）

```bash
uv run cli.py
```

这会启动一个交互式命令行，你可以一步步测试每个操作：

```
(automation) launch com.tencent.mm    # 启动微信
(automation) click_text 发现           # 点击"发现"
(automation) click_text 扫一扫          # 点击"扫一扫"
(automation) screenshot test.png      # 截图查看当前状态
(automation) help                     # 查看所有可用命令
```

**常用命令：**
- `info` - 查看设备信息
- `screenshot` - 截图
- `launch <包名>` - 启动应用
- `click_text <文本>` - 点击文本
- `click_xy <x> <y>` - 点击坐标
- `swipe <方向>` - 滑动（up/down/left/right）
- `input <文本>` - 输入文字
- `back` - 返回键
- `sleep <秒数>` - 等待
- `help` - 查看所有命令

**快捷命令：**
- `wechat` - 快速启动微信
- `alipay` - 快速启动支付宝

### 方式二：HTTP API 服务

```bash
uv run main.py
```

服务将在 `http://0.0.0.0:5000` 启动。

### API 接口

#### 1. 查看服务信息

```bash
curl http://localhost:5000/
```

#### 2. 健康检查

```bash
curl http://localhost:5000/health
```

#### 3. 查看支持的应用

```bash
curl http://localhost:5000/apps
```

#### 4. 执行工作流

```bash
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "app": "wechat",
    "workflow": "scan_from_album",
    "params": {
      "image_index": 0
    }
  }'
```

## 支持的应用和工作流

### 微信 (wechat)

#### scan_from_album - 从相册扫描二维码

```json
{
  "app": "wechat",
  "workflow": "scan_from_album",
  "params": {
    "image_index": 0
  }
}
```

#### send_message - 发送消息

```json
{
  "app": "wechat",
  "workflow": "send_message",
  "params": {
    "contact_name": "张三",
    "message": "你好"
  }
}
```

## 添加新应用

### 1. 创建应用文件夹

```bash
mkdir apps/myapp
```

### 2. 创建应用文件

每个应用需要三个文件：

#### `apps/myapp/__init__.py`
```python
"""应用名称"""
from .workflows import WORKFLOWS

__all__ = ["WORKFLOWS"]
```

#### `apps/myapp/config.py`
```python
"""应用配置"""

# 应用包名
PACKAGE_NAME = "com.example.myapp"

# 常用元素文本
TEXTS = {
    "scan": "扫一扫",
    "album": "相册",
}
```

#### `apps/myapp/workflows.py`
```python
"""工作流定义"""
from actions import Actions
from .config import PACKAGE_NAME, TEXTS


def my_workflow(actions: Actions, **params) -> dict:
    """
    工作流描述

    Args:
        actions: 操作对象
        **params: 其他参数

    Returns:
        执行结果字典
    """
    try:
        # 1. 启动应用
        actions.launch_app(PACKAGE_NAME)

        # 2. 执行操作
        actions.click_by_text(TEXTS["scan"])

        return {
            "success": True,
            "app": "myapp",
            "workflow": "my_workflow",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# 导出所有工作流
WORKFLOWS = {
    "my_workflow": my_workflow,
}
```

### 3. 使用 CLI 测试

```bash
uv run cli.py
```

逐步测试每个操作，确认工作流正确。

### 4. 调用 API

```bash
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "app": "myapp",
    "workflow": "my_workflow",
    "params": {}
  }'
```

更多详细说明请查看 [apps/README.md](apps/README.md)。

## 通用操作 API

在 `actions.py` 中提供了丰富的通用操作：

- `launch_app(package_name)` - 启动应用
- `click_by_text(text)` - 根据文本点击
- `click_by_id(resource_id)` - 根据资源 ID 点击
- `click_coordinate(x, y)` - 坐标点击
- `swipe(direction)` - 滑动屏幕
- `wait_for_element(...)` - 等待元素出现
- `input_text(text)` - 输入文字
- `press_back()` - 返回键
- `take_screenshot()` - 截图
- 更多...

## 常见问题

### 1. 设备连接失败

- 检查 USB 调试是否开启
- 检查 adb devices 是否能看到设备
- 尝试重新插拔 USB 或重启 adb 服务：`adb kill-server && adb start-server`

### 2. UIAutomator2 初始化失败

- 确保设备网络正常
- 手动安装 ATX：`python -m uiautomator2 init`
- 检查设备是否有足够存储空间

### 3. 工作流执行失败

- 不同设备、不同版本的应用 UI 可能不同
- 需要根据实际情况调整坐标和元素定位
- 使用 `weditor` 查看元素结构：`python -m weditor`

## 开发调试

### 使用交互式 CLI 测试工作流

这是推荐的工作流开发方式：

1. **启动 CLI 工具**
   ```bash
   uv run cli.py
   ```

2. **逐步测试每个操作**
   ```
   (automation) wechat              # 启动微信
   (automation) sleep 3             # 等待加载
   (automation) click_text 发现      # 点击"发现"标签
   (automation) screenshot step1.png # 截图确认
   (automation) click_text 扫一扫     # 点击"扫一扫"
   (automation) screenshot step2.png # 截图确认
   ```

3. **调整坐标或选择器**
   - 如果某个操作失败，可以用 `screenshot` 截图查看当前状态
   - 使用 `click_xy` 尝试不同的坐标
   - 使用 `exists_text` 检查元素是否存在

4. **记录成功的步骤**
   - 把测试成功的步骤写入 `apps/xxx.py` 的工作流函数中

### 查看设备界面结构

```bash
# 启动 weditor
python -m weditor
```

访问 `http://localhost:17310` 查看设备界面元素，获取精确的资源 ID 和坐标。

### 工作流开发示例

假设你要为支付宝添加扫码功能：

**第一步：使用 CLI 测试**
```
(automation) launch com.eg.android.AlipayGphone
(automation) screenshot s1.png
(automation) click_text 扫一扫
(automation) screenshot s2.png
(automation) click_text 相册
(automation) screenshot s3.png
```

**第二步：编写工作流代码**

根据测试成功的步骤，在 [apps/alipay.py](apps/alipay.py) 中编写：

```python
def scan_from_album(actions: Actions) -> dict:
    actions.launch_app("com.eg.android.AlipayGphone")
    actions.sleep(3)
    actions.click_by_text("扫一扫")
    actions.sleep(1)
    actions.click_by_text("相册")
    # ... 后续步骤
    return {"success": True}
```

### 查看日志

CLI 和服务运行时都会输出详细日志，帮助调试工作流执行过程。

## 技术栈

- **Python 3.8+**
- **uv** - 现代化的 Python 包管理工具
- **UIAutomator2** - Android 自动化框架
- **Flask** - 轻量级 Web 框架

## 许可证

MIT

## 注意事项

- 本工具仅用于学习和个人使用
- 请遵守相关应用的使用条款
- 自动化操作可能触发应用的安全机制，请谨慎使用
