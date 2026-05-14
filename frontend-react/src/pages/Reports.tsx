import { useEffect, useMemo, useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { reportsApi, Report } from '@/services/reports'
import { Link } from 'react-router-dom'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import {
  Search,
  TrendingUp,
  TrendingDown,
  Minus,
  Calendar,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { clsx } from 'clsx'

const safeFormat = (val: unknown, pattern = 'MM/dd HH:mm'): string => {
  if (!val) return '--'
  const d = new Date(val as string | number)
  if (isNaN(d.getTime())) return '--'
  return format(d, pattern, { locale: zhCN })
}

const PAGE_SIZE_OPTIONS = [12, 24, 50]

export default function Reports() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(12)
  const searchKeyword = search.trim()

  const { data, isLoading, isFetching, isError } = useQuery({
    queryKey: ['reports-list', page, pageSize, searchKeyword],
    queryFn: () =>
      reportsApi.getList({
        page,
        page_size: pageSize,
        search_keyword: searchKeyword || undefined,
      }),
    placeholderData: keepPreviousData,
    retry: false,
  })

  const reports: Report[] = data?.reports || []
  const total = Number(data?.total || 0)
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const startIndex = total === 0 ? 0 : (page - 1) * pageSize + 1
  const endIndex = total === 0 ? 0 : Math.min(total, page * pageSize)

  const pageNumbers = useMemo(() => {
    const visiblePages = new Set<number>([1, totalPages, page - 1, page, page + 1])
    return Array.from(visiblePages)
      .filter((item) => item >= 1 && item <= totalPages)
      .sort((a, b) => a - b)
  }, [page, totalPages])

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages)
    }
  }, [page, totalPages])

  const getDirectionIcon = (direction?: string) => {
    if (direction === 'bullish') return <TrendingUp className="w-4 h-4 text-green-400" />
    if (direction === 'bearish') return <TrendingDown className="w-4 h-4 text-red-400" />
    return <Minus className="w-4 h-4 text-white/40" />
  }

  const getDirectionStyle = (direction?: string) => {
    if (direction === 'bullish') return 'border-green-500/20 hover:border-green-500/40'
    if (direction === 'bearish') return 'border-red-500/20 hover:border-red-500/40'
    return 'border-white/5 hover:border-white/10'
  }

  const getDirectionBadge = (direction?: string) => {
    if (direction === 'bullish') return 'bg-green-500/10 text-green-400 border-green-500/20'
    if (direction === 'bearish') return 'bg-red-500/10 text-red-400 border-red-500/20'
    return 'bg-white/5 text-white/60 border-white/10'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">结论报告</h1>
          <p className="text-white/40 mt-1">查看和管理分析报告</p>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
        <input
          type="text"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
          placeholder="搜索股票代码、名称或内容..."
          className="w-full pl-12 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50"
        />
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="text-sm text-white/40">
          {total > 0 ? (
            <>
              共 <span className="text-white/70">{total}</span> 份报告，当前显示 {startIndex}-{endIndex}
              {isFetching && !isLoading ? <span className="ml-2 text-blue-300">正在更新...</span> : null}
            </>
          ) : (
            <span>{searchKeyword ? '没有找到匹配报告' : '暂无报告数据'}</span>
          )}
        </div>
        <label className="flex items-center gap-2 text-sm text-white/50">
          每页
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value))
              setPage(1)
            }}
            className="h-9 rounded-lg border border-white/10 bg-white/5 px-3 text-white outline-none focus:border-blue-500/50"
          >
            {PAGE_SIZE_OPTIONS.map((size) => (
              <option key={size} value={size} className="bg-slate-900 text-white">
                {size}
              </option>
            ))}
          </select>
          条
        </label>
      </div>

      {/* Reports grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 9 }).map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-2xl" />
          ))}
        </div>
      ) : isError ? (
        <div className="text-center py-16">
          <div className="w-16 h-16 rounded-2xl bg-red-500/10 flex items-center justify-center mx-auto mb-4">
            <Search className="w-8 h-8 text-red-300/60" />
          </div>
          <p className="text-red-300/80">报告列表加载失败</p>
          <p className="text-white/20 text-sm mt-1">请检查登录状态或后端报告接口</p>
        </div>
      ) : reports.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4">
            <Search className="w-8 h-8 text-white/20" />
          </div>
          <p className="text-white/40">{searchKeyword ? '没有找到匹配报告' : '暂无报告'}</p>
          <p className="text-white/20 text-sm mt-1">
            {searchKeyword ? '请调整搜索关键词后重试' : '开始分析股票以生成报告'}
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {reports.map((report) => (
              <Link key={report.id} to={`/reports/${report.id}`}>
                <Card
                  className={clsx(
                    'gradient-card rounded-2xl p-5 border transition-all duration-300 hover:-translate-y-1 cursor-pointer',
                    getDirectionStyle(report.conclusion?.direction)
                  )}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      {getDirectionIcon(report.conclusion?.direction)}
                      <div>
                        <h3 className="text-white font-semibold">{report.stock_name}</h3>
                        <p className="text-white/40 text-sm">{report.stock_code}</p>
                      </div>
                    </div>
                    <span
                      className={clsx(
                        'px-3 py-1 rounded-full text-xs font-medium border',
                        getDirectionBadge(report.conclusion?.direction)
                      )}
                    >
                      {report.conclusion?.direction === 'bullish'
                        ? '看多'
                        : report.conclusion?.direction === 'bearish'
                        ? '看空'
                        : '中性'}
                    </span>
                  </div>

                  {report.conclusion?.summary && (
                    <p className="text-white/60 text-sm line-clamp-2 mb-4">
                      {report.conclusion.summary}
                    </p>
                  )}

                  <div className="flex items-center justify-between pt-4 border-t border-white/5">
                    <div className="flex items-center gap-2 text-white/40 text-sm">
                      <Calendar className="w-4 h-4" />
                      {safeFormat(report.created_at, 'yyyy-MM-dd HH:mm')}
                    </div>
                    <ArrowRight className="w-4 h-4 text-white/20" />
                  </div>
                </Card>
              </Link>
            ))}
          </div>

          <div className="flex flex-col gap-3 border-t border-white/5 pt-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-sm text-white/40">
              第 <span className="text-white/70">{page}</span> / {totalPages} 页
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                disabled={page <= 1}
                className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-white/70 transition hover:border-white/20 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="上一页"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>

              {pageNumbers.map((pageNumber, index) => {
                const previous = pageNumbers[index - 1]
                const showGap = previous && pageNumber - previous > 1

                return (
                  <div key={pageNumber} className="flex items-center gap-2">
                    {showGap ? <span className="px-1 text-white/30">...</span> : null}
                    <button
                      type="button"
                      onClick={() => setPage(pageNumber)}
                      className={clsx(
                        'h-9 min-w-9 rounded-lg border px-3 text-sm transition',
                        pageNumber === page
                          ? 'border-blue-500/50 bg-blue-500/20 text-blue-100'
                          : 'border-white/10 bg-white/5 text-white/60 hover:border-white/20 hover:bg-white/10'
                      )}
                    >
                      {pageNumber}
                    </button>
                  </div>
                )
              })}

              <button
                type="button"
                onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                disabled={page >= totalPages}
                className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-white/70 transition hover:border-white/20 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="下一页"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
