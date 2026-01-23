package main

import (
	"context"
	"log"
	"log/slog"
	"os"

	"github.com/gopher-9527/yanshu/agent/pkg/config"
	"github.com/gopher-9527/yanshu/agent/pkg/llmmodel"
	"google.golang.org/adk/agent"
	"google.golang.org/adk/agent/llmagent"
	"google.golang.org/adk/cmd/launcher"
	"google.golang.org/adk/cmd/launcher/full"
)

func main() {
	// Load configuration from default location or environment variable
	configPath := os.Getenv("CONFIG_PATH")
	if configPath == "" {
		configPath = "config.yaml"
	}

	// Load configuration
	cfg, err := config.Load(configPath)
	if err != nil {
		log.Fatalf("Failed to load config: %v\n\nPlease create config.yaml from config.yaml.example\nOr set CONFIG_PATH environment variable", err)
	}

	// Setup logger based on config
	logLevel := slog.LevelInfo
	switch cfg.Logging.GetLogLevel() {
	case "debug":
		logLevel = slog.LevelDebug
	case "warn":
		logLevel = slog.LevelWarn
	case "error":
		logLevel = slog.LevelError
	}

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level:     logLevel,
		AddSource: cfg.Logging.AddSource,
	}))
	slog.SetDefault(logger)

	ctx := context.Background()
	logger.Info("Starting agent application",
		"config_file", configPath,
		"log_level", cfg.Logging.Level,
	)

	// Get timeout duration
	timeout, err := cfg.Model.GetTimeout()
	if err != nil {
		log.Fatalf("Invalid timeout value: %v", err)
	}

	// Create model from config
	model, err := llmmodel.NewModel(ctx, &llmmodel.Config{
		APIKey:    cfg.Model.APIKey,
		ModelName: cfg.Model.ModelName,
		BaseURL:   cfg.Model.BaseURL,
		Timeout:   timeout,
	})
	if err != nil {
		log.Fatalf("Failed to create model: %v", err)
	}
	logger.Info("Model created successfully")

	// Create agent from config
	yanshu_agent, err := llmagent.New(llmagent.Config{
		Name:        cfg.Agent.Name,
		Model:       model,
		Description: cfg.Agent.Description,
		Instruction: cfg.Agent.Instruction,
	})
	if err != nil {
		log.Fatalf("Failed to create agent: %v", err)
	}
	logger.Info("Agent created successfully", "name", cfg.Agent.Name)

	launcherConfig := &launcher.Config{
		AgentLoader: agent.NewSingleLoader(yanshu_agent),
	}

	logger.Info("Starting launcher", "args", os.Args[1:])

	l := full.NewLauncher()
	if err = l.Execute(ctx, launcherConfig, os.Args[1:]); err != nil {
		log.Fatalf("Run failed: %v\n\n%s", err, l.CommandLineSyntax())
	}
}
