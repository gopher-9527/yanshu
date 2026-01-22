# LLM Model Package Architecture

## 概述

本包将 LLM 请求逻辑抽离为通用能力，方便集成各种支持 OpenAI 兼容 API 的 LLM 提供商。

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│              Model Implementations                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  DeepSeek    │  │   OpenAI     │  │   Custom     │ │
│  │   Model      │  │    Model     │  │    Model     │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │          │
│         └──────────────────┴──────────────────┘          │
│                        │                                 │
│                        │ Uses                            │
│                        ▼                                 │
│         ┌───────────────────────────────┐               │
│         │  openai_compatible.Client     │               │
│         │  - HTTP request handling      │               │
│         │  - Streaming support         │               │
│         │  - Error handling            │               │
│         └───────────────┬───────────────┘               │
│                         │                                │
│                         │ Uses                           │
│                         ▼                                │
│         ┌───────────────────────────────┐               │
│         │    Converter Functions        │               │
│         │  - ConvertContentsToMessages   │               │
│         │  - ConvertToolsToOpenAIFormat │               │
│         └───────────────────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. openai_compatible 包

通用 OpenAI 兼容 API 客户端，包含：

- **Client**: 核心客户端，处理所有 HTTP 请求
- **Converter Functions**: 类型转换工具函数

#### Client (`client.go`)

负责：
- 创建和管理 HTTP 客户端
- 处理流式和非流式请求
- 错误处理和响应解析
- SSE (Server-Sent Events) 流式响应解析

#### Converter (`converter.go`)

提供：
- `ConvertContentsToMessages`: 将 `genai.Content` 转换为 OpenAI message 格式
- `ConvertToolsToOpenAIFormat`: 将 ADK tools 转换为 OpenAI tool 格式

### 2. Model 实现

每个 LLM 提供商只需要：

1. 定义配置结构体
2. 创建 `openai_compatible.Client` 实例
3. 实现 `model.LLM` 接口（通常只是简单的包装）

#### DeepSeek 示例

```go
type DeepSeekModel struct {
    client *openai_compatible.Client
}

func NewModel(ctx context.Context, cfg *Config) (model.LLM, error) {
    client, err := openai_compatible.NewClient(&openai_compatible.ClientConfig{
        APIKey:    cfg.APIKey,
        BaseURL:   "https://api.deepseek.com",
        ModelName: cfg.ModelName,
    })
    // ...
}
```

## 添加新的 LLM 提供商

### 步骤 1: 创建模型文件

创建新文件，如 `anthropic.go`:

```go
package llmmodel

import (
    "context"
    "fmt"
    "iter"
    
    "github.com/gopher-9527/yanshu/agent/pkg/llmmodel/openai_compatible"
    "google.golang.org/adk/model"
)

type AnthropicModel struct {
    client *openai_compatible.Client
}

type AnthropicConfig struct {
    APIKey    string
    BaseURL   string // Optional
    ModelName string // e.g., "claude-3-opus"
}

func NewAnthropicModel(ctx context.Context, cfg *AnthropicConfig) (model.LLM, error) {
    baseURL := cfg.BaseURL
    if baseURL == "" {
        baseURL = "https://api.anthropic.com" // 或通过 OpenAI 兼容代理
    }
    
    client, err := openai_compatible.NewClient(&openai_compatible.ClientConfig{
        APIKey:    cfg.APIKey,
        BaseURL:   baseURL,
        ModelName: cfg.ModelName,
    })
    if err != nil {
        return nil, fmt.Errorf("failed to create client: %w", err)
    }
    
    return &AnthropicModel{client: client}, nil
}

func (m *AnthropicModel) Name() string {
    return m.client.ModelName()
}

func (m *AnthropicModel) GenerateContent(ctx context.Context, req *model.LLMRequest, stream bool) iter.Seq2[*model.LLMResponse, error] {
    return m.client.GenerateContent(ctx, req, stream)
}
```

### 步骤 2: 更新文档

在 `README.md` 中添加新模型的说明。

## 优势

### 1. 代码复用

- 所有 OpenAI 兼容的 LLM 共享相同的请求处理逻辑
- 减少重复代码
- 统一的错误处理

### 2. 易于扩展

- 添加新提供商只需少量代码
- 无需重复实现 HTTP 请求、流式处理等

### 3. 统一接口

- 所有模型都实现 `model.LLM` 接口
- 可以在不同模型间无缝切换

### 4. 维护性

- 核心逻辑集中在一个地方
- Bug 修复和功能增强只需修改一处

## 支持的 API 特性

- ✅ 流式响应 (SSE)
- ✅ 非流式响应
- ✅ 温度参数
- ✅ 最大 tokens
- ✅ 工具调用（基础支持）
- ✅ 多轮对话
- ✅ 系统消息

## 未来扩展

可以考虑添加：

1. **重试机制**: 在 `openai_compatible.Client` 中添加自动重试
2. **速率限制**: 实现速率限制和退避策略
3. **请求日志**: 添加请求/响应日志记录
4. **指标收集**: 收集延迟、错误率等指标
5. **连接池**: HTTP 连接池优化
6. **工具调用增强**: 更完善的工具调用支持

## 文件结构

```
pkg/llmmodel/
├── deepseek.go              # DeepSeek 模型实现
├── openai.go                # OpenAI 模型实现
├── README.md                # 包文档
├── ARCHITECTURE.md          # 架构文档（本文件）
└── openai_compatible/       # 通用客户端
    ├── client.go            # 核心客户端
    ├── converter.go         # 类型转换
    └── README.md            # 客户端文档
```
