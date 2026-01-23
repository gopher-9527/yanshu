# 快速开始指南

## 安装和运行

### 1. 安装依赖

```bash
cd client/web
pnpm install
```

**注意**：本项目使用 `pnpm` 作为包管理器。如果尚未安装 pnpm：

```bash
# 使用 npm 安装 pnpm
npm install -g pnpm

# 或使用 Homebrew (macOS)
brew install pnpm
```

### 2. 配置环境变量（可选）

创建 `.env` 文件：

```env
VITE_API_URL=http://localhost:8080
VITE_AGENT_NAME=yanshu_agent
```

### 3. 启动 Agent 服务

在另一个终端窗口：

```bash
cd agent
make run-agent
# 或
go run cmd/agent.go web api webui
```

### 4. 启动前端开发服务器

```bash
cd client/web
pnpm dev
```

前端将在 http://localhost:3000 启动

## 功能特性

✅ **TypeScript** - 完整的类型安全  
✅ **儿童友好设计** - 温馨、可爱的界面  
✅ **流式输出** - 实时打字机效果  
✅ **历史记录** - 自动保存对话历史  
✅ **响应式设计** - 适配各种屏幕尺寸  

## 项目结构

```
client/web/
├── src/
│   ├── components/        # React 组件
│   │   ├── Header.tsx
│   │   ├── ChatInterface.tsx
│   │   ├── MessageList.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── MessageInput.tsx
│   │   └── TypingIndicator.tsx
│   ├── services/          # API 服务
│   │   └── agentService.ts
│   ├── types/             # TypeScript 类型
│   │   └── index.ts
│   ├── App.tsx            # 主应用
│   ├── main.tsx           # 入口
│   └── index.css          # 样式
├── package.json
├── tsconfig.json          # TypeScript 配置
└── vite.config.ts         # Vite 配置
```

## 开发命令

```bash
# 开发模式
pnpm dev

# 类型检查
pnpm type-check

# 构建生产版本
pnpm build

# 预览生产版本
pnpm preview

# 代码检查
pnpm lint
```

## 注意事项

1. **API 端点**：确保 Agent 服务运行在 `http://localhost:8080`
2. **CORS**：开发模式下使用 Vite 代理，生产环境需要配置 CORS
3. **流式输出**：当前使用 SSE（Server-Sent Events），如果 ADK 使用 WebSocket，请修改 `agentService.ts`

## 故障排查

### 无法连接到 Agent

- 检查 Agent 服务是否运行：`curl http://localhost:8080/api/agents/yanshu_agent/chat`
- 检查环境变量配置
- 查看浏览器控制台错误信息

### 类型错误

```bash
# 运行类型检查
pnpm type-check
```

### 构建错误

```bash
# 清理并重新安装
rm -rf node_modules pnpm-lock.yaml
pnpm install
```
