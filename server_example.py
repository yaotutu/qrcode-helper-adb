#!/usr/bin/env python3
"""WebSocket 服务端示例

这是一个简单的 WebSocket 服务端实现，用于接收客户端连接并下发任务。
你可以将此代码集成到你的实际服务端项目中。

依赖安装：
    pip install websockets

运行方式：
    python server_example.py
"""
import asyncio
import websockets
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Set


class TaskServer:
    """WebSocket 任务服务端"""

    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}  # client_id -> websocket
        self.client_info: Dict[str, dict] = {}  # client_id -> device_info
        self.pending_tasks: Dict[str, asyncio.Future] = {}  # task_id -> future

    async def start(self):
        """启动服务端"""
        print(f"{'='*60}")
        print(f"🚀 WebSocket 服务端启动")
        print(f"{'='*60}")
        print(f"📡 监听地址: ws://{self.host}:{self.port}/ws")
        print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()  # 永久运行

    async def handle_client(self, websocket, path):
        """处理客户端连接"""
        client_id = None

        try:
            print(f"📱 新客户端连接: {websocket.remote_address}")

            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")

                    if msg_type == "register":
                        # 注册客户端
                        client_id = data.get("client_id")
                        device_info = data.get("device_info", {})

                        # 检查 client_id 是否已存在
                        if client_id in self.clients:
                            # 发送冲突响应
                            ack_msg = {
                                "type": "register_ack",
                                "success": False,
                                "error": "客户端 ID 已存在",
                                "code": "CLIENT_ID_CONFLICT",
                                "server_time": int(time.time())
                            }
                            await websocket.send(json.dumps(ack_msg))
                            print(f"⚠️ 客户端注册失败: {client_id} (ID 冲突)\n")
                        else:
                            # 注册成功
                            self.clients[client_id] = websocket
                            self.client_info[client_id] = device_info

                            # 发送成功响应
                            ack_msg = {
                                "type": "register_ack",
                                "success": True,
                                "message": "注册成功",
                                "server_time": int(time.time())
                            }
                            await websocket.send(json.dumps(ack_msg))

                            print(f"✅ 客户端已注册: {client_id}")
                            print(f"   设备信息: {device_info.get('brand')} {device_info.get('model')}")
                            print(f"   在线客户端数: {len(self.clients)}\n")

                    elif msg_type == "heartbeat":
                        # 心跳响应
                        is_busy = data.get("is_busy", False)
                        print(f"💓 收到心跳: {client_id} [忙碌: {is_busy}]")

                    elif msg_type == "result":
                        # 任务结果
                        task_id = data.get("task_id")
                        success = data.get("success")

                        print(f"\n{'='*60}")
                        print(f"📥 收到任务结果: {task_id}")
                        print(f"   成功: {success}")
                        if success:
                            print(f"   消息: {data.get('message')}")
                            print(f"   耗时: {data.get('duration')} 秒")
                        else:
                            print(f"   错误: {data.get('error')}")
                        print(f"{'='*60}\n")

                        # 唤醒等待的任务
                        if task_id in self.pending_tasks:
                            self.pending_tasks[task_id].set_result(data)

                    elif msg_type == "pong":
                        # ping-pong 响应
                        pass

                except json.JSONDecodeError:
                    print(f"⚠️ 无效的 JSON 消息: {message}")
                except Exception as e:
                    print(f"❌ 处理消息失败: {e}")

        except websockets.exceptions.ConnectionClosed:
            print(f"📴 客户端断开连接: {client_id or websocket.remote_address}")
        except Exception as e:
            print(f"❌ 连接错误: {e}")
        finally:
            # 清理客户端
            if client_id and client_id in self.clients:
                del self.clients[client_id]
                if client_id in self.client_info:
                    del self.client_info[client_id]
                print(f"🗑️ 已清理客户端: {client_id}")
                print(f"   剩余在线客户端: {len(self.clients)}\n")

    async def send_task(self, client_id: str, app: str, workflow: str, params: dict = None, timeout: int = 30) -> dict:
        """
        向客户端发送任务并等待结果

        Args:
            client_id: 客户端 ID
            app: 应用名称
            workflow: 工作流名称
            params: 参数字典
            timeout: 超时时间（秒）

        Returns:
            任务执行结果
        """
        if client_id not in self.clients:
            return {
                "success": False,
                "error": f"客户端 '{client_id}' 未连接",
                "code": "CLIENT_NOT_FOUND"
            }

        task_id = str(uuid.uuid4())
        task_msg = {
            "type": "task",
            "task_id": task_id,
            "app": app,
            "workflow": workflow,
            "params": params or {},
            "timeout": timeout
        }

        # 创建等待future
        future = asyncio.Future()
        self.pending_tasks[task_id] = future

        try:
            # 发送任务
            ws = self.clients[client_id]
            await ws.send(json.dumps(task_msg))

            print(f"\n{'='*60}")
            print(f"📤 已发送任务: {task_id}")
            print(f"   客户端: {client_id}")
            print(f"   应用: {app}")
            print(f"   工作流: {workflow}")
            print(f"   参数: {params}")
            print(f"{'='*60}\n")

            # 等待结果
            result = await asyncio.wait_for(future, timeout=timeout)
            return result

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"任务执行超时（{timeout}秒）",
                "code": "TIMEOUT"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "code": "SEND_ERROR"
            }
        finally:
            # 清理
            if task_id in self.pending_tasks:
                del self.pending_tasks[task_id]

    def get_online_clients(self) -> list:
        """获取在线客户端列表"""
        return [
            {
                "client_id": client_id,
                "device_info": self.client_info.get(client_id, {}),
                "connected": True
            }
            for client_id in self.clients.keys()
        ]


# ==================== 使用示例 ====================

async def example_usage():
    """示例：启动服务端并发送任务"""
    server = TaskServer(host="0.0.0.0", port=8000)

    # 启动服务端（在后台运行）
    server_task = asyncio.create_task(server.start())

    # 等待客户端连接
    await asyncio.sleep(5)

    # 示例：向客户端发送任务
    # 注意：这只是演示，实际使用时你需要在合适的时机调用
    while True:
        await asyncio.sleep(10)

        # 获取在线客户端
        clients = server.get_online_clients()
        if clients:
            client_id = clients[0]["client_id"]
            print(f"\n🧪 测试：向客户端 {client_id} 发送任务...\n")

            # 发送任务
            result = await server.send_task(
                client_id=client_id,
                app="sunlogin",
                workflow="execute",
                params={"image_index": 0},
                timeout=30
            )

            print(f"\n🧪 测试结果: {result}\n")


# ==================== 集成到 FastAPI 示例 ====================

"""
如果你使用 FastAPI，可以这样集成：

from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse

app = FastAPI()
task_server = TaskServer()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await task_server.handle_client(websocket, websocket.url.path)

@app.post("/api/task/send")
async def send_task_api(
    client_id: str,
    app: str,
    workflow: str,
    params: dict = None
):
    result = await task_server.send_task(
        client_id=client_id,
        app=app,
        workflow=workflow,
        params=params
    )
    return JSONResponse(content=result)

@app.get("/api/clients")
async def get_clients():
    clients = task_server.get_online_clients()
    return JSONResponse(content={"clients": clients})
"""


if __name__ == "__main__":
    try:
        # 简单模式：只启动服务端
        server = TaskServer(host="0.0.0.0", port=8000)
        asyncio.run(server.start())

        # 高级模式：启动服务端并测试发送任务（取消注释下面一行）
        # asyncio.run(example_usage())

    except KeyboardInterrupt:
        print("\n\n👋 服务端已停止\n")
