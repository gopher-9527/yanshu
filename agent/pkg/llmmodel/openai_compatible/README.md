# OpenAI Compatible Client

This package provides a generic client for OpenAI-compatible APIs, allowing easy integration of various LLM providers that follow the OpenAI API format.

## Supported Providers

Any LLM provider that implements the OpenAI-compatible API format can use this client:

- **DeepSeek** (`https://api.deepseek.com`)
- **OpenAI** (`https://api.openai.com`)
- **Anthropic** (via OpenAI-compatible proxy)
- **Local models** (via OpenAI-compatible servers like vLLM, Ollama, etc.)
- **Other OpenAI-compatible services**

## Architecture

```
┌─────────────────────────────────────────┐
│         Model Implementations           │
│  (DeepSeek, OpenAI, etc.)              │
└──────────────┬──────────────────────────┘
               │
               │ Uses
               ▼
┌─────────────────────────────────────────┐
│     openai_compatible.Client            │
│  - HTTP request handling                │
│  - Streaming support                    │
│  - Error handling                      │
└──────────────┬──────────────────────────┘
               │
               │ Uses
               ▼
┌─────────────────────────────────────────┐
│      Converter Functions               │
│  - ConvertContentsToMessages           │
│  - ConvertToolsToOpenAIFormat          │
└─────────────────────────────────────────┘
```

## Usage

### Direct Usage

```go
import "github.com/gopher-9527/yanshu/agent/pkg/llmmodel/openai_compatible"

client, err := openai_compatible.NewClient(&openai_compatible.ClientConfig{
    APIKey:    "your-api-key",
    BaseURL:   "https://api.example.com",
    ModelName: "model-name",
})

// Use client.GenerateContent() directly
```

### Through Model Wrappers

See `deepseek.go` and `openai.go` for examples of how to create model-specific wrappers.

## Features

- ✅ **Streaming Support**: Full SSE (Server-Sent Events) streaming support
- ✅ **Non-Streaming Support**: Traditional request/response mode
- ✅ **Tool Calling**: Basic tool calling support
- ✅ **Type Conversion**: Automatic conversion between ADK types and OpenAI format
- ✅ **Error Handling**: Comprehensive error handling

## API Compatibility

This client expects the following OpenAI-compatible endpoints:

- **POST** `/v1/chat/completions` - Main chat completion endpoint
- **Headers**:
  - `Content-Type: application/json`
  - `Authorization: Bearer <api-key>`
- **Request Format**: OpenAI chat completion format
- **Response Format**: OpenAI chat completion format (JSON or SSE)

## Extending for Custom Providers

To add support for a new OpenAI-compatible provider:

1. Create a new model file (e.g., `anthropic.go`)
2. Use `openai_compatible.NewClient()` with provider-specific config
3. Implement the `model.LLM` interface wrapper

Example:

```go
package llmmodel

import (
    "context"
    "github.com/gopher-9527/yanshu/agent/pkg/llmmodel/openai_compatible"
    "google.golang.org/adk/model"
)

type CustomModel struct {
    client *openai_compatible.Client
}

func NewCustomModel(ctx context.Context, cfg *CustomConfig) (model.LLM, error) {
    client, err := openai_compatible.NewClient(&openai_compatible.ClientConfig{
        APIKey:    cfg.APIKey,
        BaseURL:   cfg.BaseURL,
        ModelName: cfg.ModelName,
    })
    // ... rest of implementation
}
```
