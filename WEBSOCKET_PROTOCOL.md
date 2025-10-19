# WebSocket 通信协议文档

## 概述

本文档定义了客户端（Android 自动化工具）与服务端之间的 WebSocket 通信协议。

**连接地址：** `ws://your-server.com:8000/ws`

**通信方向：**
- 客户端 → 服务端：注册、心跳、任务结果
- 服务端 → 客户端：任务下发、Ping

---

## 消息格式规范

### 通用规则

1. **编码格式：** UTF-8
2. **数据格式：** JSON
3. **必需字段：** 所有消息必须包含 `type` 字段，用于标识消息类型
4. **时间戳：** 使用 Unix 时间戳（秒）
5. **任务 ID：** 使用 UUID v4 格式

### 消息类型列表

| 消息类型 | 方向 | 说明 |
|---------|------|------|
| `register` | 客户端 → 服务端 | 客户端注册请求 |
| `register_ack` | 服务端 → 客户端 | 注册响应（成功/失败） |
| `heartbeat` | 客户端 → 服务端 | 心跳保活 |
| `task` | 服务端 → 客户端 | 下发任务 |
| `result` | 客户端 → 服务端 | 任务结果 |
| `ping` | 服务端 → 客户端 | Ping 检测（可选） |
| `pong` | 客户端 → 服务端 | Pong 响应（可选） |

---

## 1. 客户端注册 (register)

### 方向
客户端 → 服务端

### 触发时机
客户端连接成功后立即发送

### 消息格式

```json
{
  "type": "register",
  "client_id": "qrcode-helper-client-001",
  "timestamp": 1704067200,
  "device_info": {
    "brand": "Xiaomi",
    "model": "Mi 10",
    "android_version": "11",
    "screen_size": "1080x2340"
  }
}
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| `type` | string | ✅ | 固定值 `"register"` |
| `client_id` | string | ✅ | 客户端唯一标识，建议格式：`qrcode-helper-client-{序号}` |
| `timestamp` | integer | ✅ | 注册时间戳（Unix 秒） |
| `device_info` | object | ✅ | 设备信息对象 |
| `device_info.brand` | string | ✅ | 设备品牌（如 "Xiaomi", "Huawei"） |
| `device_info.model` | string | ✅ | 设备型号（如 "Mi 10"） |
| `device_info.android_version` | string | ✅ | Android 版本号（如 "11"） |
| `device_info.screen_size` | string | ✅ | 屏幕分辨率（格式：`宽x高`） |

### 服务端响应

**必须响应**，确认注册结果

#### 响应格式（成功）

```json
{
  "type": "register_ack",
  "success": true,
  "message": "注册成功",
  "server_time": 1704067200
}
```

#### 响应格式（失败）

```json
{
  "type": "register_ack",
  "success": false,
  "error": "客户端 ID 已存在",
  "code": "CLIENT_ID_CONFLICT",
  "server_time": 1704067200
}
```

#### 响应字段说明

| 字段 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| `type` | string | ✅ | 固定值 `"register_ack"` |
| `success` | boolean | ✅ | 注册结果<br>`true` = 成功<br>`false` = 失败 |
| `message` | string | ❌ | 成功消息（成功时返回） |
| `server_time` | integer | ✅ | 服务端时间戳（Unix 秒）<br>用于客户端时间同步检测 |
| `error` | string | ❌ | 错误信息（失败时返回） |
| `code` | string | ❌ | 错误码（失败时返回） |

#### 注册错误码

| 错误码 | 说明 | 客户端处理建议 |
|-------|------|---------------|
| `CLIENT_ID_CONFLICT` | client_id 已被占用 | **自动处理**：客户端自动添加随机后缀（如 `-1234`）后重新注册 |
| `INVALID_DEVICE_INFO` | 设备信息格式错误 | 检查 device_info 字段 |
| `UNAUTHORIZED` | 未授权（如需要 token） | 提供有效的认证信息 |
| `QUOTA_EXCEEDED` | 超过客户端数量配额 | 稍后重试或联系管理员 |

#### 注册超时处理

客户端在发送 `register` 消息后，会等待服务端响应 **5 秒**：

- **收到响应**：按照 `success` 字段处理成功或失败
- **超时未响应**：假定注册成功，继续执行（容错机制）

#### 客户端自动重试逻辑

当收到 `CLIENT_ID_CONFLICT` 错误时，客户端会自动处理：

1. 在原 client_id 后添加随机 4 位数字（如 `client-001` → `client-001-3847`）
2. 使用新 ID 重新发送 `register` 消息
3. 最多重试 **递归执行**，直至成功或遇到其他错误

#### 时间同步检测

客户端收到 `register_ack` 后会检查时间偏差：

- 计算公式：`|server_time - local_time|`
- **时间偏差 > 60 秒**：输出警告信息
- **时间偏差 ≤ 60 秒**：无提示

此机制用于检测客户端与服务端时间是否同步，避免时间戳相关的问题。

---

## 2. 心跳保活 (heartbeat)

### 方向
客户端 → 服务端

### 触发时机
客户端每 30 秒自动发送一次

### 消息格式

```json
{
  "type": "heartbeat",
  "client_id": "qrcode-helper-client-001",
  "is_busy": false,
  "timestamp": 1704067230
}
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| `type` | string | ✅ | 固定值 `"heartbeat"` |
| `client_id` | string | ✅ | 客户端唯一标识 |
| `is_busy` | boolean | ✅ | 客户端是否正在执行任务<br>`true` = 忙碌<br>`false` = 空闲 |
| `timestamp` | integer | ✅ | 心跳时间戳（Unix 秒） |

