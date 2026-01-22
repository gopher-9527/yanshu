# Yanshu 通信协议规范

## 一、协议概述

### 1.1 设计原则

- **二进制协议**：避免 JSON 解析开销，降低延迟
- **固定帧长**：音频帧固定长度，便于 buffer 管理
- **类型明确**：每个帧都有明确的类型标识
- **低开销**：最小化协议头大小

### 1.2 传输层

- **协议**：TCP 长连接
- **字节序**：网络字节序（大端）
- **编码**：UTF-8（文本字段）

## 二、帧格式定义

### 2.1 通用帧头

所有帧都遵循以下通用格式：

```
┌──────────┬──────────┬──────────────┐
│   TYPE   │   LEN     │   PAYLOAD    │
│  (1B)    │   (2B)    │  (0-65535B)  │
└──────────┴──────────┴──────────────┘
```

**字段说明**：

- **TYPE** (1 byte): 帧类型，见类型定义表
- **LEN** (2 bytes, big-endian): Payload 长度（不包括帧头）
- **PAYLOAD** (变长): 帧数据

### 2.2 帧类型定义

#### 2.2.1 控制帧（0x00 - 0x0F）

| 类型值 | 名称          | 方向         | 说明                 |
| ------ | ------------- | ------------ | -------------------- |
| 0x01   | START_CAPTURE | MCU → Server | 开始录音             |
| 0x02   | AUDIO_DATA    | MCU → Server | 音频数据             |
| 0x03   | END_CAPTURE   | MCU → Server | 结束录音             |
| 0x04   | INTERRUPT     | MCU → Server | 用户打断             |
| 0x05   | DEVICE_INFO   | MCU → Server | 设备信息（首次连接） |

#### 2.2.2 音频帧（0x10 - 0x1F）

| 类型值 | 名称        | 方向         | 说明         |
| ------ | ----------- | ------------ | ------------ |
| 0x10   | AUDIO_START | Server → MCU | 开始播放音频 |
| 0x11   | AUDIO_CHUNK | Server → MCU | 音频数据块   |
| 0x12   | AUDIO_END   | Server → MCU | 播放结束     |

#### 2.2.3 系统帧（0x20 - 0x2F）

| 类型值 | 名称      | 方向 | 说明     |
| ------ | --------- | ---- | -------- |
| 0x20   | HEARTBEAT | 双向 | 心跳     |
| 0x21   | ACK       | 双向 | 确认     |
| 0x22   | NACK      | 双向 | 否定确认 |
| 0x30   | ERROR     | 双向 | 错误消息 |

## 三、帧格式详解

### 3.1 START_CAPTURE (0x01)

**方向**: MCU → Server  
**说明**: 用户按下按键，开始录音

**Payload 格式**:

```
┌──────────────┬──────────────┐
│  SESSION_ID  │  TIMESTAMP   │
│  (16 bytes)  │   (8 bytes)  │
└──────────────┴──────────────┘
```

**字段说明**:

- **SESSION_ID** (16 bytes): UUID (big-endian)
- **TIMESTAMP** (8 bytes): Unix 时间戳（毫秒，big-endian）

**示例**:

```
TYPE: 0x01
LEN:  0x0018 (24 bytes)
PAYLOAD:
  SESSION_ID: 550e8400-e29b-41d4-a716-446655440000
  TIMESTAMP:  1704067200000
```

### 3.2 AUDIO_DATA (0x02)

**方向**: MCU → Server  
**说明**: 音频数据帧（固定长度）

**Payload 格式**:

```
┌──────────┬──────────────┬──────────────┬──────────────┐
│   SEQ    │  TIMESTAMP   │  SAMPLE_RATE │   PCM_DATA   │
│  (2B)    │   (8B)       │    (2B)      │  (640B)      │
└──────────┴──────────────┴──────────────┴──────────────┘
```

**字段说明**:

- **SEQ** (2 bytes): 序列号（big-endian），用于检测丢包
- **TIMESTAMP** (8 bytes): 时间戳（毫秒，big-endian）
- **SAMPLE_RATE** (2 bytes): 采样率（默认 16000，big-endian）
- **PCM_DATA** (640 bytes): PCM 数据
  - 格式: 16-bit, mono
  - 时长: 20ms @ 16kHz
  - 大小: 16000 _ 0.02 _ 2 = 640 bytes

