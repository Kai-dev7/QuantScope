import { NavLink, useLocation } from 'react-router-dom'
import { toast } from 'sonner'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import {
  LayoutDashboard,
  BarChart3,
  ListTodo,
  Star,
  CalendarClock,
  Settings,
  Info,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Zap,
} from 'lucide-react'
import { clsx } from 'clsx'

const navItems = [
  { path: '/dashboard', label: '作战总览', icon: LayoutDashboard },
  { path: '/analysis', label: '策略工位', icon: BarChart3 },
  { path: '/reports', label: '结论报告', icon: ListTodo },
  { path: '/tasks', label: '任务队列', icon: ListTodo },
  { path: '/watchlist-schedule', label: '自选 & 定时', icon: CalendarClock },
  { path: '/favorites', label: '观察池', icon: Star },
]

const bottomItems = [
  { path: '/settings', label: '系统设置', icon: Settings },
  { path: '/about', label: '产品说明', icon: Info },
]

export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useAppStore()
  const { logout } = useAuthStore()
  const location = useLocation()

  return (
    <aside
      className={clsx(
        'fixed left-0 top-0 h-screen flex flex-col z-50 transition-all duration-300',
        'bg-gradient-to-b from-[#111827] via-[#0d1117] to-[#111827]',
        'border-r border-white/5',
        'before:absolute before:inset-0 before:pointer-events-none before:bg-gradient-to-b before:from-blue-500/5 before:to-transparent',
        sidebarCollapsed ? 'w-[72px]' : 'w-[260px]'
      )}
    >
      {/* Logo */}
      <div className="relative flex items-center gap-3 px-5 h-[72px] border-b border-white/5">
        <div className="relative flex-shrink-0">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-cyan-400 rounded-xl blur opacity-30" />
        </div>
        {!sidebarCollapsed && (
          <div className="flex flex-col">
            <span className="text-white font-bold text-lg tracking-tight">QuantScope</span>
            <span className="text-white/40 text-[10px] uppercase tracking-widest">AI Research</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative',
                isActive || location.pathname.startsWith(item.path)
                  ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/10 text-white border border-blue-500/30'
                  : 'text-white/50 hover:text-white hover:bg-white/5'
              )
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 bg-gradient-to-b from-blue-500 to-cyan-400 rounded-r-full" />
                )}
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!sidebarCollapsed && (
                  <span className="text-sm font-medium">{item.label}</span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom section */}
      <div className="border-t border-white/5 py-4 px-3 space-y-1">
        {bottomItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200',
                isActive
                  ? 'bg-white/10 text-white'
                  : 'text-white/50 hover:text-white hover:bg-white/5'
              )
            }
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            {!sidebarCollapsed && (
              <span className="text-sm font-medium">{item.label}</span>
            )}
          </NavLink>
        ))}

        {/* Logout */}
        <button
          onClick={() => {
            toast.success('已退出登录')
            logout()
          }}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 text-white/50 hover:text-red-400 hover:bg-red-500/10"
        >
          <LogOut className="w-5 h-5 flex-shrink-0" />
          {!sidebarCollapsed && (
            <span className="text-sm font-medium">退出登录</span>
          )}
        </button>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-[84px] w-6 h-6 rounded-full bg-[#1e293b] border border-white/10 flex items-center justify-center text-white/40 hover:text-white hover:bg-[#334155] transition-all shadow-lg"
      >
        {sidebarCollapsed ? (
          <ChevronRight className="w-3 h-3" />
        ) : (
          <ChevronLeft className="w-3 h-3" />
        )}
      </button>
    </aside>
  )
}
