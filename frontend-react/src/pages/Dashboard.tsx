import { useQuery } from '@tanstack/react-query'
import { analysisApi, AnalysisTask } from '@/services/analysis'
import { reportsApi, Report } from '@/services/reports'
import { marketApi } from '@/services/market'
import StockChart from '@/components/Charts/StockChart'
import { AgentCollaboration } from '@/components/Agent/AgentCollaboration'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'

const safeFormat = (val: unknown, pattern = 'MM/dd HH:mm'): string => {
  if (!val) return '--'
  const d = new Date(val as string | number)
  if (isNaN(d.getTime())) return '--'
  return format(d, pattern, { locale: zhCN })
}
import {
  TrendingUp,
  Clock,
  CheckCircle2,
  ArrowRight,
  Activity,
  RefreshCw,
  Search,
  XCircle as XCircleAlt,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useState } from 'react'

// ============================================================
// Market Overview 组件 - 简单指数展示
// ============================================================
function MarketOverview() {
  const { data: overviewData, isError, isFetching, refetch } = useQuery({
    queryKey: ['market-overview'],
    queryFn: () => marketApi.getOverview(),
    enabled: false,
    retry: false,
  })

  const indices = overviewData?.indices || []

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-2">
        <Activity className="w-4 h-4 text-cyan-400" />
        <span className="text-white text-sm font-medium">市场概览</span>
        <button
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
          className="ml-auto inline-flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-white/60 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="刷新市场概览"
        >
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
        </button>
        {overviewData?.updated_at && !isNaN(Date.parse(overviewData.updated_at)) && (
          <span className="text-white/30 text-xs">
            {safeFormat(overviewData.updated_at, 'HH:mm')}
          </span>
        )}
      </div>
      {indices.length > 0 ? (
        <div className="grid grid-cols-2 gap-2">
          {indices.map(idx => (
            <div key={idx.code} className="bg-white/5 rounded-xl p-3 border border-white/5">
              <p className="text-white/50 text-xs">{idx.name}</p>
              <p className="text-white font-semibold text-lg mt-0.5">{idx.price.toFixed(2)}</p>
              <p className={`text-xs mt-0.5 ${idx.up ? 'text-green-400' : 'text-red-400'}`}>
                {idx.change >= 0 ? '+' : ''}{idx.change.toFixed(2)}% {idx.up ? '▲' : '▼'}
              </p>
            </div>
          ))}
        </div>
      ) : isFetching ? (
        <div className="text-center py-4 text-white/30 text-sm">正在加载市场数据...</div>
      ) : isError ? (
        <div className="text-center py-4 text-red-300/70 text-sm">市场数据加载失败</div>
      ) : (
        <div className="text-center py-4 text-white/30 text-sm">点击刷新加载市场概览</div>
      )}
    </div>
  )
}

// ============================================================
// Recent Tasks 组件
// ============================================================
function RecentTasks({
  tasks,
  loading,
  error,
}: {
  tasks: AnalysisTask[]
  loading: boolean
  error?: boolean
}) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full" />
        ))}
      </div>
    )
  }

  if (error) {
    return <div className="text-center py-8 text-red-300/70">任务数据加载失败</div>
  }

  if (tasks.length === 0) {
    return <div className="text-center py-8 text-white/40">暂无任务记录</div>
  }

  return (
    <div className="space-y-2">
      {tasks.map(task => (
        <Link
          key={task.task_id}
          to={`/reports/${task.task_id}`}
          className="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className={`status-dot ${
              task.status === 'running' ? 'running' :
              task.status === 'completed' ? 'success' : 'failed'
            }`} />
            <div>
              <p className="text-white font-medium">{task.stock_name}</p>
              <p className="text-white/40 text-sm">{task.stock_code}</p>
            </div>
          </div>
          <div className="text-right">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              task.status === 'completed' ? 'bg-green-500/20 text-green-400' :
              task.status === 'failed' ? 'bg-red-500/20 text-red-400' :
              task.status === 'running' ? 'bg-blue-500/20 text-blue-400' :
              'bg-white/10 text-white/60'
            }`}>
              {task.status === 'completed' ? '已完成' :
               task.status === 'failed' ? '失败' :
               task.status === 'running' ? '运行中' : '等待中'}
            </span>
            <p className="text-white/30 text-xs mt-1">
              {safeFormat(task.created_at)}
            </p>
          </div>
        </Link>
      ))}
    </div>
  )
}