### 服务端响应
无需响应，服务端更新客户端状态即可

---

## 3. 任务下发 (task)

### 方向
服务端 → 客户端

### 触发时机
服务端需要客户端执行自动化任务时

### 消息格式

```json
{
  "type": "task",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "app": "sunlogin",
  "workflow": "execute",
  "params": {
    "image_index": 0
  },
  "timeout": 30
}
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| `type` | string | ✅ | 固定值 `"task"` |
| `task_id` | string | ✅ | 任务唯一标识（UUID v4 格式）<br>用于关联任务结果 |
| `app` | string | ✅ | 应用名称<br>可选值：`"sunlogin"`, `"wechat"`, `"alipay"` 等 |
| `workflow` | string | ✅ | 工作流名称<br>通常为 `"execute"` |
| `params` | object | ❌ | 工作流参数（可选）<br>不同工作流参数不同 |
| `timeout` | integer | ❌ | 任务超时时间（秒），默认 30 秒 |

### params 参数说明（按应用）

#### sunlogin 应用

```json
{
  "image_index": 0  // 选择相册中第几张图片（从 0 开始）
}
```

#### wechat / alipay 应用（示例）

```json
{
  "image_index": 0,
  "contact_name": "张三",  // 仅部分工作流需要
  "message": "你好"        // 仅部分工作流需要
}
```

### 客户端响应
客户端执行完任务后，发送 `result` 消息

---

## 4. 任务结果 (result)

### 方向
客户端 → 服务端

### 触发时机
客户端执行任务完成后（成功或失败）

### 消息格式（成功）

```json
{
  "type": "result",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "success": true,
  "app": "sunlogin",
  "workflow": "execute",
  "message": "已完成从相册扫码流程，选择了第 0 张图片",
  "duration": 8.5
}
```

### 消息格式（失败）

```json
{
  "type": "result",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "success": false,
  "error": "点击扫码按钮失败",
  "code": "EXECUTION_ERROR"
}
```

### 消息格式（设备忙碌）

```json
{
  "type": "result",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "success": false,
  "error": "设备忙碌，正在执行其他任务",
  "code": "DEVICE_BUSY"
}
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| `type` | string | ✅ | 固定值 `"result"` |
| `task_id` | string | ✅ | 任务 ID，与下发任务的 `task_id` 一致 |
| `success` | boolean | ✅ | 任务执行结果<br>`true` = 成功<br>`false` = 失败 |
| `app` | string | ❌ | 应用名称（成功时返回） |
| `workflow` | string | ❌ | 工作流名称（成功时返回） |
| `message` | string | ❌ | 成功消息（成功时返回） |
| `duration` | float | ❌ | 任务执行耗时（秒），成功时返回 |
| `error` | string | ❌ | 错误信息（失败时返回） |
| `code` | string | ❌ | 错误码（失败时返回） |

