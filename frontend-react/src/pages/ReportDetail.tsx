import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { reportsApi, ReportDetail as ReportDetailType } from '@/services/reports'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const safeFormat = (val: unknown, pattern = 'MM/dd HH:mm'): string => {
  if (!val) return '--'
  const d = new Date(val as string | number)
  if (isNaN(d.getTime())) return '--'
  return format(d, pattern, { locale: zhCN })
}
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Minus,
  BarChart3,
  Shield,
  Download,
  ChevronDown,
  ChevronRight,
  FileText,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { clsx } from 'clsx'
import { useState } from 'react'

const REPORT_SECTIONS = [
  { key: 'market_report', title: '市场分析报告', icon: BarChart3 },
  { key: 'fundamentals_report', title: '基本面分析报告', icon: TrendingUp },
  { key: 'news_report', title: '新闻分析报告', icon: FileText },
  { key: 'sentiment_report', title: '舆情分析报告', icon: FileText },
  { key: 'bull_researcher', title: '看涨研究员观点', icon: TrendingUp },
  { key: 'bear_researcher', title: '看跌研究员观点', icon: TrendingDown },
  { key: 'research_team_decision', title: '研究团队决策', icon: FileText },
  { key: 'investment_plan', title: '投资计划', icon: FileText },
  { key: 'trader_investment_plan', title: '交易员计划', icon: FileText },
  { key: 'risky_analyst', title: '激进风险评估', icon: Shield },
  { key: 'safe_analyst', title: '保守风险评估', icon: Shield },
  { key: 'neutral_analyst', title: '中性风险评估', icon: Shield },
  { key: 'risk_management_decision', title: '风险管理决策', icon: Shield },
  { key: 'final_trade_decision', title: '最终交易决策', icon: FileText },
  { key: 'detailed_analysis', title: '详细分析', icon: FileText },
]

