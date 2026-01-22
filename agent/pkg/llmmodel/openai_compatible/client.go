package openai_compatible

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"strings"
	"time"

	"google.golang.org/adk/model"
	"google.golang.org/genai"
)

// APIError represents an error returned by the API
type APIError struct {
	StatusCode int
	Message    string
	Type       string
	Body       string
}

func (e *APIError) Error() string {
	if e.Message != "" {
		return fmt.Sprintf("API error %d: %s", e.StatusCode, e.Message)
	}
	return fmt.Sprintf("API error %d: %s", e.StatusCode, e.Body)
}

// ClientConfig holds configuration for OpenAI-compatible API client
type ClientConfig struct {
	APIKey     string
	BaseURL    string
	ModelName  string
	HTTPClient *http.Client
	Timeout    time.Duration // Request timeout, defaults to 5 minutes
	Logger     *slog.Logger
}

// Client handles requests to OpenAI-compatible APIs
type Client struct {
	apiKey     string
	baseURL    string
	modelName  string
	httpClient *http.Client
	logger     *slog.Logger
}

// NewClient creates a new OpenAI-compatible API client
func NewClient(cfg *ClientConfig) (*Client, error) {
	if cfg == nil {
		return nil, fmt.Errorf("config cannot be nil")
	}
	if cfg.APIKey == "" {
		return nil, fmt.Errorf("API key is required")
	}
	if cfg.BaseURL == "" {
		return nil, fmt.Errorf("base URL is required")
	}
	if cfg.ModelName == "" {
		return nil, fmt.Errorf("model name is required")
	}

	// Setup logger
	logger := cfg.Logger
	if logger == nil {
		// Use the default global logger, which inherits the level set by the application
		// This allows DEBUG logs to be printed when the application sets slog.SetDefault()
		logger = slog.Default()
	}

	// Setup HTTP client
	httpClient := cfg.HTTPClient
	if httpClient == nil {
		timeout := cfg.Timeout
		if timeout == 0 {
			timeout = 5 * time.Minute // Default 5 minutes for LLM requests
		}

		httpClient = &http.Client{
			Timeout: timeout,
			Transport: &http.Transport{
				MaxIdleConns:        100,
				MaxIdleConnsPerHost: 10,
				IdleConnTimeout:     90 * time.Second,
			},
		}
	}

	client := &Client{
		apiKey:     cfg.APIKey,
		baseURL:    cfg.BaseURL,
		modelName:  cfg.ModelName,
		httpClient: httpClient,
		logger:     logger,
	}

	client.logger.Info("OpenAI-compatible client created",
		"baseURL", cfg.BaseURL,
		"model", cfg.ModelName,
		"timeout", httpClient.Timeout,
	)

	return client, nil
}

// ModelName returns the model name
func (c *Client) ModelName() string {
	return c.modelName
}

// GenerateContent handles both streaming and non-streaming requests
func (c *Client) GenerateContent(ctx context.Context, req *model.LLMRequest, stream bool) func(func(*model.LLMResponse, error) bool) {
	return func(yield func(*model.LLMResponse, error) bool) {
		if stream {
			c.generateContentStream(ctx, req, yield)
		} else {
			c.generateContentNonStream(ctx, req, yield)
		}
	}
}

// buildRequest builds an HTTP request for the OpenAI API
func (c *Client) buildRequest(ctx context.Context, req *model.LLMRequest, stream bool) (*http.Request, error) {
	c.logger.Debug("Building request",
		"stream", stream,
		"model", c.modelName,
		"contents_count", len(req.Contents),
	)

	// Convert genai.Content to OpenAI format
	messages, err := ConvertContentsToMessages(req.Contents)
	if err != nil {
		c.logger.Error("Failed to convert contents", "error", err)
		return nil, fmt.Errorf("failed to convert contents: %w", err)
	}

	c.logger.Debug("Converted messages", "count", len(messages))

	// Build OpenAI-compatible request
	openAIReq := map[string]any{
		"model":    c.modelName,
		"messages": messages,
		"stream":   stream,
	}

	// Add temperature if specified
	if req.Config != nil && req.Config.Temperature != nil {
		openAIReq["temperature"] = *req.Config.Temperature
		c.logger.Debug("Added temperature", "value", *req.Config.Temperature)
	}

	// Add max_tokens if specified
	if req.Config != nil && req.Config.MaxOutputTokens > 0 {
		openAIReq["max_tokens"] = req.Config.MaxOutputTokens
		c.logger.Debug("Added max_tokens", "value", req.Config.MaxOutputTokens)
	}

	// Add tools if specified
	if req.Tools != nil && len(req.Tools) > 0 {
		tools, err := ConvertToolsToOpenAIFormat(req.Tools)
		if err != nil {
			c.logger.Error("Failed to convert tools", "error", err)
			return nil, fmt.Errorf("failed to convert tools: %w", err)
		}
		openAIReq["tools"] = tools
		c.logger.Debug("Added tools", "count", len(tools))
	}

	// Marshal request body
	reqBody, err := json.Marshal(openAIReq)
	if err != nil {
		c.logger.Error("Failed to marshal request", "error", err)
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Create HTTP request
	url := c.baseURL + "/v1/chat/completions"
	httpReq, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(reqBody))
	if err != nil {
		c.logger.Error("Failed to create HTTP request", "error", err, "url", url)
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+c.apiKey) // Log only prefix

	c.logger.Info("Request built successfully",
		"url", url,
		"stream", stream,
		"body_size", len(reqBody),
	)

	return httpReq, nil
}

