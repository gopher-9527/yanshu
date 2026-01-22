package llmmodel

import (
	"context"
	"fmt"
	"iter"
	"time"

	"github.com/gopher-9527/yanshu/agent/pkg/llmmodel/openai_compatible"
	"google.golang.org/adk/model"
)

// OpenAIModel implements the model.LLM interface for OpenAI API
type OpenAIModel struct {
	client *openai_compatible.Client
}

// OpenAIConfig holds configuration for OpenAI model
type OpenAIConfig struct {
	APIKey    string
	BaseURL   string        // Optional, defaults to https://api.openai.com
	ModelName string        // Required, e.g., "gpt-4", "gpt-3.5-turbo"
	Timeout   time.Duration // Optional, defaults to 5 minutes
}

// NewOpenAIModel creates a new OpenAI model instance
func NewOpenAIModel(ctx context.Context, cfg *OpenAIConfig) (model.LLM, error) {
	if cfg == nil {
		return nil, fmt.Errorf("config cannot be nil")
	}
	if cfg.APIKey == "" {
		return nil, fmt.Errorf("API key is required")
	}
	if cfg.ModelName == "" {
		return nil, fmt.Errorf("model name is required")
	}

	baseURL := cfg.BaseURL
	if baseURL == "" {
		baseURL = "https://api.openai.com"
	}

	client, err := openai_compatible.NewClient(&openai_compatible.ClientConfig{
		APIKey:    cfg.APIKey,
		BaseURL:   baseURL,
		ModelName: cfg.ModelName,
		Timeout:   cfg.Timeout,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create client: %w", err)
	}

	return &OpenAIModel{
		client: client,
	}, nil
}

// Name returns the model name
func (m *OpenAIModel) Name() string {
	return m.client.ModelName()
}

// GenerateContent implements the model.LLM interface
func (m *OpenAIModel) GenerateContent(ctx context.Context, req *model.LLMRequest, stream bool) iter.Seq2[*model.LLMResponse, error] {
	return m.client.GenerateContent(ctx, req, stream)
}
