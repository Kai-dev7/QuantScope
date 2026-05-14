import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Star, Search, Plus, Trash2 } from 'lucide-react'

const mockFavorites = [
  { code: '600519', name: '贵州茅台', addedAt: '2024-01-15' },
  { code: '000858', name: '五粮液', addedAt: '2024-01-14' },
  { code: '002594', name: '比亚迪', addedAt: '2024-01-13' },
]

export default function Favorites() {
  const [favorites, setFavorites] = useState(mockFavorites)
  const [search, setSearch] = useState('')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">观察池</h1>
          <p className="text-white/40 mt-1">管理关注的股票</p>
        </div>
        <button className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-medium hover:opacity-90 flex items-center gap-2">
          <Plus className="w-4 h-4" />
          添加
        </button>
      </div>

      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="搜索..."
          className="w-full pl-12 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {favorites.map((fav) => (
          <Card
            key={fav.code}
            className="gradient-card rounded-2xl p-5 border border-white/5 hover:border-white/10 transition-all cursor-pointer group"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <Star className="w-5 h-5 text-amber-400 fill-amber-400" />
                <div>
                  <h3 className="text-white font-semibold">{fav.name}</h3>
                  <p className="text-white/40 text-sm">{fav.code}</p>
                </div>
              </div>
              <button
                onClick={() => setFavorites(favorites.filter((f) => f.code !== fav.code))}
                className="p-2 rounded-lg hover:bg-red-500/10 text-white/40 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
            <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between text-sm">
              <span className="text-white/40">添加于 {fav.addedAt}</span>
              <button className="text-blue-400 hover:text-blue-300">分析 →</button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
