import { Bot, User } from 'lucide-react'
import type { Message } from '../types'

interface MessageBubbleProps {
  message: Message
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const bubbleClass = isUser
    ? 'chat-bubble-user ml-auto max-w-[80%]'
    : 'chat-bubble-assistant mr-auto max-w-[80%]'

  return (
    <div
      className={`flex items-start space-x-3 ${
        isUser ? 'flex-row-reverse space-x-reverse' : ''
      }`}
    >
      <div
        className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser
            ? 'bg-gradient-to-br from-sky-400 to-sky-500'
            : 'bg-gradient-to-br from-candy-400 to-candy-500'
        } shadow-md`}
      >
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-white" />
        )}
      </div>
      <div className={bubbleClass}>
        <p className="text-base leading-relaxed whitespace-pre-wrap break-words">
          {message.content || '...'}
        </p>
        {message.error && (
          <p className="text-xs text-red-400 mt-2">⚠️ 发送失败</p>
        )}
      </div>
    </div>
  )
}

export default MessageBubble
