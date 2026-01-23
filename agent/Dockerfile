# 多阶段构建 - Agent 服务
# Go 版本: 1.25.6 (最新稳定版，发布于 2026-01-15)
# 更新版本: 访问 https://go.dev/dl/ 查看最新版本，更新下面的版本号
# 建议使用 LTS 或稳定版本，避免使用 rc/beta 版本

# 阶段 1: 构建
FROM golang:1.25.6-alpine AS builder

# 安装构建依赖
RUN apk add --no-cache git ca-certificates tzdata

# 设置工作目录
WORKDIR /build

# 复制 go mod 文件
COPY go.mod go.sum ./

# 下载依赖
RUN go mod download

# 复制源代码
COPY . .

# 构建应用
# CGO_ENABLED=0 生成静态链接的二进制文件
# -ldflags="-w -s" 减小二进制文件大小
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s -extldflags '-static'" \
    -o agent \
    ./cmd/agent.go

# 阶段 2: 运行环境
FROM alpine:3.19

# 安装必要的运行时依赖
RUN apk add --no-cache ca-certificates tzdata && \
    update-ca-certificates

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 创建非 root 用户
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# 设置工作目录
WORKDIR /app

# 从构建阶段复制二进制文件
COPY --from=builder /build/agent /app/agent

# 复制配置文件模板（可选）
COPY config.yaml.example /app/config.yaml.example

# 设置权限
RUN chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 暴露端口（Agent 默认端口）
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# 启动应用
# 使用环境变量或配置文件
CMD ["/app/agent"]
