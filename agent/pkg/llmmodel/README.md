# LLM Model Implementations

This package provides LLM model implementations that implement the `model.LLM` interface from Google ADK, allowing you to use various LLM providers with the Agent Development Kit.

## Available Models

- **DeepSeek**: DeepSeek API integration
- **OpenAI**: OpenAI API integration
- **OpenAI Compatible**: Generic client for any OpenAI-compatible API

All models are built on top of a shared `openai_compatible` client, making it easy to add support for new providers.

## Features

- ✅ OpenAI-compatible API integration
- ✅ Streaming and non-streaming support
- ✅ Full compatibility with ADK's `model.LLM` interface
- ✅ Support for both `deepseek-chat` and `deepseek-reasoner` models
- ✅ Tool calling support (basic)

## Usage

### DeepSeek Example

```go
package main

import (
    "context"
    "os"
    
    "github.com/gopher-9527/yanshu/agent/pkg/llmmodel"
    "google.golang.org/adk/agent/llmagent"
)

func main() {
    ctx := context.Background()
    
    // Create DeepSeek model
    model, err := llmmodel.NewModel(ctx, &llmmodel.Config{
        APIKey:    os.Getenv("DEEPSEEK_API_KEY"),
        ModelName: "deepseek-chat", // or "deepseek-reasoner"
    })
    if err != nil {
        log.Fatalf("Failed to create model: %v", err)
    }
    
    // Create agent with DeepSeek model
    agent, err := llmagent.New(llmagent.Config{
        Name:        "yanshu_agent",
        Model:       model,
        Description: "A helpful assistant powered by DeepSeek",
        Instruction: "You are a helpful assistant.",
    })
    if err != nil {
        log.Fatalf("Failed to create agent: %v", err)
    }
    
    // Use the agent...
}
```

### OpenAI Example

```go
// Create OpenAI model
model, err := llmmodel.NewOpenAIModel(ctx, &llmmodel.OpenAIConfig{
    APIKey:    os.Getenv("OPENAI_API_KEY"),
    ModelName: "gpt-4",
})
```

### Using OpenAI-Compatible Client Directly

For custom providers or local models:

```go
import "github.com/gopher-9527/yanshu/agent/pkg/llmmodel/openai_compatible"

client, err := openai_compatible.NewClient(&openai_compatible.ClientConfig{
    APIKey:    "your-api-key",
    BaseURL:   "https://api.example.com",  // Your provider's base URL
    ModelName: "model-name",
})
```

### Configuration

The `Config` struct supports the following options:

- **APIKey** (required): Your DeepSeek API key
- **BaseURL** (optional): API base URL, defaults to `https://api.deepseek.com`
- **ModelName** (optional): Model name, defaults to `deepseek-chat`

### Available Models

- `deepseek-chat`: General-purpose model (non-thinking mode)
- `deepseek-reasoner`: Reasoning-focused model (thinking mode)

Both models are currently upgraded to DeepSeek-V3.2.

## API Compatibility

DeepSeek uses an OpenAI-compatible API, so this implementation:

- Converts ADK's `genai.Content` format to OpenAI message format
- Handles streaming responses (SSE format)
- Supports temperature, max_tokens, and other common parameters
- Provides basic tool calling support

## Environment Setup

1. Get your API key from [platform.deepseek.com](https://platform.deepseek.com)
2. Set the environment variable:
   ```bash
   export DEEPSEEK_API_KEY="your-api-key-here"
   ```

## Implementation Details

- **Protocol**: HTTP REST API (OpenAI-compatible)
- **Streaming**: Server-Sent Events (SSE)
- **Error Handling**: Comprehensive error handling with detailed messages
- **Type Conversion**: Automatic conversion between ADK types and OpenAI format

## Limitations

- Tool calling conversion is basic and may need extension for complex tools
- Some advanced ADK features may not be fully supported
- Rate limiting and retry logic should be handled at the application level

## See Also

- [DeepSeek API Documentation](https://api-docs.deepseek.com/)
- [Google ADK Documentation](https://google.github.io/adk-docs/)
