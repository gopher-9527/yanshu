需要实现的功能

1. agent，实现和LLM对话，处理不同事务的能力
2. server，业务实现，对接客户端，实现ASR、TTS、服务长连接等
3. client，实现具体和用户交互的逻辑，有web端和语音端

关键技术
语音转换：Whisper + Coqui TTS
agent： ADK
后端： go
client： react
终端： rust
agent核心模型：DeepSeek、qwen
