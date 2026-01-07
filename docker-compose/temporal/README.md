# Temporal Server Docker Compose

本地运行 Temporal Server 的 Docker Compose 配置。

## 服务说明

此配置包含以下服务：

1. **PostgreSQL** - Temporal 的持久化存储
   - 端口: `5433` (映射到容器内的 5432)
   - 用户: `temporal`
   - 密码: `temporal`
   - 数据库: `temporal`

2. **Temporal Server** - 包含所有核心服务
   - Frontend Service: `7233` (gRPC API), `6933` (Membership)
   - History Service: `7234` (gRPC API), `6934` (Membership)
   - Matching Service: `7235` (gRPC API), `6935` (Membership)
   - Worker Service: `6939` (Membership)

3. **Temporal Web UI** - Temporal 管理界面
   - 端口: `8088`
   - 访问地址: http://localhost:8088

## 使用方法

### 启动服务

```bash
cd docker-compose/temporal
docker-compose up -d
```

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f temporal
docker-compose logs -f temporal-ui
docker-compose logs -f postgres
```

### 停止服务

```bash
docker-compose down
```

### 停止并删除数据卷（清理所有数据）

```bash
docker-compose down -v
```

## 访问服务

- **Temporal Web UI**: http://localhost:8088
- **Temporal gRPC API**: localhost:7233

## 默认命名空间

Temporal Server 会自动创建一个默认命名空间 `default`，保留期为 1 天。

## 注意事项

1. PostgreSQL 端口映射到 `5433` 以避免与本地 PostgreSQL 冲突
2. 所有服务使用 `temporal` 网络进行内部通信
3. 数据会持久化到 Docker volumes，重启不会丢失数据
4. 此配置适用于开发和测试环境，不建议直接用于生产环境
