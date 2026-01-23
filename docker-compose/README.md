# Docker Compose 配置

本目录包含 Yanshu 项目的各种 Docker Compose 配置。

## 可用配置

### 1. [Caddy 反向代理](caddy/)

**用途**：反向代理前端和 Agent 服务，提供统一入口和自动 HTTPS

**特性**：
- 反向代理前端 Web 客户端
- 反向代理 Agent API 服务
- 自动 HTTPS（生产环境）
- WebSocket 支持
- 安全头配置

**快速开始**：
```bash
cd caddy
docker-compose up -d
```

详见：[caddy/README.md](caddy/README.md)

---

### 2. [Temporal Server](temporal/)

**用途**：工作流编排和任务调度

**特性**：
- PostgreSQL 持久化存储
- Temporal Server 核心服务
- Temporal Web UI

**快速开始**：
```bash
cd temporal
docker-compose up -d
```

详见：[temporal/README.md](temporal/README.md)

---

### 3. [AI Observability](ai-observability/)

**用途**：AI 服务可观测性（LiteLLM + 监控）

**特性**：
- LiteLLM 代理
- 监控和日志
- 请求追踪

**快速开始**：
```bash
cd ai-observability
docker-compose up -d
```

---

## 使用建议

### 开发环境

1. **仅启动 Agent**：
   ```bash
   cd agent
   make run-agent
   ```

2. **启动前端**：
   ```bash
   cd client/web
   pnpm dev
   ```

3. **使用 Caddy 统一入口**（可选）：
   ```bash
   cd docker-compose/caddy
   docker-compose up -d
   ```

### 生产环境

1. **使用完整服务栈**：
   ```bash
   cd docker-compose/caddy
   docker-compose -f docker-compose.full.yml up -d
   ```

2. **配置域名和 HTTPS**：
   - 编辑 `caddy/Caddyfile`
   - 配置 DNS 记录
   - Caddy 自动申请 SSL 证书

## 网络架构

```
Internet
   ↓
Caddy (80/443)
   ├─→ / → Web Client (3000)
   ├─→ /api/* → Agent API (8080)
   └─→ /ws/* → Agent WebSocket (8080)
```

## 注意事项

1. **端口冲突**：确保端口 80、443、8080、3000 未被占用
2. **环境变量**：生产环境使用 `.env` 文件管理敏感信息
3. **数据持久化**：重要数据存储在 Docker volumes 中
4. **日志管理**：定期清理日志文件，避免磁盘空间不足

## 相关文档

- [Caddy 配置文档](caddy/README.md)
- [Temporal 配置文档](temporal/README.md)
- [项目主 README](../../README.md)

---

**最后更新**: 2026-01-22  
**维护者**: Yanshu Team
