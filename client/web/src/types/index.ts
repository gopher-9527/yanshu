/**
 * 消息类型定义
 */
export interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isStreaming?: boolean
  error?: boolean
}

/**
 * Agent API 响应类型
 */
export interface AgentResponse {
  response?: string
  message?: string
  content?: string
  text?: string
  chunk?: string
}

/**
 * Agent 服务配置
 */
export interface AgentServiceConfig {
  apiUrl: string
  agentName: string
}
