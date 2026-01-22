# Security - 安全指南

## 已修复的安全问题

### ✅ API Key 硬编码问题（已修复）

**问题**：API key 直接硬编码在 `cmd/agent.go` 源代码中

**风险**：
- 🔴 任何能访问代码仓库的人都能获取 API key
- 🔴 API key 会被提交到 git 历史记录中
- 🔴 可能导致 API 滥用、费用损失或数据泄露

**修复**：
- ✅ API key 移至配置文件 `config.yaml`
- ✅ `config.yaml` 已添加到 `.gitignore`
- ✅ 支持从环境变量加载
- ✅ 提供配置模板 `config.yaml.example`

## 安全最佳实践

### 1. 密钥管理

#### ✅ 正确做法

**使用配置文件**：
```yaml
# config.yaml (在 .gitignore 中)
model:
  api_key: "sk-xxxxx"
```

**使用环境变量**：
```bash
export DEEPSEEK_API_KEY="sk-xxxxx"
go run cmd/agent.go web api webui
```

**使用密钥管理服务**：
```go
// 从 AWS Secrets Manager 加载
apiKey, err := getSecretFromAWS("deepseek-api-key")
```

#### ❌ 错误做法

```go
// ❌ 永远不要硬编码
APIKey: "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

// ❌ 不要提交到 git
git add config.yaml  # config.yaml 包含密钥

// ❌ 不要在日志中打印完整密钥
logger.Info("Using key", "key", fullAPIKey)
```

### 2. .gitignore 配置

确保以下文件在 `.gitignore` 中：

```gitignore
# Sensitive configuration files
agent/config.yaml
agent/config.yml
.env
*.env

# Credentials
*.key
*.pem
credentials.json
```

### 3. 日志安全

#### ✅ 已实现的保护

```go
// 只记录 API key 前缀，不记录完整密钥
httpReq.Header.Set("Authorization", "Bearer "+c.apiKey)
// 日志中显示：Authorization: Bearer sk-xxxxxx...
```

#### 建议

- 定期审查日志，确保没有泄露敏感信息
- 使用结构化日志（slog），避免意外记录密钥
- 在错误消息中避免包含完整的请求/响应

### 4. Git 历史清理

如果之前已经提交了包含密钥的代码：

```bash
# ⚠️ 警告：这会重写 git 历史！
# 1. 使用 BFG Repo-Cleaner 或 git filter-branch
# 2. 或者更简单：撤销 API key，生成新的

# 推荐：撤销旧的 API key，生成新的
# 1. 登录 API 提供商的控制台
# 2. 撤销/删除泄露的 API key
# 3. 生成新的 API key
# 4. 更新 config.yaml
```

### 5. 配置文件权限

设置合适的文件权限：

```bash
# 只有所有者可以读写
chmod 600 agent/config.yaml

# 验证权限
ls -la agent/config.yaml
# 应该显示：-rw------- (600)
```

### 6. Docker 部署安全

#### 使用 Docker Secrets

```yaml
# docker-compose.yml
services:
  agent:
    secrets:
      - deepseek_api_key
    environment:
      - DEEPSEEK_API_KEY_FILE=/run/secrets/deepseek_api_key

secrets:
  deepseek_api_key:
    file: ./secrets/deepseek_api_key.txt
```

#### 使用环境变量文件

```yaml
# docker-compose.yml
services:
  agent:
    env_file:
      - .env  # 不要提交此文件！
```

```bash
# .env (在 .gitignore 中)
DEEPSEEK_API_KEY=sk-xxxxx
```

## 安全检查清单

在提交代码前检查：

- [ ] 没有硬编码的 API key
- [ ] 没有硬编码的密码、token
- [ ] `config.yaml` 在 `.gitignore` 中
- [ ] `.env` 文件在 `.gitignore` 中
- [ ] 提供了配置模板（`.example` 文件）
- [ ] README 说明了如何配置
- [ ] 日志不包含完整的密钥
- [ ] 配置文件有适当的权限（600）

## 验证配置安全

### 检查 .gitignore

```bash
# 确认配置文件不会被 git 跟踪
git check-ignore agent/config.yaml
# 应该输出：agent/config.yaml

# 查看 git 状态
git status
# 不应该看到 config.yaml
```

### 扫描代码中的密钥

```bash
# 使用 gitleaks 扫描
gitleaks detect --source . --verbose

# 或使用 grep 简单检查
grep -r "sk-[a-zA-Z0-9]" agent/ --exclude-dir=.git
# 应该只在 config.yaml 中找到（不在 .go 文件中）
```

### 审计 Git 历史

```bash
# 检查 git 历史中是否有密钥
git log -p | grep -i "api.key\|sk-"
```

## 应急响应

### 如果 API key 泄露

立即执行以下步骤：

1. **撤销泄露的 API key**
   - 登录 API 提供商控制台
   - 删除/撤销泄露的 key

2. **生成新的 API key**
   - 创建新的 key
   - 更新配置文件

3. **审计使用记录**
   - 检查 API 使用日志
   - 确认是否有异常调用

4. **通知相关人员**
   - 如果是公司项目，通知安全团队
   - 如果泄露到公开仓库，立即删除

5. **清理 git 历史**（如果已提交）
   - 使用 BFG Repo-Cleaner
   - 或创建新的仓库

## 合规性

### GDPR / 数据保护

- API key 属于敏感信息
- 应使用加密存储（生产环境）
- 访问应有审计日志
- 定期轮换密钥

### SOC 2 / ISO 27001

- 实施密钥管理策略
- 使用密钥管理服务（KMS）
- 定期安全审计
- 员工安全培训

## 相关资源

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [12-Factor App - Config](https://12factor.net/config)
- [Git Secrets](https://github.com/awslabs/git-secrets)
- [gitleaks](https://github.com/gitleaks/gitleaks)

## 报告安全问题

如果你发现安全问题，请：

1. **不要公开披露**
2. 发送邮件至：security@example.com（替换为实际联系方式）
3. 我们会在 24 小时内响应

---

**最后更新**: 2026-01-22  
**维护者**: Yanshu Security Team