**示例**:

```
TYPE: 0x02
LEN:  0x0284 (644 bytes = 2+8+2+640)
PAYLOAD:
  SEQ: 0x0001
  TIMESTAMP: 1704067200000
  SAMPLE_RATE: 0x3E80 (16000)
  PCM_DATA: [640 bytes of PCM samples]
```

### 3.3 END_CAPTURE (0x03)

**方向**: MCU → Server  
**说明**: 用户松开按键，结束录音

**Payload 格式**:

```
┌──────────────┐
│  SESSION_ID  │
│  (16 bytes)  │
└──────────────┘
```

**字段说明**:

- **SESSION_ID** (16 bytes): 与 START_CAPTURE 中的 SESSION_ID 相同

### 3.4 INTERRUPT (0x04)

**方向**: MCU → Server  
**说明**: 用户打断当前播放

**Payload 格式**:

```
┌──────────┬──────────────┐
│  REASON  │  TIMESTAMP   │
│  (1B)    │   (8B)       │
└──────────┴──────────────┘
```

**字段说明**:

- **REASON** (1 byte): 打断原因
  - 0x00: 按键打断
  - 0x01: 超时
  - 0x02: 其他
- **TIMESTAMP** (8 bytes): 时间戳（毫秒）

### 3.5 DEVICE_INFO (0x05)

**方向**: MCU → Server  
**说明**: 设备信息（首次连接时发送）

**Payload 格式**:

```
┌──────────┬──────────────┬──────────────┐
│  VERSION │  DEVICE_ID   │   FEATURES   │
│  (4B)    │  (32B)       │    (1B)      │
└──────────┴──────────────┴──────────────┘
```

**字段说明**:

- **VERSION** (4 bytes): 协议版本（big-endian）
- **DEVICE_ID** (32 bytes): 设备唯一标识（UTF-8 字符串，不足补 0）
- **FEATURES** (1 byte): 功能标志位
  - Bit 0: 支持打断 (1=支持)
  - Bit 1: 支持 VAD (1=支持)
  - Bit 2-7: 保留

### 3.6 AUDIO_START (0x10)

**方向**: Server → MCU  
**说明**: 开始播放音频流

**Payload 格式**:

```
┌──────────────┬──────────────┬──────────────┐
│  SESSION_ID  │  SAMPLE_RATE │  FORMAT      │
│  (16 bytes)  │   (2B)       │   (1B)       │
└──────────────┴──────────────┴──────────────┘
```

**字段说明**:

- **SESSION_ID** (16 bytes): 会话 ID
- **SAMPLE_RATE** (2 bytes): 采样率（默认 16000）
- **FORMAT** (1 byte): 音频格式
  - 0x00: PCM 16-bit mono
  - 0x01-0xFF: 保留

### 3.7 AUDIO_CHUNK (0x11)

**方向**: Server → MCU  
**说明**: 音频数据块（流式）

**Payload 格式**:

```
┌──────────┬──────────────┬──────────────┐
│   SEQ    │  TIMESTAMP   │   PCM_DATA   │
│  (2B)    │   (8B)       │  (变长)      │
└──────────┴──────────────┴──────────────┘
```

**字段说明**:

- **SEQ** (2 bytes): 序列号
- **TIMESTAMP** (8 bytes): 时间戳
- **PCM_DATA** (变长): PCM 数据（通常 640 bytes，20ms）

**注意**: 如果收到 INTERRUPT，服务端应立即停止发送 AUDIO_CHUNK，并发送 AUDIO_END。

### 3.8 AUDIO_END (0x12)

**方向**: Server → MCU  
**说明**: 音频播放结束

**Payload 格式**:

```
┌──────────────┐
│  SESSION_ID  │
│  (16 bytes)  │
└──────────────┘
```

### 3.9 HEARTBEAT (0x20)

**方向**: 双向  
**说明**: 心跳帧，保持连接活跃

**Payload 格式**:

```
┌──────────────┐
│  TIMESTAMP   │
│  (8 bytes)   │
└──────────────┘
```

**字段说明**:

