# 版本更新指南

本文档记录项目中使用的关键依赖版本，以及如何更新它们。

## 当前版本

### Go (Agent 服务)

- **当前版本**: 1.25.6
- **发布日期**: 2026-01-15
- **类型**: 稳定版
- **使用位置**:
  - `agent/Dockerfile`
  - `agent/Dockerfile.dev`

**更新步骤**:
1. 访问 https://go.dev/dl/ 查看最新版本
2. 更新 `agent/Dockerfile` 和 `agent/Dockerfile.dev` 中的版本号
3. 测试构建和运行
4. 更新本文档

---

### Node.js (前端 Web 客户端)

- **当前版本**: 24.12.0 LTS "Krypton"
- **发布日期**: 2025-12-10
- **类型**: LTS (长期支持)
- **支持期限**: 至 2028-04
- **使用位置**:
  - `client/web/Dockerfile`
  - `client/web/Dockerfile.dev`

**更新步骤**:
1. 访问 https://nodejs.org/en/about/releases/ 查看最新 LTS 版本
2. 更新 `client/web/Dockerfile` 和 `client/web/Dockerfile.dev` 中的版本号
3. 测试构建和运行
4. 更新本文档

---

## 版本选择建议

### Go

- ✅ **推荐**: 使用最新的稳定版本（如 1.25.x）
- ✅ **生产环境**: 使用已发布至少 1 个月的稳定版本
- ❌ **避免**: 使用 rc (release candidate) 或 beta 版本

### Node.js

- ✅ **推荐**: 使用最新的 LTS 版本（如 24.x）
- ✅ **生产环境**: 使用 Active LTS 版本
- ⚠️ **谨慎**: Current 版本（非 LTS）仅用于测试新特性
- ❌ **避免**: 使用奇数版本（如 25.x）在生产环境

---

## 版本检查命令

### 检查 Go 版本

```bash
# 查看 Docker 镜像中的 Go 版本
docker run --rm golang:1.25.6-alpine go version

# 查看最新可用版本
curl -s https://go.dev/VERSION?m=text
```

### 检查 Node.js 版本

```bash
# 查看 Docker 镜像中的 Node.js 版本
docker run --rm node:24.12.0-alpine node --version

# 查看最新 LTS 版本
curl -s https://nodejs.org/dist/index.json | jq '.[] | select(.lts != false) | {version: .version, lts: .lts, date: .date}' | head -5
```

---

## 更新历史

| 日期 | 组件 | 旧版本 | 新版本 | 原因 |
|------|------|--------|--------|------|
| 2026-01-22 | Go | 1.23 | 1.25.6 | 使用最新稳定版 |
| 2026-01-22 | Node.js | 20 | 24.12.0 | 使用最新 LTS 版本 |

---

## 相关链接

- [Go 发布历史](https://go.dev/doc/devel/release.html)
- [Go 下载页面](https://go.dev/dl/)
- [Node.js 发布计划](https://nodejs.org/en/about/releases/)
- [Node.js 下载页面](https://nodejs.org/en/download/)

---

**最后更新**: 2026-01-22  
**维护者**: Yanshu Team
