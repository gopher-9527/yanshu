import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'
import type { Message } from '../types'

interface MessageListProps {
  messages: Message[]
  messagesEndRef: React.RefObject<HTMLDivElement>
}

function MessageList({ messages, messagesEndRef }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center">
          <div className="w-24 h-24 mx-auto mb-4 bg-gradient-to-br from-candy-200 to-sky-200 rounded-full flex items-center justify-center animate-bounce-slow">
            <span className="text-4xl">👋</span>
          </div>
          <h3 className="text-xl font-bold text-gray-700 mb-2">
            开始对话吧！
          </h3>
          <p className="text-gray-500">
            向小言问好，或者问任何你想知道的问题
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gradient-to-b from-sky-50/50 to-white">
      {messages.map((message) => (
        <div key={message.id}>
          <MessageBubble message={message} />
          {message.isStreaming && (
            <div className="ml-4 mt-2">
              <TypingIndicator />
            </div>
          )}
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  )
}

export default MessageList
