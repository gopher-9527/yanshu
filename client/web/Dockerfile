# 多阶段构建 - 前端 Web 客户端
# 使用 pnpm 作为包管理器
# Node.js 版本: 24.12.0 LTS "Krypton" (最新 LTS 版本，发布于 2025-12-10)
# 更新版本: 访问 https://nodejs.org/en/about/releases/ 查看最新 LTS 版本，更新下面的版本号
# 建议使用 LTS 版本以确保生产环境稳定性

# 阶段 1: 依赖安装和构建
FROM node:24.12.0-alpine AS builder

# 安装 pnpm
RUN corepack enable && corepack prepare pnpm@8.15.0 --activate

# 设置工作目录
WORKDIR /app

# 复制包管理文件
COPY package.json pnpm-lock.yaml* .npmrc ./

# 安装依赖
RUN pnpm install --frozen-lockfile

# 复制源代码
COPY . .

# 构建参数（用于构建时设置环境变量）
ARG VITE_API_URL=http://localhost:8080
ARG VITE_AGENT_NAME=yanshu_agent

# 设置环境变量（Vite 在构建时需要这些变量）
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_AGENT_NAME=${VITE_AGENT_NAME}

# 构建应用
RUN pnpm build

# 阶段 2: 生产环境
FROM caddy:2.7-alpine AS production

# 安装必要的工具（可选，用于调试）
RUN apk add --no-cache curl

# 复制构建产物到 Caddy 的静态文件目录
COPY --from=builder /app/dist /usr/share/caddy

# 复制 Caddyfile（如果使用 Caddy 作为静态文件服务器）
COPY Caddyfile.docker /etc/caddy/Caddyfile

# 暴露端口
EXPOSE 80

# 启动 Caddy
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile"]