// ============================================================
// Recent Reports 组件
// ============================================================
function ReportSummary({
  reports,
  total,
  loading,
  error,
}: {
  reports: Report[]
  total: number
  loading: boolean
  error?: boolean
}) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full" />
        ))}
      </div>
    )
  }

  if (error) {
    return <div className="text-center py-8 text-red-300/70">研报数据加载失败</div>
  }

  if (reports.length === 0) {
    return <div className="text-center py-8 text-white/40">暂无研报产出</div>
  }

  const bullish = reports.filter((report) => report.conclusion?.direction === 'bullish').length
  const bearish = reports.filter((report) => report.conclusion?.direction === 'bearish').length
  const latest = reports[0]

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-xl border border-white/5 bg-white/5 p-3">
          <p className="text-xs text-white/40">总研报</p>
          <p className="mt-1 text-2xl font-semibold text-white">{total}</p>
        </div>
        <div className="rounded-xl border border-green-500/10 bg-green-500/5 p-3">
          <p className="text-xs text-green-300/60">近期看多</p>
          <p className="mt-1 text-2xl font-semibold text-green-300">{bullish}</p>
        </div>
        <div className="rounded-xl border border-red-500/10 bg-red-500/5 p-3">
          <p className="text-xs text-red-300/60">近期看空</p>
          <p className="mt-1 text-2xl font-semibold text-red-300">{bearish}</p>
        </div>
      </div>

      <Link
        to={`/reports/${latest.id}`}
        className="flex items-center justify-between rounded-xl bg-white/5 p-3 transition-colors hover:bg-white/10"
      >
        <div>
          <p className="font-medium text-white">最新：{latest.stock_name}</p>
          <p className="mt-1 text-sm text-white/40">{latest.stock_code} · {safeFormat(latest.created_at)}</p>
        </div>
        <ArrowRight className="h-4 w-4 text-white/30" />
      </Link>
    </div>
  )
}

