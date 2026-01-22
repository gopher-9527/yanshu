# Agent Documentation

本目录包含 Yanshu Agent 的所有文档。

## 📚 文档目录

### 用户指南

#### [CONFIG_GUIDE.md](CONFIG_GUIDE.md)
**配置使用指南**

详细的配置说明文档，包括：
- 快速开始
- 配置方式（文件/环境变量）
- 完整配置结构
- 安全最佳实践
- Docker 部署
- 故障排查

**适合**: 所有需要配置和运行 agent 的用户

---

#### [SECURITY.md](SECURITY.md)
**安全最佳实践**

安全指南和最佳实践，包括：
- 已修复的安全问题
- 密钥管理
- .gitignore 配置
- 日志安全
- Git 历史清理
- Docker 部署安全
- 应急响应

**适合**: 所有开发者和运维人员

---

### 开发文档

#### [../pkg/llmmodel/README.md](../pkg/llmmodel/README.md)
**LLM 模型使用文档**

LLM 模型实现的使用文档，包括：
- 可用模型（DeepSeek, OpenAI）
- 使用示例
- 配置选项
- API 兼容性
- 限制说明

**适合**: 需要集成 LLM 模型的开发者

---

#### [../pkg/llmmodel/ARCHITECTURE.md](../pkg/llmmodel/ARCHITECTURE.md)
**LLM 包架构文档**

LLM 包的架构设计文档，包括：
- 架构概览
- 核心组件
- 如何添加新的 LLM 提供商
- 优势和扩展方向

**适合**: 需要扩展或维护 LLM 包的开发者

---

### 安全修复记录

#### [security-fixes/](security-fixes/)
**安全修复历史**

所有安全修复的详细记录，按日期组织：
- 修复总结
- 验证报告
- 最佳实践
- 修复时间线

**最新**: [2026-01-22 - API Key 硬编码修复](security-fixes/2026-01-22/)

---

## 📖 快速链接

### 新用户
1. 先看 [../README.md](../README.md) - 项目概览
2. 再看 [CONFIG_GUIDE.md](CONFIG_GUIDE.md) - 配置指南
3. 然后 [SECURITY.md](SECURITY.md) - 安全实践

### 开发者
1. [../pkg/llmmodel/ARCHITECTURE.md](../pkg/llmmodel/ARCHITECTURE.md) - 了解架构
2. [../pkg/llmmodel/README.md](../pkg/llmmodel/README.md) - 使用 LLM
3. [security-fixes/](security-fixes/) - 安全修复记录

### 运维人员
1. [CONFIG_GUIDE.md](CONFIG_GUIDE.md) - 配置和部署
2. [SECURITY.md](SECURITY.md) - 安全检查
3. [security-fixes/](security-fixes/) - 安全历史

## 🔍 文档搜索

### 按主题

**配置相关**:
- [CONFIG_GUIDE.md](CONFIG_GUIDE.md) - 完整配置指南
- [../config.yaml.example](../config.yaml.example) - 配置模板
- [../env.example](../env.example) - 环境变量模板

**安全相关**:
- [SECURITY.md](SECURITY.md) - 安全最佳实践
- [security-fixes/](security-fixes/) - 安全修复历史
- [security-fixes/2026-01-22/](security-fixes/2026-01-22/) - 最新修复

**开发相关**:
- [../pkg/llmmodel/](../pkg/llmmodel/) - LLM 模型包
- [../pkg/config/](../pkg/config/) - 配置包
- [../cmd/agent.go](../cmd/agent.go) - 主程序

## 📝 贡献文档

如果你想改进文档：

1. 在对应的 `.md` 文件中编辑
2. 确保链接正确
3. 更新本索引文件（如果添加新文档）
4. 提交 Pull Request

### 文档规范

- 使用 Markdown 格式
- 添加必要的代码示例
- 包含目录和快速链接
- 使用清晰的标题结构
- 添加适当的 emoji 图标

## 🔄 文档更新

文档会随着项目进展持续更新：

- **配置文档**: 当添加新配置选项时更新
- **安全文档**: 发现新的安全问题时更新
- **开发文档**: 架构变更时更新

## 📧 反馈

如有文档问题或建议：
1. 提交 GitHub Issue
2. 创建 Pull Request
3. 联系维护者

---

**文档版本**: v1.0  
**最后更新**: 2026-01-22  
**维护者**: Yanshu Team
