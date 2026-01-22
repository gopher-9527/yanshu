package config

import (
	"fmt"
	"os"
	"time"

	"gopkg.in/yaml.v3"
)

// Config holds the application configuration
type Config struct {
	Model   ModelConfig   `yaml:"model"`
	Agent   AgentConfig   `yaml:"agent"`
	Logging LoggingConfig `yaml:"logging"`
	Server  ServerConfig  `yaml:"server"`
}

// ModelConfig holds LLM model configuration
type ModelConfig struct {
	APIKey    string `yaml:"api_key"`
	ModelName string `yaml:"model_name"`
	BaseURL   string `yaml:"base_url"`
	Timeout   string `yaml:"timeout"`
}

// AgentConfig holds agent configuration
type AgentConfig struct {
	Name        string `yaml:"name"`
	Description string `yaml:"description"`
	Instruction string `yaml:"instruction"`
}

// LoggingConfig holds logging configuration
type LoggingConfig struct {
	Level     string `yaml:"level"`
	AddSource bool   `yaml:"add_source"`
}

// ServerConfig holds server configuration
type ServerConfig struct {
	Port         int    `yaml:"port"`
	ReadTimeout  string `yaml:"read_timeout"`
	WriteTimeout string `yaml:"write_timeout"`
	IdleTimeout  string `yaml:"idle_timeout"`
}

// Load loads configuration from file or environment variables
func Load(configPath string) (*Config, error) {
	cfg := &Config{
		// Set defaults
		Model: ModelConfig{
			ModelName: "deepseek-chat",
			BaseURL:   "https://api.deepseek.com",
			Timeout:   "5m",
		},
		Agent: AgentConfig{
			Name:        "yanshu_agent",
			Description: "A helpful assistant",
			Instruction: "You are a helpful assistant.",
		},
		Logging: LoggingConfig{
			Level:     "info",
			AddSource: true,
		},
		Server: ServerConfig{
			Port:         8080,
			ReadTimeout:  "15s",
			WriteTimeout: "15s",
			IdleTimeout:  "60s",
		},
	}

	// Try to load from config file
	if configPath != "" {
		data, err := os.ReadFile(configPath)
		if err != nil {
			return nil, fmt.Errorf("failed to read config file: %w", err)
		}

		if err := yaml.Unmarshal(data, cfg); err != nil {
			return nil, fmt.Errorf("failed to parse config file: %w", err)
		}
	}

	// Override with environment variables if set
	if apiKey := os.Getenv("DEEPSEEK_API_KEY"); apiKey != "" {
		cfg.Model.APIKey = apiKey
	}
	if modelName := os.Getenv("MODEL_NAME"); modelName != "" {
		cfg.Model.ModelName = modelName
	}
	if baseURL := os.Getenv("MODEL_BASE_URL"); baseURL != "" {
		cfg.Model.BaseURL = baseURL
	}
	if logLevel := os.Getenv("LOG_LEVEL"); logLevel != "" {
		cfg.Logging.Level = logLevel
	}

	// Validate required fields
	if cfg.Model.APIKey == "" {
		return nil, fmt.Errorf("API key is required (set in config.yaml or DEEPSEEK_API_KEY env var)")
	}

	return cfg, nil
}

// GetTimeout parses the timeout string and returns a time.Duration
func (c *ModelConfig) GetTimeout() (time.Duration, error) {
	if c.Timeout == "" {
		return 5 * time.Minute, nil
	}
	return time.ParseDuration(c.Timeout)
}

// GetLogLevel parses the log level string
func (c *LoggingConfig) GetLogLevel() string {
	switch c.Level {
	case "debug", "info", "warn", "error":
		return c.Level
	default:
		return "info"
	}
}
