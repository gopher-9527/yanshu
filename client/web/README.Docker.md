# Docker 构建指南 - 前端 Web 客户端

## 构建镜像

### 生产环境构建

```bash
cd client/web
docker build -t yanshu-web:latest .
```

### 开发环境构建

```bash
docker build -f Dockerfile.dev -t yanshu-web:dev .
```

## 运行容器

### 生产环境

```bash
docker run -d \
  --name yanshu-web \
  -p 3000:80 \
  yanshu-web:latest
```

访问：http://localhost:3000

### 开发环境（支持热重载）

```bash
docker run -d \
  --name yanshu-web-dev \
  -p 3000:3000 \
  -v $(pwd):/app \
  -v /app/node_modules \
  -e VITE_API_URL=http://localhost:8080/api \
  -e VITE_AGENT_NAME=yanshu_agent \
  yanshu-web:dev
```

## 使用 Docker Compose

### 生产环境

```bash
docker-compose up -d
```

### 开发环境

编辑 `docker-compose.yml`，取消注释 `web-dev` 服务，然后：

```bash
docker-compose up -d web-dev
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VITE_API_URL` | Agent API 地址 | `http://localhost:8080` |
| `VITE_AGENT_NAME` | Agent 名称 | `yanshu_agent` |
| `NODE_ENV` | 环境模式 | `production` |

## 构建优化

### 多阶段构建

Dockerfile 使用多阶段构建：
1. **builder 阶段**：安装依赖并构建应用
2. **production 阶段**：使用 Caddy 提供静态文件服务

### 缓存优化

构建时会利用 Docker 层缓存：
- 先复制 `package.json` 和 `pnpm-lock.yaml`
- 安装依赖（如果这些文件未变化，会使用缓存）
- 再复制源代码并构建

### 镜像大小优化

- 使用 Alpine Linux 基础镜像
- 多阶段构建，只保留必要的运行时文件
- 使用 Caddy 作为轻量级 Web 服务器

## 故障排查

### 构建失败

```bash
# 清理构建缓存
docker builder prune

# 重新构建（不使用缓存）
docker build --no-cache -t yanshu-web:latest .
```

### 容器无法启动

```bash
# 查看日志
docker logs yanshu-web

# 进入容器调试
docker exec -it yanshu-web sh
```

### 端口冲突

```bash
# 检查端口占用
lsof -i :3000

# 使用其他端口
docker run -p 3001:80 yanshu-web:latest
```

## 生产部署建议

1. **使用 Caddy 反向代理**：参考 `docker-compose/caddy/`
2. **配置 HTTPS**：通过 Caddy 自动申请证书
3. **环境变量**：使用 `.env` 文件或 Docker secrets
4. **健康检查**：配置健康检查端点
5. **日志管理**：配置日志收集和监控

## 相关文档

- [主 README](README.md)
- [Docker Compose 配置](../docker-compose/caddy/README.md)
