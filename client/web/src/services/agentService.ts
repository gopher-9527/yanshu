/**
 * Agent Service - 与后端 Agent API 通信
 * 
 * ADK launcher 在 web api 模式下提供以下端点：
 * - POST /api/agents/{agent_name}/chat - 发送消息
 * - WebSocket 或 SSE 用于流式输出
 */

import type { AgentResponse } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080'
const AGENT_NAME = import.meta.env.VITE_AGENT_NAME || 'yanshu_agent'

/**
 * 发送消息（非流式）
 */
export async function sendMessage(text: string): Promise<string> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agents/${AGENT_NAME}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: text,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data: AgentResponse = await response.json()
    return data.response || data.message || ''
  } catch (error) {
    console.error('Error sending message:', error)
    throw error
  }
}

/**
 * 流式发送消息（使用 Server-Sent Events）
 */
export async function streamMessage(
  text: string,
  onChunk: (chunk: string) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agents/${AGENT_NAME}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: text,
        stream: true,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('Response body is not readable')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data: AgentResponse = JSON.parse(line.slice(6))
            if (data.content || data.text || data.chunk) {
              const chunk = data.content || data.text || data.chunk || ''
              onChunk(chunk)
            }
          } catch (e) {
            // 忽略解析错误
          }
        } else if (line.trim() && !line.startsWith(':')) {
          // 尝试直接解析为 JSON
          try {
            const data: AgentResponse = JSON.parse(line)
            if (data.content || data.text || data.chunk) {
              const chunk = data.content || data.text || data.chunk || ''
              onChunk(chunk)
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }

    // 处理剩余的 buffer
    if (buffer.trim()) {
      try {
        const data: AgentResponse = JSON.parse(buffer)
        if (data.content || data.text || data.chunk) {
          const chunk = data.content || data.text || data.chunk || ''
          onChunk(chunk)
        }
      } catch (e) {
        // 忽略解析错误
      }
    }
  } catch (error) {
    console.error('Error streaming message:', error)
    throw error
  }
}

/**
 * WebSocket 连接接口
 */
export interface WebSocketConnection {
  send: (text: string) => void
  close: () => void
}

/**
 * 使用 WebSocket 流式发送消息（备选方案）
 */
export function createWebSocketConnection(
  onMessage: (chunk: string) => void,
  onError?: (error: Event) => void
): WebSocketConnection {
  const wsUrl = `ws://localhost:8080/ws/agents/${AGENT_NAME}/chat`
  const ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    console.log('WebSocket connected')
  }

  ws.onmessage = (event: MessageEvent) => {
    try {
      const data: AgentResponse = JSON.parse(event.data)
      if (data.content || data.text || data.chunk) {
        const chunk = data.content || data.text || data.chunk || ''
        onMessage(chunk)
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error)
    }
  }

  ws.onerror = (error: Event) => {
    console.error('WebSocket error:', error)
    if (onError) onError(error)
  }

  ws.onclose = () => {
    console.log('WebSocket closed')
  }

  return {
    send: (text: string) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ message: text }))
      }
    },
    close: () => {
      ws.close()
    },
  }
}