### 错误码列表

| 错误码 | 说明 | 处理建议 |
|-------|------|---------|
| `DEVICE_BUSY` | 设备正在执行其他任务 | 稍后重试 |
| `APP_NOT_FOUND` | 应用不存在 | 检查 app 参数是否正确 |
| `WORKFLOW_NOT_FOUND` | 工作流不存在 | 检查 workflow 参数是否正确 |
| `EXECUTION_ERROR` | 执行过程中出错 | 查看 error 字段详细信息 |
| `TIMEOUT` | 任务执行超时 | 增加 timeout 或检查工作流 |

---

## 5. Ping/Pong

### 方向
- Ping：服务端 → 客户端
- Pong：客户端 → 服务端

### 触发时机
服务端可选择性发送 Ping 检测连接

### Ping 消息格式

```json
{
  "type": "ping"
}
```

### Pong 消息格式

```json
{
  "type": "pong"
}
```

### 说明
- 这是可选机制，客户端已内置 30 秒心跳
- websockets 库本身也有 ping/pong 机制
- 建议依赖 `heartbeat` 消息而非 ping/pong

---

## 通信流程示例

### 1. 客户端连接与注册（成功）

```
客户端                           服务端
  │                                │
  │  WebSocket 连接请求              │
  ├───────────────────────────────>│
  │                                │
  │  连接成功                        │
  │<───────────────────────────────┤
  │                                │
  │  register 消息                  │
  ├───────────────────────────────>│
  │  {                             │
  │    "type": "register",         │
  │    "client_id": "client-001",  │
  │    "device_info": {...}        │
  │  }                             │
  │                                │
  │  (服务端验证并记录客户端信息)      │
  │                                │
  │  register_ack 消息（成功）       │
  │<───────────────────────────────┤
  │  {                             │
  │    "type": "register_ack",     │
  │    "success": true,            │
  │    "message": "注册成功"        │
  │  }                             │
  │                                │
  │  (客户端确认注册成功，开始心跳)   │
  │                                │
```

### 1.1 客户端注册失败处理（ID 冲突自动重试）

```
客户端                           服务端
  │                                │
  │  register 消息                  │
  ├───────────────────────────────>│
  │  {                             │
  │    "client_id": "client-001"   │
  │  }                             │
  │                                │
  │  (服务端检测到 ID 冲突)          │
  │                                │
  │  register_ack 消息（失败）       │
  │<───────────────────────────────┤
  │  {                             │
  │    "type": "register_ack",     │
  │    "success": false,           │
  │    "error": "客户端 ID 已存在",  │
  │    "code": "CLIENT_ID_CONFLICT",│
  │    "server_time": 1704067200   │
  │  }                             │
  │                                │
  │  (客户端自动添加随机后缀)        │
  │  client-001 → client-001-3847  │
  │                                │
  │  register 消息（重试）           │
  ├───────────────────────────────>│
  │  {                             │
  │    "client_id": "client-001-3847"│
  │  }                             │
  │                                │
  │  (服务端验证通过)                │
  │                                │
  │  register_ack 消息（成功）       │
  │<───────────────────────────────┤
  │  {                             │
  │    "type": "register_ack",     │
  │    "success": true,            │
  │    "message": "注册成功",       │
  │    "server_time": 1704067200   │
  │  }                             │
  │                                │
  │  (客户端确认注册成功，开始心跳)   │
  │                                │
```