const SECTION_TITLE_FALLBACK: Record<string, string> = {
  market_report: '市场分析报告',
  fundamentals_report: '基本面分析报告',
  news_report: '新闻分析报告',
  sentiment_report: '舆情分析报告',
  investment_plan: '投资计划',
  trader_investment_plan: '交易员计划',
  final_trade_decision: '最终交易决策',
}

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export default function ReportDetail() {
  const { id } = useParams<{ id: string }>()
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())
  const { data: report, isLoading } = useQuery({
    queryKey: ['report', id],
    queryFn: () => reportsApi.getDetail(id!),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-48 w-full rounded-2xl" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    )
  }

  if (!report) {
    return (
      <div className="text-center py-16">
        <p className="text-white/40">报告不存在</p>
        <Link to="/reports" className="text-blue-400 hover:text-blue-300 mt-2 inline-block">
          返回报告列表
        </Link>
      </div>
    )
  }

  const r = report as ReportDetailType
  const reportSections = Object.entries(r.reports || {})
    .filter(([, content]) => typeof content === 'string' && content.trim().length > 0)
    .sort(([a], [b]) => {
      const ai = REPORT_SECTIONS.findIndex(s => s.key === a)
      const bi = REPORT_SECTIONS.findIndex(s => s.key === b)
      return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi)
    })

  const openSections = expandedSections.size > 0
    ? expandedSections
    : new Set(reportSections.slice(0, 2).map(([key]) => key))

  const toggleSection = (key: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev.size > 0 ? prev : openSections)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })
  }

  const getDirectionIcon = (direction?: string) => {
    if (direction === 'bullish') return <TrendingUp className="w-6 h-6 text-green-400" />
    if (direction === 'bearish') return <TrendingDown className="w-6 h-6 text-red-400" />
    return <Minus className="w-6 h-6 text-white/40" />
  }

  const colorMap: Record<string, string> = {
    blue: 'border-blue-500/30 bg-blue-500/5',
    green: 'border-green-500/30 bg-green-500/5',
    red: 'border-red-500/30 bg-red-500/5',
    purple: 'border-purple-500/30 bg-purple-500/5',
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/reports"
            className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/40 hover:text-white transition-all"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white">{r.stock_name}</h1>
              <span className="text-white/40">{r.stock_code}</span>
            </div>
            <p className="text-white/40 text-sm mt-1">
              {safeFormat(r.created_at, 'yyyy-MM-dd HH:mm')}
            </p>
          </div>
        </div>
        <button
          onClick={async () => {
            if (!id) return
            const blob = await reportsApi.downloadReport(id)
            saveBlob(blob, `${r.stock_code || 'analysis'}-${r.analysis_date || 'report'}.md`)
          }}
          className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white/60 hover:text-white hover:bg-white/10 flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          导出报告
        </button>
      </div>

      {/* Decision card */}
      <Card className={clsx('gradient-card rounded-2xl border p-6', colorMap[r.conclusion?.direction === 'bullish' ? 'green' : r.conclusion?.direction === 'bearish' ? 'red' : 'blue'])}>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            {getDirectionIcon(r.conclusion?.direction)}
            <div>
              <p className="text-white/40 text-sm">投资方向</p>
              <p className="text-2xl font-bold text-white mt-1">
                {r.conclusion?.direction === 'bullish'
                  ? '看多'
                  : r.conclusion?.direction === 'bearish'
                  ? '看空'
                  : '中性'}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-white/40 text-sm">置信度</p>
            <span
              className={clsx(
                'inline-block mt-1 px-3 py-1 rounded-full text-sm font-medium',
                r.conclusion?.confidence === 'high'
                  ? 'bg-blue-500/20 text-blue-400'
                  : r.conclusion?.confidence === 'medium'
                  ? 'bg-amber-500/20 text-amber-400'
                  : 'bg-white/10 text-white/60'
              )}
            >
              {r.conclusion?.confidence === 'high' ? '高' : r.conclusion?.confidence === 'medium' ? '中' : '低'}
            </span>
          </div>
        </div>

        {(r.conclusion?.target_price || r.conclusion?.stop_loss) && (
          <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-white/10">
            {r.conclusion?.target_price && (
              <div className="text-center p-4 rounded-xl bg-white/5">
                <p className="text-white/40 text-sm">目标价</p>
                <p className="text-green-400 text-2xl font-bold mt-1">¥{r.conclusion.target_price}</p>
              </div>
            )}
            {r.conclusion?.stop_loss && (
              <div className="text-center p-4 rounded-xl bg-white/5">
                <p className="text-white/40 text-sm">止损价</p>
                <p className="text-red-400 text-2xl font-bold mt-1">¥{r.conclusion.stop_loss}</p>
              </div>
            )}
          </div>
        )}

        {r.conclusion?.summary && (
          <div className="mt-6 p-4 rounded-xl bg-white/5">
            <p className="text-white/80 leading-relaxed">{r.conclusion.summary}</p>
          </div>
        )}

        {r.conclusion?.key_risks?.length > 0 && (
          <div className="mt-6">
            <p className="text-white/40 text-sm mb-3">核心风险</p>
            <div className="flex flex-wrap gap-2">
              {r.conclusion.key_risks.map((risk, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-full bg-red-500/10 text-red-400 text-sm border border-red-500/20"
                >
                  {risk}
                </span>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* Report sections */}
      <Card className="gradient-card rounded-2xl border border-white/5 overflow-hidden">
        <div className="px-5 py-4 border-b border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-400" />
            <h2 className="text-white font-semibold">分析报告</h2>
          </div>
          <span className="text-white/40 text-sm">{reportSections.length} 个章节</span>
        </div>

        {reportSections.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-10 h-10 text-white/20 mx-auto mb-3" />
            <p className="text-white/40">暂无报告内容</p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {reportSections.map(([key, content]) => {
              const meta = REPORT_SECTIONS.find(s => s.key === key)
              const Icon = meta?.icon || FileText
              const isOpen = openSections.has(key)
              return (
                <section key={key}>
                  <button
                    onClick={() => toggleSection(key)}
                    className="w-full px-5 py-4 flex items-center gap-3 text-left hover:bg-white/5 transition-colors"
                  >
                    {isOpen ? <ChevronDown className="w-4 h-4 text-white/40" /> : <ChevronRight className="w-4 h-4 text-white/40" />}
                    <Icon className="w-4 h-4 text-blue-400" />
                    <span className="text-white font-medium">{meta?.title || SECTION_TITLE_FALLBACK[key] || key}</span>
                    <span className="ml-auto text-green-400 text-xs">已生成</span>
                  </button>
                  {isOpen && (
                    <div className="px-6 pb-6">
                      <div className="prose prose-invert prose-sm max-w-none text-white/85 bg-white/[0.03] rounded-xl border border-white/5 p-5">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
                      </div>
                    </div>
                  )}
                </section>
              )
            })}
          </div>
        )}
      </Card>
    </div>
  )
}