- **TIMESTAMP** (8 bytes): 发送时间戳（毫秒）

**行为**:

- MCU 每 10 秒发送一次
- Server 收到后立即回复相同帧
- 如果 30 秒未收到心跳，认为连接断开

### 3.10 ACK (0x21)

**方向**: 双向  
**说明**: 确认收到帧

**Payload 格式**:

```
┌──────────┬──────────────┐
│  TYPE    │     SEQ      │
│  (1B)    │    (2B)      │
└──────────┴──────────────┘
```

**字段说明**:

- **TYPE** (1 byte): 被确认的帧类型
- **SEQ** (2 bytes): 被确认的帧序列号（如果是音频帧）

### 3.11 NACK (0x22)

**方向**: 双向  
**说明**: 否定确认（请求重传）

**Payload 格式**:

```
┌──────────┬──────────────┬──────────────┐
│  TYPE    │     SEQ      │    REASON    │
│  (1B)    │    (2B)      │    (1B)      │
└──────────┴──────────────┴──────────────┘
```

**字段说明**:

- **TYPE** (1 byte): 被否定的帧类型
- **SEQ** (2 bytes): 被否定的帧序列号
- **REASON** (1 byte): 原因
  - 0x00: 校验失败
  - 0x01: 格式错误
  - 0x02: 其他

### 3.12 ERROR (0x30)

**方向**: 双向  
**说明**: 错误消息

**Payload 格式**:

```
┌──────────────┬──────────────┬──────────────┐
│  ERROR_CODE  │  ERROR_MSG   │   DETAILS    │
│   (2B)       │   (变长)     │   (变长)     │
└──────────────┴──────────────┴──────────────┘
```

**字段说明**:

- **ERROR_CODE** (2 bytes): 错误码（big-endian）
- **ERROR_MSG** (变长, UTF-8): 错误消息（以 \0 结尾）
- **DETAILS** (变长, 可选): 错误详情（JSON 格式，可选）

**错误码定义**:

- 0x0001: 协议版本不兼容
- 0x0002: 会话不存在
- 0x0003: 音频格式不支持
- 0x0004: 服务端忙
- 0x0005: ASR 失败
- 0x0006: TTS 失败
- 0x0007: Agent 错误
- 0x0100-0xFFFF: 自定义错误

## 四、协议流程

### 4.1 连接建立

```
MCU                           Server
 │                              │
 │─── DEVICE_INFO (0x05) ──────>│
 │                              │─── 验证设备 ──┐
 │                              │              │
 │<── ACK (0x21) ───────────────│<─────────────┘
 │                              │
 │─── HEARTBEAT (0x20) ────────>│
 │<── HEARTBEAT (0x20) ─────────│
```

### 4.2 正常对话流程

```
MCU                           Server
 │                              │
 │─── START_CAPTURE (0x01) ────>│
 │                              │─── 创建会话 ──┐
 │                              │              │
 │─── AUDIO_DATA (0x02, seq=1) ─>│              │
 │                              │─── ASR 处理 ──┤
 │─── AUDIO_DATA (0x02, seq=2) ─>│              │
 │                              │              │
 │─── AUDIO_DATA (0x02, seq=3) ─>│              │
 │                              │              │
 │─── END_CAPTURE (0x03) ───────>│              │
 │                              │<── ASR 完成 ──┘
 │                              │─── Agent 处理 ──┐
 │                              │                 │
 │                              │<── LLM 响应 ────┤
 │                              │                 │
 │                              │<── TTS 合成 ─────┘
 │<── AUDIO_START (0x10) ───────│
 │                              │
 │<── AUDIO_CHUNK (0x11, seq=1) ─│
 │                              │
 │<── AUDIO_CHUNK (0x11, seq=2) ─│
 │                              │
 │<── AUDIO_CHUNK (0x11, seq=3) ─│
 │                              │
 │<── AUDIO_END (0x12) ─────────│
 │                              │
```

### 4.3 打断流程

```
MCU                           Server
 │                              │
 │<── AUDIO_CHUNK (0x11, seq=5) ─│ (正在播放)
 │                              │
 │─── INTERRUPT (0x04) ────────>│
 │                              │─── 立即停止 TTS ──┐
 │                              │                  │
 │                              │<── 停止播放 ──────┘
 │<── AUDIO_END (0x12) ─────────│
 │                              │
 │─── START_CAPTURE (0x01) ────>│ (新对话)
 │                              │
```

