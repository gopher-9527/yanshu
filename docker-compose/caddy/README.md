# Caddy 反向代理配置

Caddy 用于反向代理前端 Web 客户端和 Agent 服务，提供统一的入口和自动 HTTPS 支持。

## 功能特性

- ✅ **反向代理** - 统一入口，代理前端和 API 服务
- ✅ **自动 HTTPS** - 生产环境自动申请和续期 SSL 证书
- ✅ **WebSocket 支持** - 支持 Agent 的 WebSocket 连接
- ✅ **日志记录** - 访问日志和错误日志
- ✅ **安全头** - 生产环境自动添加安全响应头

## 快速开始

### 1. 仅启动 Caddy（需要其他服务已运行）

```bash
cd docker-compose/caddy
docker-compose up -d
```

### 2. 启动完整服务栈（包含前端和 Agent）

```bash
cd docker-compose/caddy
docker-compose -f docker-compose.full.yml up -d
```

### 3. 查看日志

```bash
# Caddy 日志
docker-compose logs -f caddy

# 所有服务日志
docker-compose -f docker-compose.full.yml logs -f
```

### 4. 停止服务

```bash
docker-compose down
# 或
docker-compose -f docker-compose.full.yml down
```

## 配置说明

### Caddyfile

`Caddyfile` 是 Caddy 的配置文件，定义了路由规则：

- `/` - 前端 Web 客户端（代理到 `web:3000`）
- `/api/*` - Agent API 服务（代理到 `agent:8080`）
- `/ws/*` - WebSocket 连接（代理到 `agent:8080`）

### 本地开发

默认配置使用 `localhost`，通过 HTTP 访问：

```bash
# 访问前端
http://localhost

# 访问 API
http://localhost/api/agents/yanshu_agent/chat
```

### 生产环境

1. **编辑 Caddyfile**：
   - 取消注释生产环境配置块
   - 替换 `example.com` 为你的域名

2. **配置 DNS**：
   - 将域名 A 记录指向服务器 IP
   - 如果使用 Cloudflare，配置 API Token

3. **设置环境变量**（如果使用 DNS 验证）：
   ```bash
   export CLOUDFLARE_API_TOKEN=your-token
   ```

4. **启动服务**：
   ```bash
   docker-compose up -d
   ```

Caddy 会自动：
- 申请 SSL 证书
- 配置 HTTPS
- 自动续期证书

## 端口说明

| 端口 | 说明 |
|------|------|
| 80 | HTTP（自动重定向到 HTTPS） |
| 443 | HTTPS |
| 2019 | Caddy 管理 API（可选） |

## 网络架构

```
Internet
   ↓
Caddy (80/443)
   ├─→ / → Web Client (3000)
   ├─→ /api/* → Agent API (8080)
   └─→ /ws/* → Agent WebSocket (8080)
```

## 环境变量

### Caddy 服务

- `CADDY_ADMIN` - Caddy 管理 API 地址（默认: `0.0.0.0:2019`）

### Agent 服务（在 docker-compose.full.yml 中）

- `DEEPSEEK_API_KEY` - DeepSeek API 密钥（必需）
- `MODEL_NAME` - 模型名称（默认: `deepseek/deepseek-v3.2-251201`）
- `MODEL_BASE_URL` - API 基础 URL
- `LOG_LEVEL` - 日志级别（默认: `info`）

## 安全配置

### 生产环境安全头

Caddyfile 中已配置以下安全头：

- `Strict-Transport-Security` - 强制 HTTPS
- `X-Content-Type-Options` - 防止 MIME 类型嗅探
- `X-Frame-Options` - 防止点击劫持
- `Content-Security-Policy` - 内容安全策略

### 限制访问

可以在 Caddyfile 中添加访问控制：

```caddyfile
handle /api/* {
    # IP 白名单
    @allowed {
        remote_ip 192.168.1.0/24 10.0.0.0/8
    }
    handle @allowed {
        reverse_proxy agent:8080
    }
    handle {
        respond "Forbidden" 403
    }
}
```

## 日志管理

### 访问日志

日志文件位置：`/var/log/caddy/access.log`（容器内）

查看日志：
```bash
docker-compose exec caddy tail -f /var/log/caddy/access.log
```

### 日志格式

使用 JSON 格式，便于解析和分析。

## 故障排查

### 1. 无法访问服务

```bash
# 检查容器状态
docker-compose ps

# 检查 Caddy 配置
docker-compose exec caddy caddy validate --config /etc/caddy/Caddyfile

# 查看 Caddy 日志
docker-compose logs caddy
```

### 2. HTTPS 证书问题

```bash
# 检查证书状态
docker-compose exec caddy caddy trust

# 查看证书信息
docker-compose exec caddy ls -la /data/caddy/certificates/
```

### 3. 代理连接失败

```bash
# 检查网络连接
docker-compose exec caddy ping web
docker-compose exec caddy ping agent

# 检查服务是否运行
docker-compose ps
```

## 高级配置

### 负载均衡

如果有多个 Agent 实例，可以配置负载均衡：

```caddyfile
handle /api/* {
    reverse_proxy agent1:8080 agent2:8080 agent3:8080 {
        lb_policy round_robin
    }
}
```

### 限流

添加限流配置：

```caddyfile
handle /api/* {
    rate_limit {
        zone dynamic {
            key {remote_host}
            events 100
            window 1m
        }
    }
    reverse_proxy agent:8080
}
```

### 压缩

启用响应压缩：

```caddyfile
encode gzip zstd
```

## 相关文档

- [Caddy 官方文档](https://caddyserver.com/docs/)
- [Caddy Docker 镜像](https://hub.docker.com/_/caddy)
- [Caddyfile 语法](https://caddyserver.com/docs/caddyfile)

## 注意事项

1. **数据持久化**：Caddy 的数据和配置存储在 Docker volumes 中，删除容器不会丢失数据
2. **证书存储**：SSL 证书存储在 `caddy_data` volume 中
3. **配置更新**：修改 Caddyfile 后需要重启容器：`docker-compose restart caddy`
4. **端口冲突**：确保 80 和 443 端口未被其他服务占用

---

**最后更新**: 2026-01-22  
**维护者**: Yanshu Team
