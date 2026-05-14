import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import {
  BarChart3,
  CalendarClock,
  Play,
  Plus,
  Search,
  Star,
  Trash2,
} from 'lucide-react'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { clsx } from 'clsx'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { favoritesApi, FavoriteStock } from '@/services/favorites'
import {
  scheduledAnalysisApi,
  ScheduledAnalysisPlan,
  ScheduledAnalysisPayload,
} from '@/services/scheduledAnalysis'

const safeFormat = (val: unknown, pattern = 'yyyy-MM-dd HH:mm') => {
  if (!val) return '--'
  const date = new Date(val as string | number)
  if (Number.isNaN(date.getTime())) return '--'
  return format(date, pattern, { locale: zhCN })
}

const WEEKDAY_LABELS = ['一', '二', '三', '四', '五', '六', '日']

const frequencyLabel: Record<ScheduledAnalysisPlan['frequency'], string> = {
  daily: '每日',
  weekly: '每周',
  monthly: '每月',
}

export default function WatchlistSchedule() {
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<'watchlist' | 'schedule'>('watchlist')
  const [recentlyCreated, setRecentlyCreated] = useState(false)
  const [search, setSearch] = useState('')
  const [form, setForm] = useState({
    stock_code: '',
    stock_name: '',
    market: 'A股',
    notes: '',
  })
  const [scheduleForm, setScheduleForm] = useState<ScheduledAnalysisPayload>({
    stock_code: '',
    stock_name: '',
    market_type: 'A股',
    frequency: 'daily',
    run_time: '16:00',
    weekdays: [1, 2, 3, 4, 5],
    research_depth: '标准',
    enabled: true,
    notes: '',
  })

  const {
    data: favorites = [],
    isLoading: favoritesLoading,
    isError: favoritesError,
  } = useQuery({
    queryKey: ['favorites'],
    queryFn: favoritesApi.getList,
    retry: false,
  })

  const {
    data: plans = [],
    isLoading: plansLoading,
    isError: plansError,
  } = useQuery({
    queryKey: ['scheduled-analysis-plans'],
    queryFn: scheduledAnalysisApi.getList,
    retry: false,
    enabled: tab === 'schedule',
  })

  const addFavorite = useMutation({
    mutationFn: favoritesApi.add,
    onSuccess: () => {
      toast.success('已加入自选')
      setForm({ stock_code: '', stock_name: '', market: 'A股', notes: '' })
      queryClient.invalidateQueries({ queryKey: ['favorites'] })
    },
    onError: () => toast.error('添加自选失败'),
  })

  const removeFavorite = useMutation({
    mutationFn: favoritesApi.remove,
    onSuccess: () => {
      toast.success('已移除自选')
      queryClient.invalidateQueries({ queryKey: ['favorites'] })
    },
    onError: () => toast.error('移除自选失败'),
  })

  const createPlan = useMutation({
    mutationFn: scheduledAnalysisApi.create,
    onSuccess: async () => {
      toast.success('股票定时分析计划已创建')
      setRecentlyCreated(true)
      setScheduleForm({
        stock_code: '',
        stock_name: '',
        market_type: 'A股',
        frequency: 'daily',
        run_time: '16:00',
        weekdays: [1, 2, 3, 4, 5],
        research_depth: '标准',
        enabled: true,
        notes: '',
      })
      await queryClient.invalidateQueries({ queryKey: ['scheduled-analysis-plans'] })
      window.setTimeout(() => setRecentlyCreated(false), 4000)
    },
    onError: (error: any) => toast.error(error.response?.data?.detail || '创建计划失败'),
  })

  const updatePlan = useMutation({
    mutationFn: ({ planId, payload }: { planId: string; payload: Partial<ScheduledAnalysisPayload> }) =>
      scheduledAnalysisApi.update(planId, payload),
    onSuccess: () => {
      toast.success('计划已更新')
      queryClient.invalidateQueries({ queryKey: ['scheduled-analysis-plans'] })
    },
    onError: () => toast.error('更新计划失败'),
  })

  const deletePlan = useMutation({
    mutationFn: scheduledAnalysisApi.remove,
    onSuccess: () => {
      toast.success('计划已删除')
      queryClient.invalidateQueries({ queryKey: ['scheduled-analysis-plans'] })
    },
    onError: () => toast.error('删除计划失败'),
  })

  const runPlan = useMutation({
    mutationFn: scheduledAnalysisApi.runNow,
    onSuccess: () => {
      toast.success('已提交分析任务')
      queryClient.invalidateQueries({ queryKey: ['scheduled-analysis-plans'] })
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
    onError: () => toast.error('提交分析任务失败'),
  })

  const filteredFavorites = useMemo(() => {
    const keyword = search.trim().toLowerCase()
    if (!keyword) return favorites
    return favorites.filter((item) =>
      [item.stock_code, item.stock_name, item.market, item.notes]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(keyword))
    )
  }, [favorites, search])

  const submitFavorite = () => {
    const stockCode = form.stock_code.trim()
    if (!stockCode) {
      toast.error('请输入股票代码')
      return
    }
    addFavorite.mutate({
      stock_code: stockCode,
      stock_name: form.stock_name.trim() || stockCode,
      market: form.market,
      notes: form.notes.trim(),
    })
  }

  const submitPlan = () => {
    const stockCode = scheduleForm.stock_code.trim()
    if (!stockCode) {
      toast.error('请输入股票代码')
      return
    }
    createPlan.mutate({
      ...scheduleForm,
      stock_code: stockCode,
      stock_name: scheduleForm.stock_name.trim() || stockCode,
      notes: scheduleForm.notes?.trim() || '',
    })
  }

  const toggleWeekday = (day: number) => {
    setScheduleForm((current) => ({
      ...current,
      weekdays: current.weekdays.includes(day)
        ? current.weekdays.filter((item) => item !== day)
        : [...current.weekdays, day].sort((a, b) => a - b),
    }))
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">自选 & 定时分析</h1>
          <p className="text-white/40 mt-1">维护关注股票，并配置股票分析计划</p>
        </div>
        <div className="inline-flex rounded-xl border border-white/10 bg-white/5 p-1">
          <button
            type="button"
            onClick={() => setTab('watchlist')}
            className={clsx(
              'inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm transition',
              tab === 'watchlist' ? 'bg-blue-500/20 text-blue-100' : 'text-white/50 hover:text-white'
            )}
          >
            <Star className="h-4 w-4" />
            自选池
          </button>
          <button
            type="button"
            onClick={() => setTab('schedule')}
            className={clsx(
              'inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm transition',
              tab === 'schedule' ? 'bg-blue-500/20 text-blue-100' : 'text-white/50 hover:text-white'
            )}
          >
            <CalendarClock className="h-4 w-4" />
            定时分析
          </button>
        </div>
      </div>

      {tab === 'watchlist' ? (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[360px_1fr]">
          <Card className="gradient-card border-white/5 p-5">
            <h2 className="text-white font-semibold mb-4">添加自选</h2>
            <div className="space-y-3">
              <input
                value={form.stock_code}
                onChange={(e) => setForm((current) => ({ ...current, stock_code: e.target.value }))}
                placeholder="股票代码，例如 600519"
                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder-white/30 outline-none focus:border-blue-500/50"
              />
              <input
                value={form.stock_name}
                onChange={(e) => setForm((current) => ({ ...current, stock_name: e.target.value }))}
                placeholder="股票名称，可选"
                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder-white/30 outline-none focus:border-blue-500/50"
              />
              <select
                value={form.market}
                onChange={(e) => setForm((current) => ({ ...current, market: e.target.value }))}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none focus:border-blue-500/50"
              >
                <option className="bg-slate-900" value="A股">A股</option>
                <option className="bg-slate-900" value="港股">港股</option>
                <option className="bg-slate-900" value="美股">美股</option>
              </select>
              <textarea
                value={form.notes}
                onChange={(e) => setForm((current) => ({ ...current, notes: e.target.value }))}
                placeholder="关注理由或备注"
                rows={4}
                className="w-full resize-none rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder-white/30 outline-none focus:border-blue-500/50"
              />
              <button
                type="button"
                onClick={submitFavorite}
                disabled={addFavorite.isPending}
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 px-4 py-3 font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Plus className="h-4 w-4" />
                添加到自选
              </button>
            </div>
          </Card>

          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-white/40" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="搜索股票代码、名称、市场或备注..."
                className="w-full rounded-xl border border-white/10 bg-white/5 py-3 pl-12 pr-4 text-white placeholder-white/30 outline-none focus:border-blue-500/50"
              />
            </div>

            {favoritesLoading ? (
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                {Array.from({ length: 4 }).map((_, index) => (
                  <Skeleton key={index} className="h-36 rounded-2xl" />
                ))}
              </div>
            ) : favoritesError ? (
              <div className="rounded-2xl border border-red-500/10 bg-red-500/5 p-8 text-center text-red-300/80">
                自选股加载失败
              </div>
            ) : filteredFavorites.length === 0 ? (
              <div className="rounded-2xl border border-white/5 bg-white/[0.03] p-8 text-center text-white/40">
                暂无自选股
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                {filteredFavorites.map((item: FavoriteStock) => (
                  <Card key={item.stock_code} className="gradient-card border-white/5 p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <Star className="h-5 w-5 fill-amber-400 text-amber-400" />
                        <div>
                          <h3 className="font-semibold text-white">{item.stock_name || item.stock_code}</h3>
                          <p className="text-sm text-white/40">{item.stock_code} · {item.market || 'A股'}</p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeFavorite.mutate(item.stock_code)}
                        className="rounded-lg p-2 text-white/40 transition hover:bg-red-500/10 hover:text-red-300"
                        aria-label="移除自选"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                    {item.notes ? <p className="mt-4 line-clamp-2 text-sm text-white/55">{item.notes}</p> : null}
                    <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-4 text-sm">
                      <span className="text-white/30">添加于 {safeFormat(item.added_at, 'yyyy-MM-dd')}</span>
                      <Link to="/analysis" className="inline-flex items-center gap-1 text-blue-300 hover:text-blue-200">
                        分析 <BarChart3 className="h-4 w-4" />
                      </Link>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[360px_1fr]">
          <Card className="gradient-card border-white/5 p-5">
            <h2 className="mb-4 font-semibold text-white">新建股票定时分析</h2>
            <div className="space-y-3">
              <input
                value={scheduleForm.stock_code}
                onChange={(e) => setScheduleForm((current) => ({ ...current, stock_code: e.target.value }))}
                placeholder="股票代码，例如 600519"
                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder-white/30 outline-none focus:border-blue-500/50"
              />
              <input
                value={scheduleForm.stock_name}
                onChange={(e) => setScheduleForm((current) => ({ ...current, stock_name: e.target.value }))}
                placeholder="股票名称，可选"
                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder-white/30 outline-none focus:border-blue-500/50"
              />
              <div className="grid grid-cols-2 gap-3">
                <select
                  value={scheduleForm.market_type}
                  onChange={(e) => setScheduleForm((current) => ({ ...current, market_type: e.target.value }))}
                  className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none focus:border-blue-500/50"
                >
                  <option className="bg-slate-900" value="A股">A股</option>
                  <option className="bg-slate-900" value="港股">港股</option>
                  <option className="bg-slate-900" value="美股">美股</option>
                </select>
                <select
                  value={scheduleForm.research_depth}
                  onChange={(e) => setScheduleForm((current) => ({ ...current, research_depth: e.target.value }))}
                  className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none focus:border-blue-500/50"
                >
                  <option className="bg-slate-900" value="快速">快速</option>
                  <option className="bg-slate-900" value="基础">基础</option>
                  <option className="bg-slate-900" value="标准">标准</option>
                  <option className="bg-slate-900" value="深度">深度</option>
                  <option className="bg-slate-900" value="全面">全面</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <select
                  value={scheduleForm.frequency}
                  onChange={(e) => setScheduleForm((current) => ({ ...current, frequency: e.target.value as ScheduledAnalysisPlan['frequency'] }))}
                  className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none focus:border-blue-500/50"
                >
                  <option className="bg-slate-900" value="daily">每日</option>
                  <option className="bg-slate-900" value="weekly">每周</option>
                  <option className="bg-slate-900" value="monthly">每月</option>
                </select>
                <input
                  type="time"
                  value={scheduleForm.run_time}
                  onChange={(e) => setScheduleForm((current) => ({ ...current, run_time: e.target.value }))}
                  className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none focus:border-blue-500/50"
                />
              </div>
              <div>
                <p className="mb-2 text-sm text-white/50">交易日</p>
                <div className="grid grid-cols-7 gap-2">
                  {WEEKDAY_LABELS.map((label, index) => {
                    const day = index + 1
                    const active = scheduleForm.weekdays.includes(day)
                    return (
                      <button
                        type="button"
                        key={day}
                        onClick={() => toggleWeekday(day)}
                        className={clsx(
                          'h-9 rounded-lg border text-sm transition',
                          active
                            ? 'border-blue-500/50 bg-blue-500/20 text-blue-100'
                            : 'border-white/10 bg-white/5 text-white/45 hover:text-white'
                        )}
                      >
                        {label}
                      </button>
                    )
                  })}
                </div>
              </div>
              <textarea
                value={scheduleForm.notes}
                onChange={(e) => setScheduleForm((current) => ({ ...current, notes: e.target.value }))}
                placeholder="计划备注"
                rows={3}
                className="w-full resize-none rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder-white/30 outline-none focus:border-blue-500/50"
              />
              <button
                type="button"
                onClick={submitPlan}
                disabled={createPlan.isPending}
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 px-4 py-3 font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Plus className="h-4 w-4" />
                {createPlan.isPending ? '正在创建...' : '创建分析计划'}
              </button>
              {createPlan.isSuccess && recentlyCreated ? (
                <p className="rounded-xl border border-green-500/20 bg-green-500/10 px-4 py-3 text-sm text-green-300">
                  计划已创建，右侧列表已刷新。
                </p>
              ) : null}
            </div>
          </Card>

          <Card className="gradient-card border-white/5 p-5">
            <div className="mb-4">
              <h2 className="font-semibold text-white">股票分析计划 <span className="text-white/35 text-sm font-normal">({plans.length})</span></h2>
              <p className="mt-1 text-sm text-white/40">这里仅展示股票分析计划；系统级任务已移至系统设置</p>
            </div>
            {plansLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, index) => (
                  <Skeleton key={index} className="h-20 rounded-xl" />
                ))}
              </div>
            ) : plansError ? (
              <div className="rounded-2xl border border-red-500/10 bg-red-500/5 p-8 text-center text-red-300/80">
                股票分析计划加载失败
              </div>
            ) : plans.length === 0 ? (
              <div className="rounded-2xl border border-white/5 bg-white/[0.03] p-8 text-center text-white/40">
                暂无股票定时分析计划
              </div>
            ) : (
              <div className="divide-y divide-white/5">
                {plans.map((plan) => {
                return (
                  <div key={plan.plan_id} className="flex flex-col gap-3 py-4 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                      <div className="flex items-center gap-3">
                        <h3 className="font-medium text-white">{plan.stock_name || plan.stock_code}</h3>
                        <span
                          className={clsx(
                            'rounded-full border px-2 py-0.5 text-xs',
                            plan.enabled
                              ? 'border-green-500/20 bg-green-500/10 text-green-300'
                              : 'border-white/10 bg-white/5 text-white/40'
                          )}
                        >
                          {plan.enabled ? '启用' : '停用'}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-white/40">
                        {plan.stock_code} · {plan.market_type} · {frequencyLabel[plan.frequency]} {plan.run_time} · {plan.research_depth}
                      </p>
                      <p className="mt-1 text-xs text-white/30">
                        最近运行：{safeFormat(plan.last_run_at)}
                        {plan.last_task_id ? ` · 任务 ${plan.last_task_id.slice(0, 8)}` : ''}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => runPlan.mutate(plan.plan_id)}
                        className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/70 transition hover:bg-white/10"
                      >
                        <Play className="h-4 w-4" />
                        立即运行
                      </button>
                      <button
                        type="button"
                        onClick={() => updatePlan.mutate({ planId: plan.plan_id, payload: { enabled: !plan.enabled } })}
                        className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/70 transition hover:bg-white/10"
                      >
                        {plan.enabled ? '停用' : '启用'}
                      </button>
                      <button
                        type="button"
                        onClick={() => deletePlan.mutate(plan.plan_id)}
                        className="inline-flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-300 transition hover:bg-red-500/20"
                      >
                        <Trash2 className="h-4 w-4" />
                        删除
                      </button>
                    </div>
                  </div>
                )
              })}
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
