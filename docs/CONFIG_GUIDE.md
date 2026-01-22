# Configuration Guide - 配置指南

## 安全问题修复

**已修复**：API key 不再硬编码在源代码中，而是从配置文件或环境变量加载。

## 快速开始

### 1. 创建配置文件

从模板创建你的配置文件：

```bash
cd agent
cp config.yaml.example config.yaml
```

### 2. 编辑配置文件

编辑 `config.yaml`，填入你的实际 API key：

```yaml
model:
  api_key: "your-actual-api-key-here"  # ← 修改这里
  model_name: "deepseek/deepseek-v3.2-251201"
  base_url: "https://api.qnaigc.com"
  timeout: "5m"
```

### 3. 运行应用

```bash
make run-agent
# 或
go run cmd/agent.go web api webui
```

## 配置方式

### 方式 1: 配置文件（推荐）

**优点**：
- ✅ 集中管理所有配置
- ✅ 支持复杂配置结构
- ✅ 易于维护和版本控制（模板文件）

**使用**：
1. 创建 `config.yaml`
2. 填入实际值
3. 运行应用（默认读取 `config.yaml`）

**指定配置文件**：
```bash
go run cmd/agent.go -config /path/to/config.yaml web api webui
```

### 方式 2: 环境变量

**优点**：
- ✅ 容器化部署友好
- ✅ 云原生最佳实践
- ✅ 不需要配置文件

**使用**：
```bash
export DEEPSEEK_API_KEY="your-api-key"
export MODEL_NAME="deepseek/deepseek-v3.2-251201"
export MODEL_BASE_URL="https://api.qnaigc.com"
export LOG_LEVEL="debug"

# 运行应用（环境变量会覆盖配置文件）
make run-agent
```

### 方式 3: 混合使用

配置文件提供默认值，环境变量覆盖：

```bash
# config.yaml 有基本配置
# 通过环境变量覆盖 API key（更安全）
export DEEPSEEK_API_KEY="your-api-key"

make run-agent
```

## 配置文件结构

### 完整配置示例

```yaml
# LLM Model Configuration
model:
  # API key (required)
  # Environment variable: DEEPSEEK_API_KEY
  api_key: "sk-xxxxx"
  
  # Model name (optional, defaults to "deepseek-chat")
  # Environment variable: MODEL_NAME
  model_name: "deepseek/deepseek-v3.2-251201"
  
  # API base URL (optional, defaults to "https://api.deepseek.com")
  # Environment variable: MODEL_BASE_URL
  base_url: "https://api.qnaigc.com"
  
  # Request timeout (optional, defaults to "5m")
  timeout: "5m"

# Agent Configuration
agent:
  name: "yanshu_agent"
  description: "A helpful voice assistant"
  instruction: "You are a helpful assistant that tells the current time in a city."

# Logging Configuration
logging:
  # Log level: debug, info, warn, error
  # Environment variable: LOG_LEVEL
  level: "debug"
  
  # Add source location (file:line) to logs
  add_source: true

# Server Configuration (for web mode)
server:
  port: 8080
  read_timeout: "15s"
  write_timeout: "15s"
  idle_timeout: "60s"
```

## 环境变量优先级

环境变量会覆盖配置文件的值：

| 配置项 | 环境变量 | 默认值 |
|--------|----------|--------|
| model.api_key | `DEEPSEEK_API_KEY` | (required) |
| model.model_name | `MODEL_NAME` | `deepseek-chat` |
| model.base_url | `MODEL_BASE_URL` | `https://api.deepseek.com` |
| logging.level | `LOG_LEVEL` | `info` |

## 安全最佳实践

### ✅ DO（推荐做法）

1. **使用配置文件或环境变量**
   ```bash
   export DEEPSEEK_API_KEY="sk-xxxxx"
   ```

2. **配置文件不提交到 git**
   - `config.yaml` 已在 `.gitignore` 中
   - 只提交 `config.yaml.example` 模板

3. **生产环境使用环境变量**
   ```yaml
   # docker-compose.yml
   services:
     agent:
       environment:
         - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
   ```

4. **使用密钥管理服务**（高级）
   - AWS Secrets Manager
   - Google Secret Manager
   - HashiCorp Vault

### ❌ DON'T（避免这样做）

1. **不要硬编码 API key 到代码中**
   ```go
   // ❌ 永远不要这样做！
   APIKey: "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   ```

2. **不要提交 config.yaml 到 git**
   ```bash
   # 检查是否在 .gitignore 中
   git check-ignore agent/config.yaml  # 应该显示匹配
   ```

3. **不要在日志中打印完整 API key**
   - 已实现：日志只显示前缀（如 `sk-xxxxxx...`）

4. **不要把密钥放在公开的地方**
   - 不要放在 issue、PR、文档中
   - 不要放在错误消息中

## Docker 部署

### 使用环境变量文件

创建 `.env` 文件（已在 .gitignore 中）：

```bash
# .env
DEEPSEEK_API_KEY=sk-xxxxx
MODEL_NAME=deepseek/deepseek-v3.2-251201
MODEL_BASE_URL=https://api.qnaigc.com
LOG_LEVEL=info
```

在 `docker-compose.yml` 中使用：

```yaml
services:
  agent:
    build: ./agent
    env_file:
      - .env
    # 或直接引用
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
```

## 故障排查

### 问题 1: "API key is required"

**原因**：没有提供 API key

**解决**：
```bash
# 方式 1: 创建 config.yaml
cp config.yaml.example config.yaml
# 编辑 config.yaml，填入 API key

# 方式 2: 使用环境变量
export DEEPSEEK_API_KEY="your-api-key"
```

### 问题 2: "Failed to load config"

**原因**：找不到配置文件

**解决**：
```bash
# 确认配置文件存在
ls -la config.yaml

# 或指定配置文件路径
go run cmd/agent.go -config /path/to/config.yaml web api webui
```

### 问题 3: "Invalid timeout value"

**原因**：timeout 格式错误

**解决**：
```yaml
# 正确格式（使用 Go 的 time.Duration 格式）
timeout: "5m"    # ✅ 5 分钟
timeout: "30s"   # ✅ 30 秒
timeout: "2h"    # ✅ 2 小时

# 错误格式
timeout: "5 minutes"  # ❌
timeout: "300"        # ❌
```

## 配置验证

运行应用时，会在日志中看到配置信息：

```
level=INFO msg="Starting agent application" config_file=config.yaml log_level=debug
level=INFO msg="OpenAI-compatible client created" baseURL=https://api.qnaigc.com model=deepseek/... timeout=5m0s
level=INFO msg="Model created successfully"
level=INFO msg="Agent created successfully" name=yanshu_agent
```

## 迁移指南

### 从硬编码迁移到配置文件

如果你之前使用了硬编码的配置：

1. **创建配置文件**：
   ```bash
   cp config.yaml.example config.yaml
   ```

2. **复制你的配置值**：
   - API key
   - Model name
   - Base URL

3. **删除硬编码的值**（已完成）

4. **测试**：
   ```bash
   make run-agent
   ```

5. **确认 config.yaml 不会被提交**：
   ```bash
   git status  # 不应该看到 config.yaml
   ```

## 参考资源

- [Go YAML 库文档](https://pkg.go.dev/gopkg.in/yaml.v3)
- [12-Factor App - Config](https://12factor.net/config)
- [OWASP - Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
