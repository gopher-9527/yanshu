import { useState, useRef, useEffect } from 'react'
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import { streamMessage } from '../services/agentService'
import type { Message } from '../types'

function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return

    // 添加用户消息
    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])

    // 添加占位符消息用于流式输出
    const assistantMessageId = Date.now() + 1
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    }
    setMessages((prev) => [...prev, assistantMessage])

    setIsLoading(true)

    try {
      // 使用流式输出
      await streamMessage(text, (chunk: string) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: msg.content + chunk, isStreaming: true }
              : msg
          )
        )
      })

      // 流式输出完成
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, isStreaming: false }
            : msg
        )
      )
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: msg.content || '抱歉，我遇到了一些问题，请稍后再试。',
                isStreaming: false,
                error: true,
              }
            : msg
        )
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-3xl shadow-2xl overflow-hidden flex flex-col h-[600px]">
      <MessageList messages={messages} messagesEndRef={messagesEndRef} />
      <MessageInput
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />
    </div>
  )
}

export default ChatInterface
