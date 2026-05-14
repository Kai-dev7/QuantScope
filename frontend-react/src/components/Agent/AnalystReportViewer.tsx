import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { clsx } from 'clsx'
import { Loader2 } from 'lucide-react'

// ============================================================
// Analyst report tab definition
// ============================================================
export interface AnalystTab {
  id: string
  label: string
  icon?: string
  category: string
  content?: string
  loading?: boolean
}

interface AnalystReportViewerProps {
  tabs: AnalystTab[]
  activeTab?: string
  onTabChange?: (tabId: string) => void
}

// ============================================================
// Tab badge: shows which analysts have content
// ============================================================
export function AnalystBadge({ count }: { count: number }) {
  if (count === 0) return null
  return (
    <span className="ml-1 px-1.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400 text-[10px] font-medium">
      {count}
    </span>
  )
}

// ============================================================
// AnalystReportViewer: tabbed analyst reports
// ============================================================
export function AnalystReportViewer({ tabs, activeTab, onTabChange }: AnalystReportViewerProps) {
  const [localActiveTab, setLocalActiveTab] = useState(tabs[0]?.id || '')
  const currentTabId = activeTab ?? localActiveTab
  const currentTab = tabs.find(t => t.id === currentTabId) || tabs[0]

  const handleTabClick = (tabId: string) => {
    setLocalActiveTab(tabId)
    onTabChange?.(tabId)
  }

  if (tabs.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-white/30 text-sm">
        暂无分析师报告
      </div>
    )
  }

  // Group tabs by category
  const categories = [...new Set(tabs.map(t => t.category))]

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar */}
      <div className="border-b border-white/10 overflow-x-auto flex-shrink-0">
        <div className="flex gap-0 min-w-max px-4">
          {categories.map(cat => (
            <div key={cat} className="mr-4">
              <div className="text-[10px] text-white/30 uppercase tracking-wider mb-1 mt-2 px-1">{cat}</div>
              {tabs.filter(t => t.category === cat).map(tab => (
                <button
                  key={tab.id}
                  onClick={() => handleTabClick(tab.id)}
                  className={clsx(
                    'px-3 py-2 text-xs font-medium border-b-2 transition-colors whitespace-nowrap',
                    currentTabId === tab.id
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-white/50 hover:text-white/80'
                  )}
                >
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Report content */}
      <div className="flex-1 overflow-y-auto p-5">
        {currentTab?.loading ? (
          <div className="flex items-center gap-2 justify-center h-32 text-white/40">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">加载报告中...</span>
          </div>
        ) : currentTab?.content ? (
          <div className="prose prose-invert prose-sm max-w-none text-white/90">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {currentTab.content}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="flex items-center justify-center h-32 text-white/30 text-sm">
            {currentTab ? '暂无报告内容' : '选择一个分析师查看报告'}
          </div>
        )}
      </div>
    </div>
  )
}

// ============================================================
// Parse analyst reports from task result_data.state.messages
// TradingAgents LangGraph state → individual analyst reports
// ============================================================
export function parseAnalystReportsFromMessages(
  messages: any[],
  stockCode: string
): AnalystTab[] {
  const tabs: AnalystTab[] = []

  if (!messages || messages.length === 0) return tabs

  // Try to extract analyst outputs from the messages
  // The structure varies by backend; this handles common patterns
  for (const msg of messages) {
    if (!msg || typeof msg !== 'object') continue

    const content: string = msg.content || ''
    const role: string = msg.role || ''

    // Identify analyst by content patterns or message metadata
    const lowerContent = content.toLowerCase()

    if (lowerContent.includes('market') || lowerContent.includes('k线') ||
        lowerContent.includes('技术分析') || lowerContent.includes('均线')) {
      tabs.push({
        id: 'market',
        label: '📈 市场技术分析',
        category: '并行采集',
        content: content.length > 50 ? content : undefined,
      })
    }

    if (lowerContent.includes('基本面') || lowerContent.includes('财务') ||
        lowerContent.includes('净利润') || lowerContent.includes('营收')) {
      tabs.push({
        id: 'fundamentals',
        label: '💰 基本面分析',
        category: '并行采集',
        content: content.length > 50 ? content : undefined,
      })
    }

    if (lowerContent.includes('新闻') || lowerContent.includes('公告') ||
        lowerContent.includes('政策') || lowerContent.includes('event')) {
      tabs.push({
        id: 'news',
        label: '📰 新闻舆情分析',
        category: '并行采集',
        content: content.length > 50 ? content : undefined,
      })
    }

    if (lowerContent.includes('情绪') || lowerContent.includes('舆情') ||
        lowerContent.includes('social') || lowerContent.includes('论坛')) {
      tabs.push({
        id: 'social',
        label: '💭 社区情绪分析',
        category: '并行采集',
        content: content.length > 50 ? content : undefined,
      })
    }

    if (lowerContent.includes('看涨') || lowerContent.includes('bullish') ||
        lowerContent.includes('多头')) {
      tabs.push({
        id: 'bull',
        label: '🐂 看涨研究员',
        category: '多空辩论',
        content: content.length > 50 ? content : undefined,
      })
    }

    if (lowerContent.includes('看跌') || lowerContent.includes('bearish') ||
        lowerContent.includes('空头')) {
      tabs.push({
        id: 'bear',
        label: '🐻 看跌研究员',
        category: '多空辩论',
        content: content.length > 50 ? content : undefined,
      })
    }

    if (lowerContent.includes('交易') || lowerContent.includes('投资计划') ||
        lowerContent.includes('trader')) {
      tabs.push({
        id: 'trader',
        label: '💼 交易员',
        category: '交易决策',
        content: content.length > 50 ? content : undefined,
      })
    }

    if (lowerContent.includes('风险') || lowerContent.includes('risk')) {
      tabs.push({
        id: 'risk',
        label: '🛡️ 风险评估',
        category: '风险评估',
        content: content.length > 50 ? content : undefined,
      })
    }
  }

  // Deduplicate by id
  const seen = new Set<string>()
  return tabs.filter(tab => {
    if (seen.has(tab.id)) return false
    seen.add(tab.id)
    return true
  })
}
