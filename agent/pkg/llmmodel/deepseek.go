package llmmodel

import (
	"context"
	"fmt"
	"iter"
	"time"

	"github.com/gopher-9527/yanshu/agent/pkg/llmmodel/openai_compatible"
	"google.golang.org/adk/model"
)

// DeepSeekModel implements the model.LLM interface for DeepSeek API
type DeepSeekModel struct {
	client *openai_compatible.Client
}

// Config holds configuration for DeepSeek model
type Config struct {
	APIKey    string
	BaseURL   string        // Optional, defaults to https://api.deepseek.com
	ModelName string        // Optional, defaults to deepseek-chat
	Timeout   time.Duration // Optional, defaults to 5 minutes
}

// NewModel creates a new DeepSeek model instance
func NewModel(ctx context.Context, cfg *Config) (model.LLM, error) {
	if cfg == nil {
		return nil, fmt.Errorf("config cannot be nil")
	}
	if cfg.APIKey == "" {
		return nil, fmt.Errorf("API key is required")
	}

	baseURL := cfg.BaseURL
	if baseURL == "" {
		baseURL = "https://api.deepseek.com"
	}

	modelName := cfg.ModelName
	if modelName == "" {
		modelName = "deepseek-chat"
	}

	client, err := openai_compatible.NewClient(&openai_compatible.ClientConfig{
		APIKey:    cfg.APIKey,
		BaseURL:   baseURL,
		ModelName: modelName,
		Timeout:   cfg.Timeout,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create client: %w", err)
	}

	return &DeepSeekModel{
		client: client,
	}, nil
}

// Name returns the model name
func (m *DeepSeekModel) Name() string {
	return m.client.ModelName()
}

// GenerateContent implements the model.LLM interface
func (m *DeepSeekModel) GenerateContent(ctx context.Context, req *model.LLMRequest, stream bool) iter.Seq2[*model.LLMResponse, error] {
	return m.client.GenerateContent(ctx, req, stream)
}