// handleHTTPError parses and returns a detailed API error
func (c *Client) handleHTTPError(resp *http.Response) error {
	body, _ := io.ReadAll(resp.Body)

	var errResp struct {
		Error struct {
			Message string `json:"message"`
			Type    string `json:"type"`
			Code    string `json:"code"`
		} `json:"error"`
	}

	if err := json.Unmarshal(body, &errResp); err == nil && errResp.Error.Message != "" {
		return &APIError{
			StatusCode: resp.StatusCode,
			Message:    errResp.Error.Message,
			Type:       errResp.Error.Type,
			Body:       string(body),
		}
	}

	return &APIError{
		StatusCode: resp.StatusCode,
		Body:       string(body),
	}
}

// generateContentNonStream handles non-streaming requests
func (c *Client) generateContentNonStream(ctx context.Context, req *model.LLMRequest, yield func(*model.LLMResponse, error) bool) {
	c.logger.Info("Starting non-streaming request")

	// Build HTTP request
	httpReq, err := c.buildRequest(ctx, req, false)
	if err != nil {
		c.logger.Error("Failed to build request", "error", err)
		yield(nil, err)
		return
	}

	// Make HTTP request
	c.logger.Info("Sending HTTP request", "url", httpReq.URL.String())
	startTime := time.Now()

	resp, err := c.httpClient.Do(httpReq)
	elapsed := time.Since(startTime)

	if err != nil {
		c.logger.Error("HTTP request failed",
			"error", err,
			"elapsed", elapsed,
		)
		yield(nil, fmt.Errorf("failed to make request: %w", err))
		return
	}
	defer resp.Body.Close()

	c.logger.Info("Received HTTP response",
		"status", resp.StatusCode,
		"elapsed", elapsed,
	)

	if resp.StatusCode != http.StatusOK {
		err := c.handleHTTPError(resp)
		c.logger.Error("API returned error", "error", err)
		yield(nil, err)
		return
	}

	// Parse OpenAI response
	var openAIResp struct {
		ID      string `json:"id"`
		Choices []struct {
			Message struct {
				Role    string `json:"role"`
				Content string `json:"content"`
			} `json:"message"`
			FinishReason string `json:"finish_reason"`
		} `json:"choices"`
		Usage struct {
			PromptTokens     int `json:"prompt_tokens"`
			CompletionTokens int `json:"completion_tokens"`
			TotalTokens      int `json:"total_tokens"`
		} `json:"usage"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&openAIResp); err != nil {
		c.logger.Error("Failed to decode response", "error", err)
		yield(nil, fmt.Errorf("failed to decode response: %w", err))
		return
	}

	c.logger.Info("Parsed response",
		"id", openAIResp.ID,
		"choices", len(openAIResp.Choices),
		"prompt_tokens", openAIResp.Usage.PromptTokens,
		"completion_tokens", openAIResp.Usage.CompletionTokens,
	)

	// Convert to genai format
	if len(openAIResp.Choices) > 0 {
		choice := openAIResp.Choices[0]
		content := genai.NewContentFromText(choice.Message.Content, genai.RoleModel)
		llmResp := &model.LLMResponse{
			Content: content,
			UsageMetadata: &genai.GenerateContentResponseUsageMetadata{
				PromptTokenCount:     int32(openAIResp.Usage.PromptTokens),
				CandidatesTokenCount: int32(openAIResp.Usage.CompletionTokens),
				TotalTokenCount:      int32(openAIResp.Usage.TotalTokens),
			},
			TurnComplete: true,
		}

		if choice.FinishReason != "" {
			llmResp.FinishReason = genai.FinishReason(choice.FinishReason)
		}

		c.logger.Info("Yielding response",
			"content_length", len(choice.Message.Content),
			"finish_reason", choice.FinishReason,
		)

		yield(llmResp, nil)
	} else {
		c.logger.Warn("No choices in response")
	}
}

// generateContentStream handles streaming requests
func (c *Client) generateContentStream(ctx context.Context, req *model.LLMRequest, yield func(*model.LLMResponse, error) bool) {
	c.logger.Info("Starting streaming request")

	// Build HTTP request
	httpReq, err := c.buildRequest(ctx, req, true)
	if err != nil {
		c.logger.Error("Failed to build request", "error", err)
		yield(nil, err)
		return
	}

	// Make HTTP request
	c.logger.Info("Sending streaming HTTP request", "url", httpReq.URL.String())
	startTime := time.Now()

	resp, err := c.httpClient.Do(httpReq)
	elapsed := time.Since(startTime)

	if err != nil {
		c.logger.Error("Streaming HTTP request failed",
			"error", err,
			"elapsed", elapsed,
		)
		yield(nil, fmt.Errorf("failed to make request: %w", err))
		return
	}
	defer resp.Body.Close()

	c.logger.Info("Received streaming HTTP response",
		"status", resp.StatusCode,
		"elapsed", elapsed,
	)

	if resp.StatusCode != http.StatusOK {
		err := c.handleHTTPError(resp)
		c.logger.Error("Streaming API returned error", "error", err)
		yield(nil, err)
		return
	}

	// Parse streaming response (SSE format)
	c.logger.Info("Starting to parse streaming response")
	scanner := bufio.NewScanner(resp.Body)
	var accumulatedContent strings.Builder
	accumulatedContent.Grow(1024) // Pre-allocate capacity

	chunkCount := 0
	firstChunkTime := time.Time{}

	for scanner.Scan() {
		// Check context cancellation
		select {
		case <-ctx.Done():
			c.logger.Warn("Context cancelled during streaming", "chunks_received", chunkCount)
			yield(nil, ctx.Err())
			return
		default:
		}

		line := scanner.Text()
		if line == "" {
			continue
		}

		// SSE format: "data: {...}" or "[DONE]"
		if !strings.HasPrefix(line, "data: ") {
			continue
		}

		data := strings.TrimPrefix(line, "data: ")
		if data == "[DONE]" {
			c.logger.Info("Stream completed with [DONE]",
				"chunks_received", chunkCount,
				"total_content_length", accumulatedContent.Len(),
			)

			// Send final response
			if accumulatedContent.Len() > 0 {
				content := genai.NewContentFromText(accumulatedContent.String(), genai.RoleModel)
				llmResp := &model.LLMResponse{
					Content:      content,
					TurnComplete: true,
				}
				if !yield(llmResp, nil) {
					return
				}
			}
			break
		}

		var streamChunk struct {
			ID      string `json:"id"`
			Choices []struct {
				Delta struct {
					Role    string `json:"role"`
					Content string `json:"content"`
				} `json:"delta"`
				FinishReason string `json:"finish_reason"`
			} `json:"choices"`
		}

		if err := json.Unmarshal([]byte(data), &streamChunk); err != nil {
			c.logger.Warn("Failed to parse stream chunk, skipping", "error", err, "data", data[:min(len(data), 100)])
			continue
		}

		if len(streamChunk.Choices) > 0 {
			choice := streamChunk.Choices[0]
			if choice.Delta.Content != "" {
				chunkCount++
				if firstChunkTime.IsZero() {
					firstChunkTime = time.Now()
					c.logger.Info("First chunk received", "time_to_first_chunk", time.Since(startTime))
				}

				accumulatedContent.WriteString(choice.Delta.Content)
				content := genai.NewContentFromText(choice.Delta.Content, genai.RoleModel)
				llmResp := &model.LLMResponse{
					Content: content,
					Partial: true,
				}

				if chunkCount%10 == 0 {
					c.logger.Debug("Streaming progress",
						"chunks", chunkCount,
						"accumulated_length", accumulatedContent.Len(),
					)
				}

				if !yield(llmResp, nil) {
					c.logger.Info("Yield returned false, stopping stream", "chunks_sent", chunkCount)
					return
				}
			}

			if choice.FinishReason != "" {
				c.logger.Info("Stream finished",
					"reason", choice.FinishReason,
					"chunks_received", chunkCount,
					"total_content_length", accumulatedContent.Len(),
				)

				// Send final response with accumulated content
				content := genai.NewContentFromText(accumulatedContent.String(), genai.RoleModel)
				llmResp := &model.LLMResponse{
					Content:      content,
					FinishReason: genai.FinishReason(choice.FinishReason),
					TurnComplete: true,
				}
				if !yield(llmResp, nil) {
					return
				}
				break
			}
		}
	}

	if err := scanner.Err(); err != nil {
		c.logger.Error("Scanner error during streaming", "error", err, "chunks_received", chunkCount)
		yield(nil, fmt.Errorf("failed to read stream: %w", err))
		return
	}

	c.logger.Info("Streaming completed successfully", "total_chunks", chunkCount)
}
