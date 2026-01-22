# Yanshu Agent

Google ADK-based agent for the Yanshu voice assistant project.

## Quick Start

### 1. Setup Configuration

Create configuration file from template:

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` and fill in your actual API key:

```yaml
model:
  api_key: "your-api-key-here"  # ← Change this
```

### 2. Run the Agent

```bash
make run-agent
# or
go run cmd/agent.go web api webui
```

### 3. Access Web UI

Open browser: http://localhost:8080/ui/

## Configuration

See [../docs/CONFIG_GUIDE.md](../docs/CONFIG_GUIDE.md) for detailed configuration options.

### Environment Variables (Alternative)

```bash
export DEEPSEEK_API_KEY="your-api-key"
export MODEL_NAME="deepseek/deepseek-v3.2-251201"
export LOG_LEVEL="debug"

make run-agent
```

## Security

⚠️ **IMPORTANT**: Never commit `config.yaml` to git. It contains sensitive API keys.

- ✅ `config.yaml` is in `.gitignore`
- ✅ Use `config.yaml.example` as a template
- ✅ Use environment variables in production

See [../docs/SECURITY.md](../docs/SECURITY.md) for security best practices.

## Project Structure

```
agent/
├── cmd/
│   └── agent.go           # Main application entry
├── pkg/
│   ├── config/            # Configuration loading
│   │   └── config.go
│   └── llmmodel/          # LLM model implementations
│       ├── deepseek.go
│       ├── openai.go
│       └── openai_compatible/
├── config.yaml.example    # Configuration template
├── config.yaml            # Your actual config (gitignored)
└── Makefile
```

## Documentation

### User Guides
- [../docs/CONFIG_GUIDE.md](../docs/CONFIG_GUIDE.md) - Configuration guide
- [../docs/SECURITY.md](../docs/SECURITY.md) - Security best practices

### Developer Docs
- [pkg/llmmodel/README.md](pkg/llmmodel/README.md) - LLM model documentation
- [pkg/llmmodel/ARCHITECTURE.md](pkg/llmmodel/ARCHITECTURE.md) - Architecture overview

### Security Fixes
- [../docs/security-fixes/](../docs/security-fixes/) - Security fix history
- [../docs/security-fixes/2026-01-22/](../docs/security-fixes/2026-01-22/) - Latest fixes (4 items)

## Development

### Build

```bash
go build -o bin/agent ./cmd/agent.go
```

### Run with custom config

```bash
go run cmd/agent.go -config /path/to/config.yaml web api webui
```

### Run in console mode

```bash
go run cmd/agent.go console
```

## Requirements

- Go 1.23+ (for iter.Seq2 support)
- API key from your LLM provider

## License

[To be determined]