### 4.4 错误处理流程

```
MCU                           Server
 │                              │
 │─── AUDIO_DATA (0x02) ───────>│
 │                              │─── 处理失败 ──┐
 │                              │              │
 │<── ERROR (0x30) ─────────────│<─────────────┘
 │                              │
 │─── ACK (0x21) ──────────────>│ (确认收到错误)
 │                              │
```

## 五、实现建议

### 5.1 MCU 端实现

**关键点**:

1. **Buffer 管理**: 使用环形缓冲区管理音频数据
2. **序列号**: 每个 AUDIO_DATA 帧递增序列号
3. **超时处理**:
   - 录音超时: 30 秒自动发送 END_CAPTURE
   - 响应超时: 10 秒未收到响应，发送 ERROR
4. **重连机制**: 连接断开后，指数退避重连

**伪代码示例**:

```rust
// 发送音频帧
fn send_audio_frame(seq: u16, pcm_data: &[u8]) {
    let frame = AudioFrame {
        type: 0x02,
        seq: seq,
        timestamp: get_timestamp(),
        sample_rate: 16000,
        pcm_data: pcm_data,
    };
    tcp_send(&frame.encode());
}
```

### 5.2 服务端实现

**关键点**:

1. **流式处理**: 收到 AUDIO_DATA 立即送入 ASR，不等待 END_CAPTURE
2. **背压控制**: 如果 TTS 生成速度 > 播放速度，暂停生成
3. **打断处理**: 收到 INTERRUPT 立即停止当前 TTS 生成
4. **会话管理**: 使用 SESSION_ID 关联整个对话流程

**伪代码示例**:

```python
async def handle_audio_data(frame: AudioFrame):
    # 立即送入 ASR（流式）
    asr_result = await asr_service.process_stream(frame.pcm_data)

    if asr_result.is_complete:
        # ASR 完成，送入 Agent
        agent_response = await agent_service.process(asr_result.text)

        # 流式 TTS
        async for tts_chunk in tts_service.synthesize_stream(agent_response):
            await send_audio_chunk(tts_chunk)
```

## 六、版本管理

### 6.1 协议版本

- **当前版本**: v1.0
- **版本号格式**: 4 bytes (major.minor.patch.build)
- **兼容性**: 向后兼容（旧版本客户端可以连接新版本服务端）

### 6.2 版本协商

在 DEVICE_INFO 帧中携带协议版本，服务端检查兼容性：

- 如果版本不兼容，返回 ERROR (0x0001)
- 如果版本兼容，继续处理

## 七、安全考虑

### 7.1 认证（可选）

如果需要在生产环境添加认证：

**DEVICE_INFO 扩展**:

```
┌──────────┬──────────────┬──────────────┬──────────────┐
│  VERSION │  DEVICE_ID   │   FEATURES   │   AUTH_TOKEN │
│  (4B)    │  (32B)       │    (1B)      │   (32B)      │
└──────────┴──────────────┴──────────────┴──────────────┘
```

### 7.2 加密（可选）

如果需要加密传输：

- 使用 TLS/SSL（TCP over TLS）
- 或应用层加密（AES-256）

## 八、调试与测试

### 8.1 日志格式

建议在帧头添加可选的调试信息（仅开发环境）:

```
┌──────────┬──────────┬──────────────┬──────────────┐
│   TYPE   │   LEN    │  DEBUG_FLAG  │   PAYLOAD    │
│  (1B)    │   (2B)   │    (1B)      │  (变长)      │
└──────────┴──────────┴──────────────┴──────────────┘
```

DEBUG_FLAG (仅开发环境):

- Bit 0: 是否包含调试信息
- Bit 1-7: 保留

### 8.2 测试工具

建议开发以下测试工具：

1. **协议解析器**: 解析二进制帧，输出可读格式
2. **模拟器**: PC 端模拟 MCU 行为
3. **抓包工具**: 记录和分析协议流量

---

**文档版本**: v1.0  
**最后更新**: 2025-01-22  
**维护者**: Yanshu Team
