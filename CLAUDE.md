# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于 UIAutomator2 的 Android 自动化工具,通过 HTTP API 或 CLI 远程控制手机执行特定操作(如扫描二维码、发送消息等)。采用插件化架构,每个应用(微信、支付宝等)独立管理。

## 开发环境设置

### 依赖管理
本项目使用 **uv** 作为包管理工具(而非 pip):

```bash
# 安装依赖
uv sync

# 运行 HTTP 服务
uv run main.py

# 运行交互式 CLI 工具
uv run cli.py
```

### Android 设备配置
在开发前需要确保:
1. Android 设备已开启 USB 调试
2. 设备通过 USB 或 WiFi ADB 连接
3. 已安装 UIAutomator2 服务: `python -m uiautomator2 init`
4. 可通过 `adb devices` 验证连接

## 核心架构

### 模块职责

- **main.py**: Flask HTTP 服务入口,提供 REST API
- **cli.py**: 交互式命令行工具,用于测试和调试工作流
- **device.py**: 设备管理模块,封装 UIAutomator2 设备连接
- **actions.py**: 通用操作封装(点击、滑动、输入等基础操作)
- **apps/**: 应用自动化模块,每个应用一个文件夹

### 工作流系统架构

工作流采用**三层结构**:

1. **Actions 层** (`actions.py`): 基础 UI 操作
   - 提供设备无关的通用操作(点击、滑动、输入等)
   - 所有应用共享

2. **Steps 层** (`apps/{app}/steps.py`, 可选): 可复用的应用步骤
   - 每个函数完成单一职责的原子操作
   - 包含页面状态判断函数(如 `is_on_my_page()`)
   - 适合需要灵活组合的复杂应用

3. **Workflows 层** (`apps/{app}/workflows.py`): 完整业务流程
   - 组合多个 steps 或直接使用 actions 完成完整任务
   - 导出到 `WORKFLOWS` 字典供 API/CLI 调用

**推荐模式** (参考 sunlogin):
- 使用 steps 层进行逻辑拆分
- 使用 `is_on_xxx_page()` 进行状态判断
- 使用 `ensure_on_xxx_page()` 进行幂等性保护
- workflow 仅负责编排 steps 并返回统一格式的结果

### 应用插件结构

每个应用位于 `apps/{app_name}/`,必需文件:

```
apps/{app_name}/
├── __init__.py      # 导出 WORKFLOWS
├── config.py        # 应用配置(包名、文本常量、坐标等)
├── workflows.py     # 工作流定义
└── steps.py         # (可选) 可复用的步骤函数
```

**config.py** 应包含:
- `PACKAGE_NAME`: Android 包名
- `TEXTS`: 界面文本常量字典
- `RESOURCE_IDS`: 资源 ID 常量字典
- 坐标配置(如需要)

**workflows.py** 格式:
```python
def workflow_name(actions: Actions, **params) -> dict:
    """工作流描述"""
    try:
        # 执行操作
        return {
            "success": True,
            "app": "app_name",
            "workflow": "workflow_name",
            "message": "描述信息"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

WORKFLOWS = {
    "workflow_name": workflow_name,
}
```

## 开发工作流

### 添加新应用的标准流程

1. **创建应用文件夹**
   ```bash
   mkdir apps/{app_name}
   ```

2. **使用 CLI 进行交互式测试**(推荐)
   ```bash
   uv run cli.py
   ```

   逐步测试每个操作:
   ```
   (qrcode-helper) launch com.example.app
   (qrcode-helper) screenshot s1.png
   (qrcode-helper) click_text 按钮名称
   (qrcode-helper) click_xy 500 1000
   ```

3. **使用 weditor 查看元素信息**
   ```bash
   python -m weditor
   ```
   访问 http://localhost:17310 获取 resource-id、text、坐标

4. **编写配置和工作流代码**
   - 先在 `config.py` 定义常量
   - 如果逻辑复杂,在 `steps.py` 拆分可复用步骤
   - 在 `workflows.py` 编排完整流程
   - 在 `__init__.py` 导出 WORKFLOWS

5. **测试工作流**
   ```bash
   # CLI 测试
   uv run cli.py
   (qrcode-helper) list
   (qrcode-helper) run {app_name} {workflow_name}

   # API 测试
   uv run main.py
   curl -X POST http://localhost:8000/execute \
     -H "Content-Type: application/json" \
     -d '{"app": "{app_name}", "workflow": "{workflow_name}", "params": {}}'
   ```

### 工作流调试技巧

- CLI 提供单步调试命令: `list`、`run`、`steps`、`step`
- 使用 `screenshot` 命令在关键步骤截图验证
- 使用 `exists_text` / `exists_id` 检查元素是否存在
- 优先使用 resource-id 定位元素(比文本更稳定)
- 坐标点击作为备用方案(不同设备可能不同)

## HTTP API 端点

- `GET /`: 服务信息
- `GET /health`: 健康检查
- `GET /apps`: 列出所有应用和工作流
- `POST /execute`: 执行工作流
  ```json
  {
    "app": "app_name",
    "workflow": "workflow_name",
    "params": {
      "param1": "value1"
    }
  }
  ```

服务默认运行在 `http://0.0.0.0:8000`

## 常见操作

### 查看包名
```bash
adb shell dumpsys window | grep mCurrentFocus
```

### 重启 ADB
```bash
adb kill-server && adb start-server
```

### WiFi 连接设备
```bash
adb tcpip 5555
adb connect <设备IP>:5555
```

## 代码规范

- 工作流函数必须返回标准格式字典(包含 `success` 字段)
- 配置与逻辑分离(常量放 config.py)
- 所有工作流添加详细的 docstring 说明参数和步骤
- 优先使用 resource-id > text > 坐标 的定位优先级
- Steps 函数返回布尔值表示成功/失败,便于错误处理