### 2. 心跳保活

```
客户端                           服务端
  │                                │
  │  (每 30 秒)                     │
  │  heartbeat 消息                 │
  ├───────────────────────────────>│
  │  {                             │
  │    "type": "heartbeat",        │
  │    "is_busy": false            │
  │  }                             │
  │                                │
  │  (服务端更新在线状态)            │
  │                                │
```

### 3. 任务执行流程（成功）

```
客户端                           服务端
  │                                │
  │  task 消息                      │
  │<───────────────────────────────┤
  │  {                             │
  │    "type": "task",             │
  │    "task_id": "uuid-1234",     │
  │    "app": "sunlogin",          │
  │    "workflow": "execute"       │
  │  }                             │
  │                                │
  │  (执行工作流...)                 │
  │                                │
  │  result 消息                    │
  ├───────────────────────────────>│
  │  {                             │
  │    "type": "result",           │
  │    "task_id": "uuid-1234",     │
  │    "success": true,            │
  │    "duration": 8.5             │
  │  }                             │
  │                                │
```

### 4. 任务执行流程（失败）

```
客户端                           服务端
  │                                │
  │  task 消息                      │
  │<───────────────────────────────┤
  │                                │
  │  (检测到设备忙碌)                 │
  │                                │
  │  result 消息                    │
  ├───────────────────────────────>│
  │  {                             │
  │    "type": "result",           │
  │    "task_id": "uuid-1234",     │
  │    "success": false,           │
  │    "code": "DEVICE_BUSY"       │
  │  }                             │
  │                                │
```

### 5. 连接断开与重连

```
客户端                           服务端
  │                                │
  │  (网络断开)                     │
  │  X────────────────────────────X│
  │                                │
  │  (服务端检测到连接关闭)          │
  │                                │
  │  (5秒后自动重连)                 │
  │  WebSocket 连接请求              │
  ├───────────────────────────────>│
  │                                │
  │  连接成功                        │
  │<───────────────────────────────┤
  │                                │
  │  register 消息                  │
  ├───────────────────────────────>│
  │                                │
```

---

## 服务端实现要点

### 1. 客户端注册处理

```python
import time
import json

# 处理注册请求
async def handle_register(websocket, data):
    client_id = data.get("client_id")
    device_info = data.get("device_info", {})

    # 检查 client_id 是否已存在
    if client_id in clients:
        # 发送冲突响应
        ack_msg = {
            "type": "register_ack",
            "success": False,
            "error": "客户端 ID 已存在",
            "code": "CLIENT_ID_CONFLICT",
            "server_time": int(time.time())
        }
        await websocket.send(json.dumps(ack_msg))
        return False

    # 注册成功
    clients[client_id] = websocket
    client_info[client_id] = {
        "device_info": device_info,
        "last_heartbeat": int(time.time()),
        "is_busy": False
    }

    # 发送成功响应
    ack_msg = {
        "type": "register_ack",
        "success": True,
        "message": "注册成功",
        "server_time": int(time.time())
    }
    await websocket.send(json.dumps(ack_msg))
    return True
```

### 2. 客户端管理

```python
# 维护客户端连接字典
clients = {
    "client-001": websocket_instance,
    "client-002": websocket_instance,
}

# 维护客户端信息
client_info = {
    "client-001": {
        "device_info": {...},
        "last_heartbeat": 1704067230,
        "is_busy": false
    }
}
```

### 3. 任务管理

