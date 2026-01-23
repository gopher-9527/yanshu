# Yanshu Web Client - 小言助手 Web 客户端

儿童友好的智能对话界面，支持与 Yanshu Agent 进行实时对话和流式输出。

## 特性

- 🎨 **儿童友好设计** - 温馨、可爱的界面，适合 3-18 岁用户
- 💬 **实时对话** - 与 Agent 进行流畅的对话体验
- 🌊 **流式输出** - 支持实时流式响应，打字机效果
- 📜 **历史记录** - 自动保存和展示对话历史
- ✨ **动画效果** - 丰富的动画和交互效果

## 技术栈

- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Tailwind CSS** - 样式框架
- **Lucide React** - 图标库

## 快速开始

### 安装依赖

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

### 开发模式

```bash
pnpm dev
```

应用将在 http://localhost:3000 启动

### 构建生产版本

```bash
pnpm build
```

构建产物在 `dist/` 目录

### 预览生产版本

```bash
pnpm preview
```

## 配置

### 环境变量

创建 `.env` 文件（可选）：

```env
VITE_API_URL=http://localhost:8080
VITE_AGENT_NAME=yanshu_agent
```

### 代理配置

开发模式下，Vite 已配置代理，将 `/api` 请求转发到 `http://localhost:8080`

## 设计说明

### 配色方案

- **Candy 色系** - 粉色系，温馨可爱
- **Sky 色系** - 蓝色系，清新自然
- **Sunshine 色系** - 黄色系，温暖明亮

### 组件结构

```
src/
├── components/
│   ├── Header.tsx          # 顶部导航
│   ├── ChatInterface.tsx   # 主聊天界面
│   ├── MessageList.tsx     # 消息列表
│   ├── MessageBubble.tsx  # 消息气泡
│   ├── MessageInput.tsx   # 输入框
│   └── TypingIndicator.tsx # 打字指示器
├── services/
│   └── agentService.ts    # Agent API 服务
├── types/
│   └── index.ts           # TypeScript 类型定义
├── App.tsx                # 主应用组件
├── main.tsx               # 入口文件
└── index.css              # 全局样式
```

## API 集成

### Agent 服务端点

应用需要连接到运行在 `http://localhost:8080` 的 Agent 服务。

**预期端点**：
- `POST /api/agents/{agent_name}/chat` - 发送消息
- `POST /api/agents/{agent_name}/chat/stream` - 流式发送消息（SSE）

**注意**：如果 ADK 的 API 端点不同，请修改 `src/services/agentService.ts` 中的端点配置。

## 功能说明

### 对话功能

1. 在输入框中输入消息
2. 点击"发送"按钮或按 Enter 键发送
3. 消息会立即显示在聊天界面
4. Agent 的回复会以流式方式显示

### 历史记录

- 对话历史自动保存在组件状态中
- 刷新页面会清空历史（未来可添加持久化）

## 开发计划

- [ ] 添加消息持久化（LocalStorage）
- [ ] 支持多 Agent 切换
- [ ] 添加表情选择器
- [ ] 支持语音输入
- [ ] 添加主题切换
- [ ] 优化移动端体验

## 许可证

[待定]
