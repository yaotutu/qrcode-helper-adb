# Apps 目录结构说明

每个 App 都是一个独立的文件夹，包含自己的配置和工作流。

## 目录结构

```
apps/
├── README.md           # 本说明文件
├── wechat/             # 微信自动化
│   ├── __init__.py     # 模块入口，导出 WORKFLOWS
│   ├── config.py       # 配置（包名、元素ID、文本等）
│   ├── workflows.py    # 工作流定义
│   └── utils.py        # （可选）辅助函数
├── alipay/             # 支付宝自动化
│   ├── __init__.py
│   ├── config.py
│   └── workflows.py
└── <其他app>/
    ├── __init__.py
    ├── config.py
    └── workflows.py
```

## 创建新应用

### 1. 创建应用目录

```bash
mkdir apps/myapp
```

### 2. 创建必需文件

#### `__init__.py`
```python
"""应用名称"""
from .workflows import WORKFLOWS

__all__ = ["WORKFLOWS"]
```

#### `config.py`
```python
"""应用配置"""

# 应用包名
PACKAGE_NAME = "com.example.app"

# 常用元素文本
TEXTS = {
    "button1": "按钮1",
    "button2": "按钮2",
}

# 资源 ID（可选）
RESOURCE_IDS = {
    "search": "com.example.app:id/search",
}
```

#### `workflows.py`
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
        print("开始执行工作流...")

        # 1. 启动应用
        actions.launch_app(PACKAGE_NAME)

        # 2. 执行操作
        actions.click_by_text(TEXTS["button1"])

        # 3. 返回结果
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

```
(automation) launch com.example.app
(automation) click_text 按钮1
(automation) screenshot test.png
```

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

## 最佳实践

1. **配置与逻辑分离**：把包名、文本、ID 等放在 `config.py`
2. **一个工作流一个函数**：保持每个工作流函数职责单一
3. **使用辅助函数**：如果有复杂的通用逻辑，放在 `utils.py`
4. **详细的文档字符串**：说明参数、返回值、注意事项
5. **使用 CLI 先测试**：把每一步都测试通过后再写代码
6. **截图辅助调试**：在关键步骤加入截图，方便排查问题

## 常见模式

### 模式 1：启动应用 + 点击按钮

```python
def simple_action(actions: Actions) -> dict:
    actions.launch_app(PACKAGE_NAME)
    actions.click_by_text("按钮")
    return {"success": True}
```

### 模式 2：搜索 + 输入 + 提交

```python
def search_action(actions: Actions, keyword: str) -> dict:
    actions.launch_app(PACKAGE_NAME)
    actions.click_by_id(RESOURCE_IDS["search"])
    actions.input_text(keyword)
    actions.click_by_text("搜索")
    return {"success": True}
```

### 模式 3：多步骤流程

```python
def complex_action(actions: Actions) -> dict:
    # 步骤 1
    actions.launch_app(PACKAGE_NAME)
    actions.sleep(2)

    # 步骤 2
    if not actions.click_by_text("选项1"):
        return {"success": False, "error": "未找到选项1"}

    # 步骤 3
    actions.swipe("up")
    actions.click_coordinate(500, 1000)

    return {"success": True}
```

## 获取应用包名

```bash
# Android 设备上查看当前运行的应用包名
adb shell dumpsys window | grep mCurrentFocus
```

## 获取元素信息

使用 weditor 查看界面元素：

```bash
python -m weditor
```

访问 http://localhost:17310 查看设备界面，点击元素获取：
- resource-id（资源ID）
- text（文本）
- 坐标位置
