import { MessageCircle, Heart } from 'lucide-react'

function Header() {
  return (
    <header className="bg-white/80 backdrop-blur-sm shadow-sm border-b border-sky-100">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-candy-400 to-sky-400 rounded-full flex items-center justify-center animate-pulse-slow">
            <MessageCircle className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-800">小言助手</h1>
            <p className="text-xs text-gray-500">你的智能小伙伴</p>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-candy-500">
          <Heart className="w-5 h-5 animate-pulse" />
          <span className="text-sm font-semibold">在线</span>
        </div>
      </div>
    </header>
  )
}

export default Header
