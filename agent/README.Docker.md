# Docker 构建指南 - Agent 服务

## 构建镜像

### 生产环境构建

```bash
cd agent
docker build -t yanshu-agent:latest .
```

### 开发环境构建

```bash
docker build -f Dockerfile.dev -t yanshu-agent:dev .
```

## 运行容器

### 生产环境

```bash
docker run -d \
  --name yanshu-agent \
  -p 8080:8080 \
  -e DEEPSEEK_API_KEY=your-api-key \
  -e MODEL_NAME=deepseek/deepseek-v3.2-251201 \
  -e MODEL_BASE_URL=https://api.qnaigc.com \
  -e LOG_LEVEL=info \
  yanshu-agent:latest
```

### 使用配置文件

```bash
# 创建配置文件
cp config.yaml.example config.yaml
# 编辑 config.yaml，填入 API key

# 运行容器（挂载配置文件）
docker run -d \
  --name yanshu-agent \
  -p 8080:8080 \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  yanshu-agent:latest
```

### 开发环境（支持热重载）

```bash
# 使用 air 进行热重载
docker run -d \
  --name yanshu-agent-dev \
  -p 8080:8080 \
  -v $(pwd):/app \
  -v go-mod-cache:/go/pkg/mod \
  -e DEEPSEEK_API_KEY=your-api-key \
  -e LOG_LEVEL=debug \
  yanshu-agent:dev
```

## 使用 Docker Compose

### 生产环境

```bash
# 创建 .env 文件
cat > .env << EOF
DEEPSEEK_API_KEY=your-api-key
MODEL_NAME=deepseek/deepseek-v3.2-251201
MODEL_BASE_URL=https://api.qnaigc.com
LOG_LEVEL=info
EOF

# 启动服务
docker-compose up -d
```

### 开发环境

编辑 `docker-compose.yml`，取消注释 `agent-dev` 服务，然后：

```bash
docker-compose up -d agent-dev
```

## 环境变量

| 变量 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | - | ✅ |
| `MODEL_NAME` | 模型名称 | `deepseek/deepseek-v3.2-251201` | ❌ |
| `MODEL_BASE_URL` | API 基础 URL | `https://api.qnaigc.com` | ❌ |
| `LOG_LEVEL` | 日志级别 | `info` | ❌ |
| `CONFIG_PATH` | 配置文件路径 | `config.yaml` | ❌ |

## 构建优化

### 多阶段构建

Dockerfile 使用多阶段构建：
1. **builder 阶段**：编译 Go 应用
2. **production 阶段**：最小化运行时镜像

### 静态链接

构建时使用 `CGO_ENABLED=0` 和静态链接，生成：
- 更小的二进制文件
- 无需 C 库依赖
- 更好的可移植性

### 安全优化

- 使用非 root 用户运行
- 最小化基础镜像（Alpine）
- 只复制必要的文件

## 健康检查

容器包含健康检查配置：

```bash
# 手动检查健康状态
docker inspect --format='{{.State.Health.Status}}' yanshu-agent

# 查看健康检查日志
docker inspect yanshu-agent | grep -A 10 Health
```

## 故障排查

### 构建失败

```bash
# 清理构建缓存
docker builder prune

# 重新构建（不使用缓存）
docker build --no-cache -t yanshu-agent:latest .
```

### 容器无法启动

```bash
# 查看日志
docker logs yanshu-agent

# 查看详细日志
docker logs -f yanshu-agent

# 进入容器调试
docker exec -it yanshu-agent sh
```

### API Key 错误

```bash
# 检查环境变量
docker exec yanshu-agent env | grep DEEPSEEK

# 检查配置文件
docker exec yanshu-agent cat /app/config.yaml
```

### 端口冲突

```bash
# 检查端口占用
lsof -i :8080

# 使用其他端口
docker run -p 8081:8080 yanshu-agent:latest
```

## 生产部署建议

1. **使用 Caddy 反向代理**：参考 `docker-compose/caddy/`
2. **配置管理**：使用 Docker secrets 或环境变量
3. **日志管理**：配置日志收集和监控
4. **资源限制**：设置 CPU 和内存限制
5. **自动重启**：使用 `restart: unless-stopped`

### 资源限制示例

```yaml
services:
  agent:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

## 相关文档

- [主 README](README.md)
- [配置指南](../docs/CONFIG_GUIDE.md)
- [Docker Compose 配置](../docker-compose/caddy/README.md)
