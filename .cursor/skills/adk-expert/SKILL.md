---
name: adk-expert
description: Expert guidance on using Google ADK (Agent Development Kit) for Go. Use when working with ADK agents, implementing LLM models, creating agents with llmagent, using launcher, or when the user mentions ADK, agent development, model.LLM interface, or Google Agent Development Kit.
---

# Google ADK (Go) Expert Guide

Expert knowledge for building agents with Google Agent Development Kit (ADK) in Go.

## Core Concepts

### Agent Architecture

ADK agents follow this pattern:

1. **Model**: Implements `model.LLM` interface
2. **Agent**: Created with `llmagent.New()`
3. **Launcher**: Runs the agent with `launcher.Execute()`

### Key Packages

```go
import (
    "google.golang.org/adk/agent"
    "google.golang.org/adk/agent/llmagent"
    "google.golang.org/adk/cmd/launcher"
    "google.golang.org/adk/cmd/launcher/full"
    "google.golang.org/adk/model"
)
```

## Creating an Agent

### Basic Agent Setup

```go
package main

import (
    "context"
    "log"
    "os"

    "google.golang.org/adk/agent"
    "google.golang.org/adk/agent/llmagent"
    "google.golang.org/adk/cmd/launcher"
    "google.golang.org/adk/cmd/launcher/full"
)

func main() {
    ctx := context.Background()
    
    // 1. Create model (implements model.LLM interface)
    model, err := createModel(ctx)
    if err != nil {
        log.Fatalf("Failed to create model: %v", err)
    }
    
    // 2. Create agent
    agent, err := llmagent.New(llmagent.Config{
        Name:        "my_agent",
        Model:       model,
        Description: "Agent description",
        Instruction: "You are a helpful assistant.",
    })
    if err != nil {
        log.Fatalf("Failed to create agent: %v", err)
    }
    
    // 3. Setup launcher
    config := &launcher.Config{
        AgentLoader: agent.NewSingleLoader(agent),
    }
    
    // 4. Run agent
    l := full.NewLauncher()
    if err = l.Execute(ctx, config, os.Args[1:]); err != nil {
        log.Fatalf("Run failed: %v\n\n%s", err, l.CommandLineSyntax())
    }
}
```

## Implementing model.LLM Interface

### Interface Definition

```go
type LLM interface {
    Name() string
    GenerateContent(ctx context.Context, req *LLMRequest, stream bool) iter.Seq2[*LLMResponse, error]
}
```

### Example Implementation

```go
type MyModel struct {
    client *httpClient
    modelName string
}

func (m *MyModel) Name() string {
    return m.modelName
}

func (m *MyModel) GenerateContent(
    ctx context.Context,
    req *model.LLMRequest,
    stream bool,
) iter.Seq2[*model.LLMResponse, error] {
    return func(yield func(*model.LLMResponse, error) bool) {
        // Implementation here
        // For streaming: yield responses as they arrive
        // For non-streaming: yield single final response
    }
}
```

## LLMRequest Structure

Key fields in `model.LLMRequest`:

- `Contents []*genai.Content` - Message history
- `Tools []*genai.Tool` - Available tools for function calling
- `Config *model.LLMConfig` - Generation parameters
  - `Temperature` - Sampling temperature
  - `MaxOutputTokens` - Maximum tokens to generate
  - `TopP` - Nucleus sampling
  - `TopK` - Top-k sampling

## LLMResponse Structure

Key fields in `model.LLMResponse`:

- `Candidates []*genai.Candidate` - Generated responses
- `Usage *genai.UsageMetadata` - Token usage statistics
- `Model` - Model identifier

## Streaming Support

### Streaming Pattern

```go
func (m *MyModel) GenerateContent(
    ctx context.Context,
    req *model.LLMRequest,
    stream bool,
) iter.Seq2[*model.LLMResponse, error] {
    return func(yield func(*model.LLMResponse, error) bool) {
        if stream {
            // Stream responses
            for chunk := range streamChunks {
                resp := &model.LLMResponse{
                    Candidates: []*genai.Candidate{{
                        Content: &genai.Content{
                            Parts: []*genai.Part{{
                                Text: chunk.Text,
                            }},
                        },
                    }},
                }
                if !yield(resp, nil) {
                    return
                }
            }
        } else {
            // Single response
            resp := buildCompleteResponse()
            yield(resp, nil)
        }
    }
}
```

## Content Format Conversion

### Converting genai.Content to Provider Format

Common pattern for OpenAI-compatible APIs:

```go
func convertContentToMessages(contents []*genai.Content) []Message {
    messages := make([]Message, 0, len(contents))
    for _, content := range contents {
        msg := Message{
            Role:    convertRole(content.Role),
            Content: extractText(content),
        }
        messages = append(messages, msg)
    }
    return messages
}
```

## Tool Calling Support

### Converting ADK Tools to Provider Format

```go
func convertToolsToProviderFormat(tools []*genai.Tool) []Tool {
    providerTools := make([]Tool, 0, len(tools))
    for _, tool := range tools {
        providerTool := Tool{
            Type: "function",
            Function: Function{
                Name:        tool.FunctionDecl.Name,
                Description: tool.FunctionDecl.Description,
                Parameters:  convertSchema(tool.FunctionDecl.Parameters),
            },
        }
        providerTools = append(providerTools, providerTool)
    }
    return providerTools
}
```

## Error Handling

### Best Practices

1. **Wrap errors with context**:
   ```go
   if err != nil {
       return nil, fmt.Errorf("failed to create client: %w", err)
   }
   ```

2. **Handle HTTP errors**:
   ```go
   if resp.StatusCode != http.StatusOK {
       body, _ := io.ReadAll(resp.Body)
       return fmt.Errorf("API error: %s", string(body))
   }
   ```

3. **Context cancellation**:
   ```go
   select {
   case <-ctx.Done():
       return ctx.Err()
   default:
       // Continue
   }
   ```

## Common Patterns

### OpenAI-Compatible Client

For providers with OpenAI-compatible APIs:

1. Use standard HTTP client
2. Convert `genai.Content` to OpenAI message format
3. Parse SSE (Server-Sent Events) for streaming
4. Handle tool calling format conversion

### Model Configuration

```go
type Config struct {
    APIKey    string
    BaseURL   string
    ModelName string
}
```

## Launcher Options

### Full Launcher

```go
l := full.NewLauncher()
// Supports web UI, CLI, API server
```

### Custom Launcher

Implement `launcher.Launcher` interface for custom execution.

## Testing Agents

### Unit Testing Model

```go
func TestModel(t *testing.T) {
    model := &MyModel{...}
    
    req := &model.LLMRequest{
        Contents: []*genai.Content{{
            Role: "user",
            Parts: []*genai.Part{{
                Text: "Hello",
            }},
        }},
    }
    
    for resp, err := range model.GenerateContent(ctx, req, false) {
        // Assert response
    }
}
```

## Best Practices

1. **Always implement streaming**: Even if provider doesn't support it, yield single response
2. **Handle context cancellation**: Check `ctx.Done()` in loops
3. **Convert types properly**: Use converter functions for content/tool conversion
4. **Error wrapping**: Use `fmt.Errorf` with `%w` verb
5. **Resource cleanup**: Close HTTP connections, cancel contexts

## Additional Resources

- [ADK Documentation](https://google.github.io/adk-docs/)
- [ADK Go Package](https://pkg.go.dev/google.golang.org/adk)
- [genai Package](https://pkg.go.dev/google.golang.org/genai)
