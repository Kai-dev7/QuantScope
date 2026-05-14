import { useLocation } from 'react-router-dom'
import { Bell, RefreshCw } from 'lucide-react'

const routeTitles: Record<string, string> = {
  '/dashboard': '作战总览',
  '/analysis': '策略工位',
  '/reports': '结论报告',
  '/tasks': '任务队列',
  '/favorites': '观察池',
  '/watchlist-schedule': '自选 & 定时分析',
  '/settings': '系统设置',
  '/about': '产品说明',
}

export default function Header() {
  const location = useLocation()
  const title = routeTitles[location.pathname] || 'QuantScope'

  return (
    <header className="sticky top-0 z-40 h-[72px] bg-[#0a0e17]/80 backdrop-blur-xl border-b border-white/5 flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-white">{title}</h1>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
            LIVE
          </span>
          <span className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full bg-white/5 text-white/60 border border-white/10">
            CN / HK / US
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button className="relative w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-white/60 hover:text-white hover:bg-white/10 transition-all">
          <RefreshCw className="w-4 h-4" />
        </button>
        <button className="relative w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-white/60 hover:text-white hover:bg-white/10 transition-all">
          <Bell className="w-4 h-4" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-blue-500 rounded-full" />
        </button>
      </div>
    </header>
  )
}