```python
# 维护待处理任务
pending_tasks = {
    "uuid-1234": asyncio.Future(),  # 用于等待结果
}

# 发送任务
async def send_task(client_id, app, workflow, params):
    task_id = str(uuid.uuid4())
    future = asyncio.Future()
    pending_tasks[task_id] = future

    # 发送任务消息
    await clients[client_id].send(json.dumps({
        "type": "task",
        "task_id": task_id,
        "app": app,
        "workflow": workflow,
        "params": params
    }))

    # 等待结果
    result = await asyncio.wait_for(future, timeout=30)
    return result
```

### 4. 心跳超时检测

```python
# 定期检查心跳超时（建议 60 秒）
async def check_heartbeat_timeout():
    while True:
        await asyncio.sleep(60)
        now = time.time()
        for client_id, info in client_info.items():
            if now - info["last_heartbeat"] > 60:
                # 心跳超时，断开连接
                await clients[client_id].close()
                del clients[client_id]
```

---

## 客户端实现要点

### 1. 注册与自动重试

```python
import asyncio
import random
import time

async def register(ws, client_id):
    """注册客户端，支持自动重试"""
    register_msg = {
        "type": "register",
        "client_id": client_id,
        "timestamp": int(time.time()),
        "device_info": {
            "brand": "Xiaomi",
            "model": "Mi 10",
            "android_version": "11",
            "screen_size": "1080x2340"
        }
    }

    await ws.send(json.dumps(register_msg))

    # 等待服务端响应（超时 5 秒）
    try:
        response = await asyncio.wait_for(ws.recv(), timeout=5.0)
        data = json.loads(response)

        if data.get("type") == "register_ack":
            if data.get("success"):
                # 注册成功
                print("注册成功")

                # 检查时间同步
                if "server_time" in data:
                    server_time = data["server_time"]
                    local_time = int(time.time())
                    time_diff = abs(server_time - local_time)
                    if time_diff > 60:
                        print(f"警告: 时间偏差 {time_diff} 秒")

                return client_id
            else:
                # 注册失败
                code = data.get("code")
                if code == "CLIENT_ID_CONFLICT":
                    # ID 冲突，自动重试
                    new_id = f"{client_id}-{random.randint(1000, 9999)}"
                    print(f"ID 冲突，使用新 ID: {new_id}")
                    return await register(ws, new_id)  # 递归重试
                else:
                    raise Exception(f"注册失败: {data.get('error')}")

    except asyncio.TimeoutError:
        # 超时假定成功
        print("注册响应超时，假定成功")
        return client_id
```

### 2. 自动重连

```python
while True:
    try:
        async with websockets.connect(server_url) as ws:
            # 注册客户端
            client_id = await register(ws, "qrcode-helper-client")
            # 启动心跳和任务监听
            await listen_tasks(ws, client_id)
    except:
        await asyncio.sleep(5)  # 5秒后重连
```

### 3. 忙碌状态管理

```python
is_busy = False

async def handle_task(task):
    global is_busy

    if is_busy:
        # 拒绝任务
        return {"success": False, "code": "DEVICE_BUSY"}

    is_busy = True
    try:
        result = execute_workflow(task)
        return result
    finally:
        is_busy = False
```

---

## 安全建议

1. **使用 WSS（WebSocket Secure）**
   - 生产环境建议使用 `wss://` 而非 `ws://`
   - 配置 SSL 证书

2. **身份验证**
   - 在 `register` 消息中添加 token 字段
   - 服务端验证 token 有效性

3. **消息签名**
   - 对关键消息进行签名验证
   - 防止消息篡改

4. **频率限制**
   - 限制任务下发频率
   - 防止恶意调用

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|-----|------|---------|
| 1.1 | 2025-01-19 | 完善注册确认机制<br>- 添加 `register_ack` 必须响应要求<br>- `server_time` 字段改为必需<br>- 新增客户端自动重试逻辑<br>- 新增时间同步检测机制<br>- 完善注册失败处理流程 |
| 1.0 | 2025-01-19 | 初始版本 |

---

## 联系方式

如有疑问，请参考：
- 客户端代码：`ws_client.py`
- 服务端示例：`server_example.py`
