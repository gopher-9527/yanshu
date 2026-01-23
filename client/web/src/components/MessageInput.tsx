import { useState, useRef, useEffect } from 'react'
import { Send, Smile } from 'lucide-react'

interface MessageInputProps {
  onSendMessage: (text: string) => void
  isLoading: boolean
}

function MessageInput({ onSendMessage, isLoading }: MessageInputProps) {
  const [input, setInput] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim())
      setInput('')
      inputRef.current?.focus()
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <form onSubmit={handleSubmit} className="flex items-end space-x-3">
        <div className="flex-1 relative">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入你的消息..."
            className="input-field resize-none min-h-[50px] max-h-[120px]"
            rows={1}
            disabled={isLoading}
          />
          <button
            type="button"
            className="absolute right-3 bottom-3 text-gray-400 hover:text-candy-500 transition-colors"
            title="表情"
          >
            <Smile className="w-5 h-5" />
          </button>
        </div>
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="button-primary disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center space-x-2"
        >
          <Send className="w-5 h-5" />
          <span>发送</span>
        </button>
      </form>
      <p className="text-xs text-gray-400 mt-2 text-center">
        按 Enter 发送，Shift + Enter 换行
      </p>
    </div>
  )
}

export default MessageInput
