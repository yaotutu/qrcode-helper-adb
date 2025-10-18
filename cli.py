#!/usr/bin/env python3
"""交互式命令行工具 - 用于测试和调试自动化操作"""
import cmd
import sys
import os
import importlib
from device import get_device_manager
from actions import Actions


class AutomationCLI(cmd.Cmd):
    """交互式自动化测试命令行"""

    intro = """
╔══════════════════════════════════════════════════════════════╗
║          二维码助手 - 命令行模式                              ║
╚══════════════════════════════════════════════════════════════╝

💡 可用命令:
  menu                           进入交互式菜单
  list                           列出所有可用的工作流
  steps                          列出所有可用的步骤
  run <app> <workflow> [参数]    直接执行工作流
  step <app> <step> [参数]       直接执行步骤

🔧 调试命令:
  launch <包名>                  启动应用
  click_text <文本>              点击文本
  screenshot <文件名>            截图
  info                          查看设备信息
  help                          查看所有命令
  quit/exit                      退出程序
"""
    prompt = "(qrcode-helper) "

    def __init__(self):
        super().__init__()
        self.device = None
        self.actions = None
        self.available_apps = {}  # 存储所有可用的 app 和工作流
        self.available_steps = {}  # 存储所有可用的 app 和 steps

    def preloop(self):
        """在命令循环开始前连接设备"""
        try:
            print("正在连接设备...")
            device_manager = get_device_manager()
            self.device = device_manager.connect()
            self.actions = Actions(self.device)
            print(f"✓ 设备已连接\n")

            # 加载所有可用的工作流和步骤
            self._load_workflows()
            self._load_steps()
        except Exception as e:
            print(f"✗ 连接设备失败: {e}")
            print("请确保设备已连接并开启 USB 调试\n")
            sys.exit(1)

    def _load_workflows(self):
        """加载所有 app 的工作流"""
        apps_dir = "apps"
        self.available_apps = {}

        for item in os.listdir(apps_dir):
            item_path = os.path.join(apps_dir, item)

            # 跳过非目录、隐藏文件和 __pycache__
            if not os.path.isdir(item_path) or item.startswith(".") or item == "__pycache__":
                continue

            app_name = item
            try:
                # 导入 app 模块
                module = importlib.import_module(f"apps.{app_name}")
                workflows = getattr(module, "WORKFLOWS", {})
                if workflows:
                    self.available_apps[app_name] = workflows
            except Exception as e:
                print(f"⚠️  加载 {app_name} 失败: {e}")

    def _load_steps(self):
        """加载所有 app 的步骤"""
        apps_dir = "apps"
        self.available_steps = {}

        for item in os.listdir(apps_dir):
            item_path = os.path.join(apps_dir, item)

            # 跳过非目录、隐藏文件和 __pycache__
            if not os.path.isdir(item_path) or item.startswith(".") or item == "__pycache__":
                continue

            app_name = item
            try:
                # 尝试导入 steps 模块
                steps_module = importlib.import_module(f"apps.{app_name}.steps")
                # 获取所有函数（不包括私有函数和导入的模块）
                steps = {}
                for name in dir(steps_module):
                    if not name.startswith("_"):
                        obj = getattr(steps_module, name)
                        if callable(obj) and hasattr(obj, "__module__"):
                            if obj.__module__ == f"apps.{app_name}.steps":
                                steps[name] = obj
                if steps:
                    self.available_steps[app_name] = steps
            except (ImportError, AttributeError):
                # 如果没有 steps 模块，跳过
                pass
            except Exception as e:
                print(f"⚠️  加载 {app_name} 的 steps 失败: {e}")

    # ==================== 工作流管理 ====================

    def do_list(self, arg):
        """列出所有可用的应用和工作流"""
        if not self.available_apps:
            print("✗ 没有找到可用的工作流\n")
            return

        print("\n可用的应用和工作流:\n")
        print("=" * 60)
        for app_name, workflows in self.available_apps.items():
            print(f"\n📱 {app_name}")
            for workflow_name, workflow_func in workflows.items():
                # 获取工作流的文档字符串
                doc = workflow_func.__doc__
                if doc:
                    desc = doc.strip().split("\n")[0]  # 取第一行作为描述
                else:
                    desc = "无描述"
                print(f"   └─ {workflow_name}: {desc}")
        print("\n" + "=" * 60)
        print("\n使用方法: run <app> <workflow> [参数]")
        print("示例: run sunlogin open_scan")
        print("示例: run wechat scan_from_album image_index=0\n")

    def do_run(self, arg):
        """执行指定的工作流
        用法: run <app> <workflow> [参数]
        示例: run sunlogin open_scan
        示例: run wechat scan_from_album image_index=0
        """
        parts = arg.split()
        if len(parts) < 2:
            print("✗ 用法: run <app> <workflow> [参数]\n")
            print("示例: run sunlogin open_scan")
            print("示例: run wechat scan_from_album image_index=0\n")
            return

        app_name = parts[0]
        workflow_name = parts[1]

        # 解析参数
        params = {}
        for param in parts[2:]:
            if "=" in param:
                key, value = param.split("=", 1)
                # 尝试转换为数字
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass  # 保持字符串
                params[key] = value

        # 检查 app 是否存在
        if app_name not in self.available_apps:
            print(f"✗ 应用 '{app_name}' 不存在\n")
            print("使用 'list' 命令查看所有可用应用\n")
            return

        # 检查 workflow 是否存在
        workflows = self.available_apps[app_name]
        if workflow_name not in workflows:
            print(f"✗ 工作流 '{workflow_name}' 不存在\n")
            print(f"应用 {app_name} 可用的工作流:")
            for name in workflows.keys():
                print(f"  - {name}")
            print()
            return

        # 执行工作流
        try:
            print(f"\n▶️  执行工作流: {app_name}.{workflow_name}")
            if params:
                print(f"   参数: {params}")
            print()

            workflow_func = workflows[workflow_name]
            result = workflow_func(self.actions, **params)

            # 显示结果
            print("\n" + "=" * 60)
            if result.get("success"):
                print(f"✅ 成功: {result.get('message', '工作流执行完成')}")
            else:
                print(f"❌ 失败: {result.get('error', '未知错误')}")
            print("=" * 60 + "\n")

        except Exception as e:
            print(f"\n❌ 执行失败: {e}\n")
            import traceback
            traceback.print_exc()

    # ==================== 步骤管理 ====================

    def do_steps(self, arg):
        """列出所有可用的应用和步骤"""
        if not self.available_steps:
            print("✗ 没有找到可用的步骤\n")
            return

        print("\n可用的应用和步骤:\n")
        print("=" * 60)
        for app_name, steps in self.available_steps.items():
            print(f"\n📱 {app_name}")
            for step_name, step_func in steps.items():
                # 获取步骤的文档字符串
                doc = step_func.__doc__
                if doc:
                    desc = doc.strip().split("\n")[0]  # 取第一行作为描述
                else:
                    desc = "无描述"
                print(f"   └─ {step_name}: {desc}")
        print("\n" + "=" * 60)
        print("\n使用方法: step <app> <step_name> [参数]")
        print("示例: step sunlogin open_app")
        print("示例: step sunlogin select_image image_index=0\n")

    def do_step(self, arg):
        """执行指定的步骤
        用法: step <app> <step_name> [参数]
        示例: step sunlogin open_app
        示例: step sunlogin select_image image_index=0
        """
        parts = arg.split()
        if len(parts) < 2:
            print("✗ 用法: step <app> <step_name> [参数]\n")
            print("示例: step sunlogin open_app")
            print("示例: step sunlogin goto_my_tab\n")
            return

        app_name = parts[0]
        step_name = parts[1]

        # 解析参数
        params = {}
        for param in parts[2:]:
            if "=" in param:
                key, value = param.split("=", 1)
                # 尝试转换为数字
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass  # 保持字符串
                params[key] = value

        # 检查 app 是否存在
        if app_name not in self.available_steps:
            print(f"✗ 应用 '{app_name}' 没有可用的步骤\n")
            print("使用 'steps' 命令查看所有可用步骤\n")
            return

        # 检查 step 是否存在
        steps = self.available_steps[app_name]
        if step_name not in steps:
            print(f"✗ 步骤 '{step_name}' 不存在\n")
            print(f"应用 {app_name} 可用的步骤:")
            for name in steps.keys():
                print(f"  - {name}")
            print()
            return

        # 执行步骤
        try:
            print(f"\n▶️  执行步骤: {app_name}.{step_name}")
            if params:
                print(f"   参数: {params}")
            print()

            step_func = steps[step_name]
            result = step_func(self.actions, **params)

            # 显示结果
            print("\n" + "=" * 60)

            # 显示返回值
            if isinstance(result, bool):
                # 布尔类型：显示 True/False
                if result:
                    print(f"✅ 返回值: True")
                else:
                    print(f"❌ 返回值: False")
            elif result is None:
                print(f"ℹ️  返回值: None")
            else:
                # 其他类型：直接显示
                print(f"📊 返回值: {result}")

            print("=" * 60 + "\n")

        except TypeError as e:
            if "missing" in str(e) and "required positional argument" in str(e):
                print(f"\n❌ 参数错误: {e}")
                print(f"💡 提示: 这个步骤可能需要额外参数\n")
            else:
                print(f"\n❌ 执行失败: {e}\n")
                import traceback
                traceback.print_exc()
        except Exception as e:
            print(f"\n❌ 执行失败: {e}\n")
            import traceback
            traceback.print_exc()

    # ==================== 设备信息 ====================

    def do_info(self, arg):
        """显示设备信息"""
        try:
            info = self.device.info
            print("\n设备信息:")
            print(f"  品牌: {info.get('brand', 'Unknown')}")
            print(f"  型号: {info.get('model', 'Unknown')}")
            print(f"  系统版本: Android {info.get('version', 'Unknown')}")
            print(f"  屏幕分辨率: {info.get('displayWidth')}x{info.get('displayHeight')}")
            print()
        except Exception as e:
            print(f"✗ 获取设备信息失败: {e}\n")

    def do_screenshot(self, arg):
        """截图
        用法: screenshot [文件名]
        示例: screenshot test.png
        """
        try:
            filename = arg.strip() if arg.strip() else None
            filepath = self.actions.take_screenshot(filename)
            print(f"✓ 截图已保存: {filepath}\n")
        except Exception as e:
            print(f"✗ 截图失败: {e}\n")

    # ==================== 应用操作 ====================

    def do_launch(self, arg):
        """启动应用
        用法: launch <包名>
        示例: launch com.tencent.mm  # 启动微信

        常用应用包名:
          - 微信: com.tencent.mm
          - 支付宝: com.eg.android.AlipayGphone
          - 淘宝: com.taobao.taobao
          - 抖音: com.ss.android.ugc.aweme
        """
        if not arg:
            print("✗ 请提供应用包名\n")
            return

        try:
            self.actions.launch_app(arg.strip())
            print(f"✓ 已启动应用: {arg}\n")
        except Exception as e:
            print(f"✗ 启动应用失败: {e}\n")

    def do_stop(self, arg):
        """停止应用
        用法: stop <包名>
        示例: stop com.tencent.mm
        """
        if not arg:
            print("✗ 请提供应用包名\n")
            return

        try:
            self.actions.stop_app(arg.strip())
            print(f"✓ 已停止应用: {arg}\n")
        except Exception as e:
            print(f"✗ 停止应用失败: {e}\n")

    # ==================== 点击操作 ====================

    def do_click_text(self, arg):
        """根据文本点击
        用法: click_text <文本> [超时秒数]
        示例: click_text 发现 10
        """
        parts = arg.split()
        if not parts:
            print("✗ 请提供文本\n")
            return

        text = parts[0]
        timeout = float(parts[1]) if len(parts) > 1 else 10.0

        try:
            if self.actions.click_by_text(text, timeout):
                print(f"✓ 已点击文本: {text}\n")
            else:
                print(f"✗ 未找到文本: {text}\n")
        except Exception as e:
            print(f"✗ 点击失败: {e}\n")

    def do_click_id(self, arg):
        """根据资源 ID 点击
        用法: click_id <resource_id> [超时秒数]
        示例: click_id com.tencent.mm:id/button 10
        """
        parts = arg.split()
        if not parts:
            print("✗ 请提供资源 ID\n")
            return

        resource_id = parts[0]
        timeout = float(parts[1]) if len(parts) > 1 else 10.0

        try:
            if self.actions.click_by_id(resource_id, timeout):
                print(f"✓ 已点击 ID: {resource_id}\n")
            else:
                print(f"✗ 未找到 ID: {resource_id}\n")
        except Exception as e:
            print(f"✗ 点击失败: {e}\n")

    def do_click_xy(self, arg):
        """根据坐标点击
        用法: click_xy <x> <y>
        示例: click_xy 500 1000
        """
        parts = arg.split()
        if len(parts) < 2:
            print("✗ 请提供 X 和 Y 坐标\n")
            return

        try:
            x = int(parts[0])
            y = int(parts[1])
            self.actions.click_coordinate(x, y)
            print(f"✓ 已点击坐标: ({x}, {y})\n")
        except ValueError:
            print("✗ 坐标必须是整数\n")
        except Exception as e:
            print(f"✗ 点击失败: {e}\n")

    # ==================== 滑动操作 ====================

    def do_swipe(self, arg):
        """滑动屏幕
        用法: swipe <方向> [比例]
        示例: swipe up 0.8
        方向: up, down, left, right
        """
        parts = arg.split()
        if not parts:
            print("✗ 请提供滑动方向 (up/down/left/right)\n")
            return

        direction = parts[0]
        scale = float(parts[1]) if len(parts) > 1 else 0.8

        try:
            self.actions.swipe(direction, scale)
            print(f"✓ 已滑动: {direction}\n")
        except Exception as e:
            print(f"✗ 滑动失败: {e}\n")

    # ==================== 输入操作 ====================

    def do_input(self, arg):
        """输入文字（需要先点击输入框）
        用法: input <文本>
        示例: input 你好世界
        """
        if not arg:
            print("✗ 请提供要输入的文本\n")
            return

        try:
            self.actions.input_text(arg)
            print(f"✓ 已输入: {arg}\n")
        except Exception as e:
            print(f"✗ 输入失败: {e}\n")

    # ==================== 按键操作 ====================

    def do_back(self, arg):
        """按返回键"""
        try:
            self.actions.press_back()
            print("✓ 已按返回键\n")
        except Exception as e:
            print(f"✗ 操作失败: {e}\n")

    def do_home(self, arg):
        """按 Home 键"""
        try:
            self.actions.press_home()
            print("✓ 已按 Home 键\n")
        except Exception as e:
            print(f"✗ 操作失败: {e}\n")

    # ==================== 等待操作 ====================

    def do_wait_text(self, arg):
        """等待文本出现
        用法: wait_text <文本> [超时秒数]
        示例: wait_text 发现 10
        """
        parts = arg.split()
        if not parts:
            print("✗ 请提供文本\n")
            return

        text = parts[0]
        timeout = float(parts[1]) if len(parts) > 1 else 10.0

        try:
            if self.actions.wait_for_element(text=text, timeout=timeout):
                print(f"✓ 元素已出现: {text}\n")
            else:
                print(f"✗ 等待超时: {text}\n")
        except Exception as e:
            print(f"✗ 等待失败: {e}\n")

    def do_wait_id(self, arg):
        """等待资源 ID 出现
        用法: wait_id <resource_id> [超时秒数]
        示例: wait_id com.tencent.mm:id/button 10
        """
        parts = arg.split()
        if not parts:
            print("✗ 请提供资源 ID\n")
            return

        resource_id = parts[0]
        timeout = float(parts[1]) if len(parts) > 1 else 10.0

        try:
            if self.actions.wait_for_element(resource_id=resource_id, timeout=timeout):
                print(f"✓ 元素已出现: {resource_id}\n")
            else:
                print(f"✗ 等待超时: {resource_id}\n")
        except Exception as e:
            print(f"✗ 等待失败: {e}\n")

    def do_sleep(self, arg):
        """等待指定秒数
        用法: sleep <秒数>
        示例: sleep 2
        """
        if not arg:
            print("✗ 请提供等待秒数\n")
            return

        try:
            seconds = float(arg)
            self.actions.sleep(seconds)
            print(f"✓ 已等待 {seconds} 秒\n")
        except ValueError:
            print("✗ 秒数必须是数字\n")
        except Exception as e:
            print(f"✗ 等待失败: {e}\n")

    # ==================== 元素检查 ====================

    def do_exists_text(self, arg):
        """检查文本是否存在
        用法: exists_text <文本>
        示例: exists_text 发现
        """
        if not arg:
            print("✗ 请提供文本\n")
            return

        try:
            exists = self.actions.element_exists(text=arg)
            if exists:
                print(f"✓ 元素存在: {arg}\n")
            else:
                print(f"✗ 元素不存在: {arg}\n")
        except Exception as e:
            print(f"✗ 检查失败: {e}\n")

    def do_exists_id(self, arg):
        """检查资源 ID 是否存在
        用法: exists_id <resource_id>
        示例: exists_id com.tencent.mm:id/button
        """
        if not arg:
            print("✗ 请提供资源 ID\n")
            return

        try:
            exists = self.actions.element_exists(resource_id=arg)
            if exists:
                print(f"✓ 元素存在: {arg}\n")
            else:
                print(f"✗ 元素不存在: {arg}\n")
        except Exception as e:
            print(f"✗ 检查失败: {e}\n")

    # ==================== 交互式菜单 ====================

    def do_menu(self, arg):
        """进入交互式菜单模式"""
        print("\n" + "=" * 60)
        print("🌟 欢迎使用交互式菜单模式")
        print("=" * 60)
        print("💡 提示: 随时输入 0 可返回上一级，按 Ctrl+C 退出菜单")
        print()

        while True:
            # 1. 选择应用
            app_name = self._menu_select_app()
            if app_name is None:
                print("\n👋 已退出菜单模式")
                print("💡 输入 'menu' 可重新进入菜单，输入 'quit' 退出程序\n")
                break  # 用户选择退出

            # 2. 选择操作类型（工作流 or 步骤）
            action_type = self._menu_select_action_type(app_name)
            if action_type is None:
                continue  # 返回应用选择

            # 3. 根据类型选择具体的工作流或步骤
            if action_type == "workflow":
                self._menu_execute_workflow(app_name)
            elif action_type == "step":
                self._menu_execute_step(app_name)

    def _menu_select_app(self):
        """菜单：选择应用"""
        print("\n" + "=" * 60)
        print("📱 选择应用")
        print("=" * 60)

        # 合并所有应用（工作流 + 步骤）
        all_apps = set()
        all_apps.update(self.available_apps.keys())
        all_apps.update(self.available_steps.keys())
        app_list = sorted(list(all_apps))

        if not app_list:
            print("❌ 没有找到任何应用")
            input("\n按回车键继续...")
            return None

        # 显示应用列表
        for i, app_name in enumerate(app_list, 1):
            workflow_count = len(self.available_apps.get(app_name, {}))
            step_count = len(self.available_steps.get(app_name, {}))
            info = []
            if workflow_count > 0:
                info.append(f"{workflow_count} 个工作流")
            if step_count > 0:
                info.append(f"{step_count} 个步骤")
            info_str = ", ".join(info) if info else "无功能"
            print(f"  {i}. {app_name} ({info_str})")

        print(f"  0. 返回/退出")
        print()

        # 获取用户输入
        try:
            choice = input("请选择应用 (输入序号): ").strip()
            if not choice or choice == "0":
                return None

            index = int(choice) - 1
            if 0 <= index < len(app_list):
                return app_list[index]
            else:
                print("❌ 无效的序号")
                input("\n按回车键继续...")
                return self._menu_select_app()
        except ValueError:
            print("❌ 请输入数字")
            input("\n按回车键继续...")
            return self._menu_select_app()
        except KeyboardInterrupt:
            return None

    def _menu_select_action_type(self, app_name):
        """菜单：选择操作类型（工作流或步骤）"""
        print("\n" + "=" * 60)
        print(f"📱 {app_name} - 选择操作类型")
        print("=" * 60)

        options = []
        if app_name in self.available_apps:
            options.append("workflow")
            print(f"  1. 执行工作流 ({len(self.available_apps[app_name])} 个)")
        if app_name in self.available_steps:
            options.append("step")
            step_num = len(options)
            print(f"  {step_num}. 执行步骤 ({len(self.available_steps[app_name])} 个)")

        print(f"  0. 返回")
        print()

        if not options:
            print("❌ 该应用没有可用的操作")
            input("\n按回车键继续...")
            return None

        try:
            choice = input("请选择操作类型 (输入序号): ").strip()
            if not choice or choice == "0":
                return None

            index = int(choice) - 1
            if 0 <= index < len(options):
                return options[index]
            else:
                print("❌ 无效的序号")
                input("\n按回车键继续...")
                return self._menu_select_action_type(app_name)
        except ValueError:
            print("❌ 请输入数字")
            input("\n按回车键继续...")
            return self._menu_select_action_type(app_name)
        except KeyboardInterrupt:
            return None

    def _menu_execute_workflow(self, app_name):
        """菜单：执行工作流"""
        workflows = self.available_apps.get(app_name, {})
        if not workflows:
            print("❌ 该应用没有工作流")
            input("\n按回车键继续...")
            return

        while True:
            print("\n" + "=" * 60)
            print(f"🔧 {app_name} - 选择工作流")
            print("=" * 60)

            workflow_list = list(workflows.items())
            for i, (workflow_name, workflow_func) in enumerate(workflow_list, 1):
                doc = workflow_func.__doc__
                if doc:
                    desc = doc.strip().split("\n")[0]
                else:
                    desc = "无描述"
                print(f"  {i}. {workflow_name}")
                print(f"     {desc}")

            print(f"  0. 返回")
            print()

            try:
                choice = input("请选择工作流 (输入序号): ").strip()
                if not choice or choice == "0":
                    return

                index = int(choice) - 1
                if 0 <= index < len(workflow_list):
                    workflow_name, workflow_func = workflow_list[index]

                    # 询问是否需要参数
                    print(f"\n💡 提示: 如需传递参数，格式为 key=value，多个参数用空格分隔")
                    params_input = input("请输入参数 (直接回车跳过): ").strip()

                    # 解析参数
                    params = {}
                    if params_input:
                        for param in params_input.split():
                            if "=" in param:
                                key, value = param.split("=", 1)
                                try:
                                    value = int(value)
                                except ValueError:
                                    try:
                                        value = float(value)
                                    except ValueError:
                                        pass
                                params[key] = value

                    # 执行工作流
                    print(f"\n▶️  执行工作流: {app_name}.{workflow_name}")
                    if params:
                        print(f"   参数: {params}")
                    print()

                    try:
                        result = workflow_func(self.actions, **params)

                        print("\n" + "=" * 60)
                        if result.get("success"):
                            print(f"✅ 成功: {result.get('message', '工作流执行完成')}")
                        else:
                            print(f"❌ 失败: {result.get('error', '未知错误')}")
                        print("=" * 60)
                    except Exception as e:
                        print(f"\n❌ 执行失败: {e}")
                        import traceback
                        traceback.print_exc()

                    input("\n按回车键继续...")
                else:
                    print("❌ 无效的序号")
                    input("\n按回车键继续...")
            except ValueError:
                print("❌ 请输入数字")
                input("\n按回车键继续...")
            except KeyboardInterrupt:
                return

    def _menu_execute_step(self, app_name):
        """菜单：执行步骤"""
        steps = self.available_steps.get(app_name, {})
        if not steps:
            print("❌ 该应用没有步骤")
            input("\n按回车键继续...")
            return

        while True:
            print("\n" + "=" * 60)
            print(f"🔧 {app_name} - 选择步骤")
            print("=" * 60)

            step_list = list(steps.items())
            for i, (step_name, step_func) in enumerate(step_list, 1):
                doc = step_func.__doc__
                if doc:
                    desc = doc.strip().split("\n")[0]
                else:
                    desc = "无描述"
                print(f"  {i}. {step_name}")
                print(f"     {desc}")

            print(f"  0. 返回")
            print()

            try:
                choice = input("请选择步骤 (输入序号): ").strip()
                if not choice or choice == "0":
                    return

                index = int(choice) - 1
                if 0 <= index < len(step_list):
                    step_name, step_func = step_list[index]

                    # 询问是否需要参数
                    print(f"\n💡 提示: 如需传递参数，格式为 key=value，多个参数用空格分隔")
                    params_input = input("请输入参数 (直接回车跳过): ").strip()

                    # 解析参数
                    params = {}
                    if params_input:
                        for param in params_input.split():
                            if "=" in param:
                                key, value = param.split("=", 1)
                                try:
                                    value = int(value)
                                except ValueError:
                                    try:
                                        value = float(value)
                                    except ValueError:
                                        pass
                                params[key] = value

                    # 执行步骤
                    print(f"\n▶️  执行步骤: {app_name}.{step_name}")
                    if params:
                        print(f"   参数: {params}")
                    print()

                    try:
                        result = step_func(self.actions, **params)

                        print("\n" + "=" * 60)
                        if isinstance(result, bool):
                            if result:
                                print(f"✅ 返回值: True")
                            else:
                                print(f"❌ 返回值: False")
                        elif result is None:
                            print(f"ℹ️  返回值: None")
                        else:
                            print(f"📊 返回值: {result}")
                        print("=" * 60)
                    except TypeError as e:
                        if "missing" in str(e) and "required positional argument" in str(e):
                            print(f"\n❌ 参数错误: {e}")
                            print(f"💡 提示: 这个步骤可能需要额外参数")
                        else:
                            print(f"\n❌ 执行失败: {e}")
                            import traceback
                            traceback.print_exc()
                    except Exception as e:
                        print(f"\n❌ 执行失败: {e}")
                        import traceback
                        traceback.print_exc()

                    input("\n按回车键继续...")
                else:
                    print("❌ 无效的序号")
                    input("\n按回车键继续...")
            except ValueError:
                print("❌ 请输入数字")
                input("\n按回车键继续...")
            except KeyboardInterrupt:
                return

    # ==================== 快捷命令 ====================

    def do_wechat(self, arg):
        """快速启动微信"""
        self.do_launch("com.tencent.mm")

    def do_alipay(self, arg):
        """快速启动支付宝"""
        self.do_launch("com.eg.android.AlipayGphone")

    # ==================== 退出 ====================

    def do_quit(self, arg):
        """退出程序"""
        print("\n再见！\n")
        return True

    def do_exit(self, arg):
        """退出程序"""
        return self.do_quit(arg)

    def do_EOF(self, arg):
        """Ctrl+D 退出"""
        print()
        return self.do_quit(arg)


def main():
    """主函数"""
    try:
        cli = AutomationCLI()
        # 直接进入菜单模式，而不是命令行模式
        cli.preloop()
        cli.do_menu("")

        # 退出菜单后，进入命令行模式（可选）
        print("\n💡 现在可以使用命令行模式，输入 'help' 查看帮助，'quit' 退出程序")
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\n\n再见！\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
