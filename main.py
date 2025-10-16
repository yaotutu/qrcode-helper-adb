"""HTTP 服务入口"""
from flask import Flask, request, jsonify
from device import get_device_manager
from actions import Actions
import importlib
import os

app = Flask(__name__)


@app.route("/")
def index():
    """首页"""
    return jsonify(
        {
            "service": "qrcode-helper-adb",
            "status": "running",
            "endpoints": {
                "execute": "/execute - 执行自动化工作流",
                "health": "/health - 健康检查",
                "apps": "/apps - 查看支持的应用列表",
            },
        }
    )


@app.route("/health")
def health():
    """健康检查"""
    try:
        device_manager = get_device_manager()
        is_connected = device_manager.is_connected()
        return jsonify({"status": "ok", "device_connected": is_connected})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/apps")
def list_apps():
    """列出所有支持的应用和工作流"""
    apps_dir = "apps"
    supported_apps = {}

    # 遍历 apps 目录下的所有文件夹
    for item in os.listdir(apps_dir):
        item_path = os.path.join(apps_dir, item)

        # 跳过非目录、隐藏文件和 __pycache__
        if not os.path.isdir(item_path) or item.startswith(".") or item == "__pycache__":
            continue

        app_name = item
        try:
            # 导入 app 模块（每个 app 是一个文件夹）
            module = importlib.import_module(f"apps.{app_name}")
            workflows = getattr(module, "WORKFLOWS", {})
            supported_apps[app_name] = list(workflows.keys())
        except Exception as e:
            supported_apps[app_name] = {"error": str(e)}

    return jsonify({"apps": supported_apps})


@app.route("/execute", methods=["POST"])
def execute():
    """
    执行自动化工作流

    请求格式:
    {
        "app": "wechat",
        "workflow": "scan_from_album",
        "params": {
            "image_index": 0
        }
    }
    """
    try:
        data = request.get_json()

        # 参数验证
        if not data:
            return jsonify({"success": False, "error": "缺少请求数据"}), 400

        app_name = data.get("app")
        workflow_name = data.get("workflow")
        params = data.get("params", {})

        if not app_name:
            return jsonify({"success": False, "error": "缺少 app 参数"}), 400

        if not workflow_name:
            return jsonify({"success": False, "error": "缺少 workflow 参数"}), 400

        # 连接设备
        device_manager = get_device_manager()
        device = device_manager.get_device()

        # 创建 Actions 对象
        actions = Actions(device)

        # 动态导入 app 模块
        try:
            module = importlib.import_module(f"apps.{app_name}")
        except ModuleNotFoundError:
            return jsonify({"success": False, "error": f"不支持的应用: {app_name}"}), 404

        # 获取工作流
        workflows = getattr(module, "WORKFLOWS", {})
        if workflow_name not in workflows:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"应用 {app_name} 不支持工作流: {workflow_name}",
                        "available_workflows": list(workflows.keys()),
                    }
                ),
                404,
            )

        # 执行工作流
        workflow_func = workflows[workflow_name]
        result = workflow_func(actions, **params)

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def main():
    """启动 Flask 服务"""
    print("=" * 60)
    print("🚀 二维码助手服务启动中...")
    print("=" * 60)
    print("\n📱 请确保:")
    print("  1. Android 设备已通过 USB 连接或 WiFi ADB 连接")
    print("  2. 设备已开启 USB 调试")
    print("  3. 已安装 UIAutomator2 服务 (python -m uiautomator2 init)")
    print("\n🌐 API 文档:")
    print("  - GET  /          - 服务信息")
    print("  - GET  /health    - 健康检查")
    print("  - GET  /apps      - 查看支持的应用")
    print("  - POST /execute   - 执行工作流")
    print("\n🔗 服务地址: http://0.0.0.0:8000")
    print("\n" + "=" * 60)

    app.run(host="0.0.0.0", port=8000, debug=True)


if __name__ == "__main__":
    main()
