# Yanshu - 语音助手项目

Yanshu 是一个基于 AI Agent 的语音助手系统，采用**瘦客户端 + 智能服务端**架构，支持边缘设备本地部署。

## 项目概述

Yanshu 将语音助手拆分为两个部分：

- **MCU 终端**：纯语音 I/O 设备，负责音频采集、播放和用户交互
- **服务端**：所有智能逻辑（ASR、Agent、LLM、TTS、会话管理）在服务端完成

这种架构设计使得：

- MCU 端实现简单，功耗低，成本可控
- 服务端可以快速迭代和升级 AI 能力
- 支持边缘设备本地部署，保护隐私

## 项目结构

```
yanshu/
├── agent/              # Agent 核心代码
│   └── yanshu.py      # Agno Agent 定义
├── doc/               # 文档目录
│   ├── plan/         # 规划文档
│   ├── architecture.md  # 架构设计文档
│   └── protocol.md   # 通信协议规范
├── docker-compose/    # Docker 部署配置
├── main.py           # 主程序入口
├── pyproject.toml    # Python 项目配置
└── README.md         # 本文件
```

## 核心文档

- **[架构设计文档](doc/architecture.md)** - 完整的系统架构、技术选型、部署方案
- **[通信协议规范](doc/protocol.md)** - 详细的二进制协议定义和实现指南

## 技术栈

### MCU 终端

- **硬件**: ESP32-S3
- **语言**: Rust (no_std)
- **功能**: 音频 I/O、状态机、协议处理

### 服务端

- **语言**: Python
- **Agent 框架**: [Agno](https://github.com/agno-ai/agno)
- **ASR**: faster-whisper
- **TTS**: OpenAI TTS / Azure TTS
- **部署**: Docker + Docker Compose

## ⚠️ 安全提示

**重要**：本项目不再使用硬编码的 API keys。请按照以下步骤配置：

```bash
# 进入 agent 目录
cd agent

# 创建配置文件
cp config.yaml.example config.yaml

# 编辑 config.yaml，填入你的 API key
vi config.yaml
```

详见：[docs/CONFIG_GUIDE.md](docs/CONFIG_GUIDE.md) 和 [docs/SECURITY.md](docs/SECURITY.md)

## 快速开始

### 开发环境

1. **配置 Agent**:

```bash
cd agent
cp config.yaml.example config.yaml
# 编辑 config.yaml，填入 API key
```

2. **安装依赖**:

```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -e .
```

2. **运行 Agent 服务**:

```bash
python main.py
```

### 部署

使用 Docker Compose 部署完整服务栈：

```bash
cd docker-compose
docker-compose up -d
```

## 开发路线图

### Phase 1: MVP (2-3 周)

- [ ] MCU 端：音频采集 + TCP 连接
- [ ] 服务端：协议网关 + ASR (Whisper)
- [ ] 服务端：Agent 集成 (Agno)
- [ ] 服务端：TTS (OpenAI TTS)
- [ ] 基础状态机（MCU）
- [ ] PC 端模拟器（测试用）

### Phase 2: 完善功能 (2-3 周)

- [ ] 打断功能（barge-in）
- [ ] 会话管理（Redis）
- [ ] 错误处理与重连
- [ ] 心跳机制
- [ ] 性能优化（延迟优化）

### Phase 3: 生产就绪 (2-3 周)

- [ ] 部署方案（Docker Compose）
- [ ] 监控与日志
- [ ] 固件 OTA 升级
- [ ] 压力测试
- [ ] 文档完善

## 性能指标

| 阶段           | 目标延迟 |
| -------------- | -------- |
| ASR 首字       | < 300ms  |
| Agent 首 token | < 500ms  |
| TTS 首帧       | < 300ms  |
| 端到端         | < 1.5s   |

## 贡献指南

欢迎贡献代码、文档或提出建议！

## 许可证

[待定]

---

**项目状态**: 🚧 开发中  
**最后更新**: 2025-01-22
