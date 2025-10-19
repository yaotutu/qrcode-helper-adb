#!/usr/bin/env python3
"""WebSocket 客户端 - 连接服务端并监听任务

架构说明：
    服务端（公网）← WebSocket连接 ← 客户端（内网）
    服务端下发任务 → 客户端执行工作流 → 返回结果

使用方法：
    uv run ws_client.py --server ws://your-server.com:8000/ws
"""
import asyncio
import websockets
import json
import sys
import argparse
import time
from datetime import datetime
from device import get_device_manager
from actions import Actions
import importlib


class TaskClient:
    """WebSocket 任务客户端"""

    def __init__(self, server_url: str, client_id: str = "qrcode-helper-client"):
        """
        初始化客户端

        Args:
            server_url: WebSocket 服务端地址（如 ws://example.com:8000/ws）
            client_id: 客户端唯一标识
        """
        self.server_url = server_url
        self.client_id = client_id
        self.device_manager = None
        self.device = None
        self.actions = None
        self.ws = None
        self.is_busy = False  # 任务执行状态
        self.heartbeat_task = None
        self.reconnect_interval = 5  # 重连间隔（秒）

    async def connect(self):
        """连接服务端并保持重连"""
        # 初始化设备
        await self._init_device()

        # 循环重连
        while True:
            try:
                print(f"\n{'='*60}")
                print(f"⏳ 正在连接服务端: {self.server_url}")
                print(f"{'='*60}")

                async with websockets.connect(
                    self.server_url,
                    ping_interval=30,  # 每30秒发送ping
                    ping_timeout=10,  # ping超时时间
                ) as ws:
                    self.ws = ws
                    print(f"✅ 已连接到服务端")
                    print(f"⏰ 连接时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

                    # 注册设备
                    await self._register()

                    # 启动心跳
                    self.heartbeat_task = asyncio.create_task(self._heartbeat())

                    # 监听任务
                    await self._listen_tasks()

            except websockets.exceptions.ConnectionClosed:
                print(f"\n❌ 连接已关闭")
                await self._cleanup()
            except Exception as e:
                print(f"\n❌ 连接错误: {e}")
                await self._cleanup()

            # 等待重连
            print(f"⏳ {self.reconnect_interval} 秒后尝试重连...\n")
            await asyncio.sleep(self.reconnect_interval)

    async def _init_device(self):
        """初始化设备连接"""
        try:
            print("⏳ 正在连接 Android 设备...")
            self.device_manager = get_device_manager()
            self.device = self.device_manager.connect()
            self.actions = Actions(self.device)
            print("✅ 设备已连接\n")
        except Exception as e:
            print(f"❌ 设备连接失败: {e}")
            print("请确保设备已连接并开启 USB 调试\n")
            sys.exit(1)

    async def _register(self):
        """向服务端注册设备信息并等待响应"""
        device_info = self.device.info
        register_msg = {
            "type": "register",
            "client_id": self.client_id,
            "timestamp": int(time.time()),
            "device_info": {
                "brand": device_info.get("brand", "Unknown"),
                "model": device_info.get("model", "Unknown"),
                "android_version": device_info.get("version", "Unknown"),
                "screen_size": f"{device_info.get('displayWidth')}x{device_info.get('displayHeight')}",
            },
        }

        await self.ws.send(json.dumps(register_msg))
        print(f"📤 已发送注册请求: {self.client_id}")

        # 等待服务端响应（超时 5 秒）
        try:
            response = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
            data = json.loads(response)

            if data.get("type") == "register_ack":
                if data.get("success"):
                    print(f"✅ 注册成功: {data.get('message', '已注册')}")
                    if "server_time" in data:
                        server_time = data["server_time"]
                        local_time = int(time.time())
                        time_diff = abs(server_time - local_time)
                        if time_diff > 60:
                            print(f"⚠️  时间偏差: {time_diff} 秒（服务端时间: {server_time}，本地时间: {local_time}）")
                else:
                    error = data.get("error", "未知错误")
                    code = data.get("code", "UNKNOWN")
                    print(f"❌ 注册失败: {error} (错误码: {code})")

                    # 根据错误码处理
                    if code == "CLIENT_ID_CONFLICT":
                        # client_id 冲突，自动添加随机后缀重试
                        import random
                        new_id = f"{self.client_id}-{random.randint(1000, 9999)}"
                        print(f"🔄 尝试使用新 ID: {new_id}")
                        self.client_id = new_id
                        # 递归重新注册
                        await self._register()
                    else:
                        # 其他错误，抛出异常
                        raise Exception(f"注册失败: {error}")
            else:
                print(f"⚠️  收到非预期消息: {data.get('type')}")

        except asyncio.TimeoutError:
            print(f"⚠️  注册响应超时（5秒），假定注册成功")
        except json.JSONDecodeError:
            print(f"⚠️  注册响应格式错误")
        except Exception as e:
            print(f"❌ 注册过程出错: {e}")
            raise

    async def _heartbeat(self):
        """心跳保活（每30秒）"""
        try:
            while True:
                await asyncio.sleep(30)
                if self.ws and not self.ws.closed:
                    heartbeat_msg = {
                        "type": "heartbeat",
                        "client_id": self.client_id,
                        "is_busy": self.is_busy,
                        "timestamp": int(time.time()),
                    }
                    await self.ws.send(json.dumps(heartbeat_msg))
                    print(f"💓 心跳已发送 [忙碌: {self.is_busy}]")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"⚠️ 心跳错误: {e}")

    async def _listen_tasks(self):
        """监听并处理任务"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")

                    if msg_type == "task":
                        # 处理任务
                        await self._handle_task(data)
                    elif msg_type == "ping":
                        # 响应 ping
                        await self.ws.send(json.dumps({"type": "pong"}))
                    elif msg_type == "register_ack":
                        # 注册响应已在 _register() 中处理，这里忽略
                        pass
                    elif msg_type == "cancel":
                        # 取消任务（暂不支持）
                        task_id = data.get("task_id")
                        print(f"⚠️ 收到取消任务请求: {task_id}（暂不支持）")
                    else:
                        print(f"⚠️ 未知消息类型: {msg_type}")

                except json.JSONDecodeError:
                    print(f"⚠️ 无效的 JSON 消息: {message}")
                except Exception as e:
                    print(f"❌ 处理消息失败: {e}")

        except asyncio.CancelledError:
            pass

    async def _handle_task(self, task):
        """处理任务"""
        task_id = task.get("task_id")
        app_name = task.get("app")
        workflow_name = task.get("workflow")
        params = task.get("params", {})

        print(f"\n{'='*60}")
        print(f"📥 收到任务: {task_id}")
        print(f"   应用: {app_name}")
        print(f"   工作流: {workflow_name}")
        print(f"   参数: {params}")
        print(f"{'='*60}\n")

        # 检查是否忙碌
        if self.is_busy:
            error_msg = {
                "type": "result",
                "task_id": task_id,
                "success": False,
                "error": "设备忙碌，正在执行其他任务",
                "code": "DEVICE_BUSY",
            }
            await self.ws.send(json.dumps(error_msg))
            print(f"❌ 任务被拒绝: 设备忙碌\n")
            return

        # 标记为忙碌
        self.is_busy = True
        start_time = time.time()

        try:
            # 动态导入工作流
            module = importlib.import_module(f"apps.{app_name}")
            workflows = getattr(module, "WORKFLOWS", {})

            if workflow_name not in workflows:
                raise ValueError(f"工作流 '{workflow_name}' 不存在")

            workflow_func = workflows[workflow_name]

            # 执行工作流
            result = workflow_func(self.actions, **params)

            # 添加执行时长
            duration = round(time.time() - start_time, 2)
            result["duration"] = duration
            result["task_id"] = task_id
            result["type"] = "result"

            # 发送结果
            await self.ws.send(json.dumps(result))

            if result.get("success"):
                print(f"\n✅ 任务执行成功: {task_id}")
                print(f"   耗时: {duration} 秒\n")
            else:
                print(f"\n❌ 任务执行失败: {task_id}")
                print(f"   错误: {result.get('error')}\n")

        except ModuleNotFoundError:
            error_msg = {
                "type": "result",
                "task_id": task_id,
                "success": False,
                "error": f"应用 '{app_name}' 不存在",
                "code": "APP_NOT_FOUND",
            }
            await self.ws.send(json.dumps(error_msg))
            print(f"❌ 应用不存在: {app_name}\n")

        except Exception as e:
            error_msg = {
                "type": "result",
                "task_id": task_id,
                "success": False,
                "error": str(e),
                "code": "EXECUTION_ERROR",
            }
            await self.ws.send(json.dumps(error_msg))
            print(f"❌ 任务执行异常: {e}\n")
            import traceback
            traceback.print_exc()

        finally:
            # 解除忙碌状态
            self.is_busy = False

    async def _cleanup(self):
        """清理资源"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
            self.heartbeat_task = None


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="WebSocket 任务客户端")
    parser.add_argument(
        "--server",
        "-s",
        default="ws://localhost:8000/ws",
        help="WebSocket 服务端地址（默认: ws://localhost:8000/ws）",
    )
    parser.add_argument(
        "--client-id",
        "-c",
        default="qrcode-helper-client",
        help="客户端 ID（默认: qrcode-helper-client）",
    )

    args = parser.parse_args()

    print("""
╔══════════════════════════════════════════════════════════════╗
║          二维码助手 - WebSocket 客户端模式                    ║
╚══════════════════════════════════════════════════════════════╝
""")
    print(f"🔗 服务端地址: {args.server}")
    print(f"🆔 客户端 ID: {args.client_id}")
    print()

    # 创建并启动客户端
    client = TaskClient(server_url=args.server, client_id=args.client_id)

    try:
        await client.connect()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，正在退出...\n")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
