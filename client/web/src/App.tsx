import Header from './components/Header'
import ChatInterface from './components/ChatInterface'
import { Sparkles } from 'lucide-react'

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-4xl">
          <div className="text-center mb-8">
            <div className="inline-flex items-center space-x-3 mb-4 animate-float">
              <Sparkles className="w-8 h-8 text-candy-500" />
              <h1 className="text-4xl font-bold bg-gradient-to-r from-candy-500 to-sky-500 bg-clip-text text-transparent">
                小言助手
              </h1>
              <Sparkles className="w-8 h-8 text-sky-500" />
            </div>
            <p className="text-gray-600 text-lg">
              你好！我是小言，你的智能小伙伴 🌟
            </p>
          </div>
          <ChatInterface />
        </div>
      </main>
      <footer className="text-center py-4 text-gray-500 text-sm">
        <p>💝 小言助手 - 让对话更有趣</p>
      </footer>
    </div>
  )
}

export default App