// ============================================================
// Main Dashboard
// ============================================================
export default function Dashboard() {
  console.log('Dashboard V2 rendering!')

  const [stockSymbol, setStockSymbol] = useState('')
  const [klineSymbol, setKlineSymbol] = useState('')

  const { data: dashboardStats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => analysisApi.getDashboardStats(),
    refetchInterval: 30000,
    retry: false,
  })

  const { data: tasksData, isLoading: tasksLoading, isError: tasksError } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => analysisApi.getTasks({ page_size: 20 }),
    refetchInterval: 15000,
    retry: false,
  })

  const { data: reportsData, isLoading: reportsLoading, isError: reportsError } = useQuery({
    queryKey: ['dashboard-reports'],
    queryFn: () => reportsApi.getList({ page: 1, page_size: 5 }),
    retry: false,
  })

  const { data: klineData, isLoading: klineLoading } = useQuery({
    queryKey: ['kline', klineSymbol],
    queryFn: () => marketApi.getKLine(klineSymbol, { limit: 60 }),
    enabled: klineSymbol.length >= 6,
    retry: false,
  })

  const tasks: AnalysisTask[] = tasksData?.tasks || []
  const reports: Report[] = reportsData?.reports || []

  // 找到最新运行中的任务（用于Pipeline展示）
  const runningTask = tasks.find(t => t.status === 'running') || null

  // 统计数据
  const stats = [
    { title: '总分析次数', value: dashboardStats?.total_analyses || 0, color: 'blue', loading: statsLoading },
    { title: '成功分析', value: dashboardStats?.successful_analyses || 0, color: 'green', loading: statsLoading },
    { title: '失败分析', value: dashboardStats?.failed_analyses || 0, color: 'red', loading: statsLoading },
    { title: '研报数量', value: dashboardStats?.report_count || 0, color: 'purple', loading: statsLoading },
  ]

  const colorMap: Record<string, string> = {
    blue: 'from-blue-500/20 to-blue-500/5 border-blue-500/20',
    green: 'from-green-500/20 to-green-500/5 border-green-500/20',
    red: 'from-red-500/20 to-red-500/5 border-red-500/20',
    purple: 'from-purple-500/20 to-purple-500/5 border-purple-500/20',
  }

  const iconColorMap: Record<string, string> = {
    blue: 'text-blue-400',
    green: 'text-green-400',
    red: 'text-red-400',
    purple: 'text-purple-400',
  }

  const iconMap: Record<string, any> = {
    blue: Activity,
    green: CheckCircle2,
    red: XCircleAlt,
    purple: TrendingUp,
  }

  return (
    <div className="space-y-6">
      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map(stat => {
          const Icon = iconMap[stat.color]
          return (
            <div
              key={stat.title}
              className={`relative overflow-hidden rounded-2xl p-5 bg-gradient-to-br ${colorMap[stat.color]} border`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/60 text-sm">{stat.title}</p>
                  {stat.loading ? (
                    <Skeleton className="h-8 w-20 mt-1" />
                  ) : (
                    <p className="text-3xl font-bold text-white mt-1">{stat.value}</p>
                  )}
                </div>
                <div className={`p-3 rounded-xl bg-white/5 ${iconColorMap[stat.color]}`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Main content: Pipeline + Market Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Pipeline - takes 2 columns */}
        <Card className="gradient-card border-white/5 lg:col-span-2">
          <CardContent className="p-5">
            <AgentCollaboration task={runningTask} />
          </CardContent>
        </Card>

        {/* Right column: Market Overview */}
        <Card className="gradient-card border-white/5">
          <CardContent className="p-5">
            <MarketOverview />
          </CardContent>
        </Card>
      </div>

      {/* K线图 */}
      <Card className="gradient-card border-white/5">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-yellow-400" />
            K线行情
          </CardTitle>
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="股票代码 (如 000001)"
              value={stockSymbol}
              onChange={e => setStockSymbol(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  setKlineSymbol(stockSymbol.trim())
                }
              }}
              className="bg-white/5 border border-white/10 rounded px-3 py-1.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50 w-40"
            />
            <button
              type="button"
              onClick={() => setKlineSymbol(stockSymbol.trim())}
              disabled={stockSymbol.trim().length < 6 || klineLoading}
              className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-white/60 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="查询K线行情"
            >
              <Search className="h-4 w-4" />
            </button>
            <span className="text-xs text-white/40">{klineData?.name || klineData?.symbol || '—'}</span>
          </div>
        </CardHeader>
        <CardContent>
          {klineLoading ? (
            <div className="h-80 flex items-center justify-center">
              <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
            </div>
          ) : klineData?.records && klineData.records.length > 0 ? (
            <StockChart
              symbol={klineData.symbol}
              stockName={klineData.name}
              records={klineData.records}
              height={340}
            />
          ) : (
            <div className="h-80 flex items-center justify-center text-white/30">
              输入股票代码后按 Enter 或点击查询
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent tasks and report summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="gradient-card border-white/5">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-blue-400" />
              最近任务
            </CardTitle>
            <Link to="/tasks" className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1">
              查看全部 <ArrowRight className="w-4 h-4" />
            </Link>
          </CardHeader>
          <CardContent>
            <RecentTasks tasks={tasks.slice(0, 5)} loading={tasksLoading} error={tasksError} />
          </CardContent>
        </Card>

        <Card className="gradient-card border-white/5">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-400" />
              研报概览
            </CardTitle>
            <Link to="/reports" className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1">
              查看全部 <ArrowRight className="w-4 h-4" />
            </Link>
          </CardHeader>
          <CardContent>
            <ReportSummary
              reports={reports}
              total={reportsData?.total || 0}
              loading={reportsLoading}
              error={reportsError}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
