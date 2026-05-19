import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { analysisApi, AnalysisTask, AnalysisResult, StockExtractResult } from '@/services/analysis'
import { AgentCollaboration } from '@/components/Agent/AgentCollaboration'
import { AnalystReportViewer, parseAnalystReportsFromMessages, AnalystTab } from '@/components/Agent/AnalystReportViewer'
import { Drawer } from '@/components/ui/drawer'
import { toast } from 'sonner'
import {
  Send,
  User,
  Bot,
  Loader2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { clsx } from 'clsx'

const NODE_LABELS: Record<string, string> = {
  market:'📊 市场分析师', fundamentals:'💼 基本面分析师', news:'📰 新闻分析师',
  social:'💬 社交媒体分析师', bull:'🐂 看涨研究员', bear:'🐻 看跌研究员',
  trader:'💼 交易员决策',
  risk_aggressive:'🔥 激进风险评估', risk_conservative:'🛡️ 保守风险评估',
  risk_neutral:'⚖️ 中性风险评估', risk_manager:'🎯 风险经理',
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

// 从 result.result_data.reports 中提取各分析师报告
// 后端已将 reports 字典存入 MongoDB: { market_report, fundamentals_report, ... }
function extractAnalystTabs(result: AnalysisResult): AnalystTab[] {
  const raw = (result as any)._raw || result
  const resultData = raw?.result_data || raw || {}
  const reports = resultData.reports || {}

  const REPORT_KEYS: Array<{ id: string; label: string; category: string; key: string }> = [
    { id: 'market',            label: '📊 市场分析师',     category: '并行采集', key: 'market_report' },
    { id: 'fundamentals',      label: '💼 基本面分析师',   category: '并行采集', key: 'fundamentals_report' },
    { id: 'news',              label: '📰 新闻分析师',     category: '并行采集', key: 'news_report' },
    { id: 'social',            label: '💬 社交媒体分析师', category: '并行采集', key: 'sentiment_report' },
    { id: 'bull',              label: '🐂 看涨研究员',     category: '多空辩论', key: 'bull_researcher' },
    { id: 'bear',              label: '🐻 看跌研究员',     category: '多空辩论', key: 'bear_researcher' },
    { id: 'trader',            label: '💼 交易员',         category: '交易决策', key: 'trader_investment_plan' },
    // Phase 4: 3个并行风险视角 + 风险经理汇总（共用 risk_management_decision）
    { id: 'risk_aggressive',   label: '🔥 激进风险评估',   category: '风险评估', key: 'risk_management_decision' },
    { id: 'risk_conservative',  label: '🛡️ 保守风险评估',   category: '风险评估', key: 'risk_management_decision' },
    { id: 'risk_neutral',      label: '⚖️ 中性风险评估',   category: '风险评估', key: 'risk_management_decision' },
    { id: 'risk_manager',      label: '🎯 风险经理',       category: '风险评估', key: 'risk_management_decision' },
  ]

  const tabs: AnalystTab[] = []
  for (const { id, label, category, key } of REPORT_KEYS) {
    const content = reports[key]
    if (content && typeof content === 'string' && content.trim().length > 20) {
      tabs.push({ id, label, category, content: content.trim() })
    }
  }

  if (tabs.length > 0) return tabs

  // Fallback: try parsing from state.messages
  const state = resultData.state || {}
  const messages = state.messages || []
  if (messages.length > 0) {
    const fromMessages = parseAnalystReportsFromMessages(messages, raw.stock_code || '')
    if (fromMessages.length > 0) return fromMessages
  }

  return []
}

// Default analyst tabs for the full report
const FULL_REPORT_TABS: AnalystTab[] = [
  { id: 'market', label: '📈 市场技术分析', category: '并行采集', content: '' },
  { id: 'fundamentals', label: '💰 基本面分析', category: '并行采集', content: '' },
  { id: 'news', label: '📰 新闻舆情分析', category: '并行采集', content: '' },
  { id: 'social', label: '💭 社区情绪分析', category: '并行采集', content: '' },
  { id: 'bull', label: '🐂 看涨研究员', category: '多空辩论', content: '' },
  { id: 'bear', label: '🐻 看跌研究员', category: '多空辩论', content: '' },
  { id: 'trader', label: '💼 交易员', category: '交易决策', content: '' },
  { id: 'risk_aggressive', label: '🔥 激进风险评估', category: '风险评估', content: '' },
  { id: 'risk_conservative', label: '🛡️ 保守风险评估', category: '风险评估', content: '' },
  { id: 'risk_neutral', label: '⚖️ 中性风险评估', category: '风险评估', content: '' },
  { id: 'risk_manager', label: '🎯 风险经理', category: '风险评估', content: '' },
]

export default function Analysis() {
  const [prompt, setPrompt] = useState('')
  const [extractedStock, setExtractedStock] = useState<StockExtractResult | null>(null)
  const [extracting, setExtracting] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [currentTask, setCurrentTask] = useState<AnalysisTask | null>(null)
  const [taskResult, setTaskResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [pipelineCollapsed, setPipelineCollapsed] = useState(false)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const isActiveTask = !!currentTask && !['completed', 'failed', 'cancelled'].includes(currentTask.status)

  const getTaskStepText = (task: AnalysisTask) =>
    task.current_step_description ||
    task.current_step_name ||
    task.message ||
    (typeof task.current_step === 'string' ? task.current_step : '') ||
    (task.status === 'pending' ? '等待执行...' : '分析中...')

  const getTaskErrorText = (task: AnalysisTask) =>
    task.error_message || task.last_error || task.message || '分析任务失败，请查看后端日志'

  // Poll task status when running
  const { data: polledTask } = useQuery({
    queryKey: ['task-status', currentTask?.task_id],
    queryFn: () => analysisApi.getTaskStatus(currentTask!.task_id),
    enabled: !!currentTask?.task_id && isActiveTask,
    refetchInterval: 3000,
  })

  // Merge polled status into currentTask
  useEffect(() => {
    if (polledTask && currentTask) {
      setCurrentTask(prev => prev ? {
        ...prev,
        ...polledTask,
        // 优先使用 current_step_name（后端返回的步骤名称）
        current_step: polledTask.current_step_name || polledTask.current_step || prev.current_step,
      } : prev)
      if (polledTask.status === 'completed') {
        analysisApi.getTaskResult(currentTask.task_id).then(result => {
          setTaskResult(result)
          setLoading(false)
          sessionStorage.setItem(`analysis_result_${currentTask.task_id}`, JSON.stringify(result))
          setMessages(prev => [
            ...prev,
            {
              role: 'assistant',
              content: `分析${polledTask.status === 'completed' ? '完成' : '失败'}！\n\n结论：${result.conclusion?.summary || '已完成分析'}`,
              timestamp: new Date(),
            },
          ])
        }).catch(() => {
          setLoading(false)
        })
      } else if (polledTask.status === 'failed') {
        setLoading(false)
        setMessages(prev => [
          ...prev,
          { role: 'assistant', content: `分析失败\n\n${getTaskErrorText(polledTask)}`, timestamp: new Date() },
        ])
      } else if (polledTask.status === 'cancelled') {
        setLoading(false)
        setMessages(prev => [
          ...prev,
          { role: 'assistant', content: '分析任务已取消', timestamp: new Date() },
        ])
      }
    }
  }, [polledTask])

  // Restore last analysis result on mount (survives page refresh)
  useEffect(() => {
    // Priority 1: sessionStorage (same-tab recovery)
    const lastTaskId = sessionStorage.getItem('last_analysis_task_id')
    if (lastTaskId) {
      const savedTask = sessionStorage.getItem(`analysis_task_${lastTaskId}`)
      const savedResult = sessionStorage.getItem(`analysis_result_${lastTaskId}`)
      if (savedTask) {
        try {
          const task: AnalysisTask = JSON.parse(savedTask)
          setCurrentTask(task)
          if (task.status === 'completed' && savedResult) {
            try {
              const result: AnalysisResult = JSON.parse(savedResult)
              setTaskResult(result)
            } catch {
              analysisApi.getTaskResult(lastTaskId).then(r => setTaskResult(r)).catch(() => {})
            }
          } else if (['running', 'pending'].includes(task.status)) {
            analysisApi.getTaskStatus(lastTaskId).then(status => {
              setCurrentTask(status)
              if (status.status === 'completed') {
                analysisApi.getTaskResult(lastTaskId).then(r => { setTaskResult(r); setLoading(false) }).catch(() => { setLoading(false) })
              } else if (['failed', 'cancelled'].includes(status.status)) {
                setLoading(false)
              }
            }).catch(() => { setLoading(false) })
          } else {
            setLoading(false)
          }
          return
        } catch {
          sessionStorage.removeItem(`analysis_task_${lastTaskId}`)
          sessionStorage.removeItem(`analysis_result_${lastTaskId}`)
        }
      }
    }

    // Priority 2: Fetch latest completed task from backend
    analysisApi.getHistory({ page: 1, page_size: 1 }).then(data => {
      const tasks: any[] = data?.tasks || data?.records || data || []
      const latest = tasks.find((t: any) => t.status === 'completed')
      if (latest) {
        const taskId = latest.task_id || latest.id
        setCurrentTask({
          task_id: taskId,
          stock_code: latest.stock_code || latest.symbol || '',
          stock_name: latest.stock_name || latest.stock_code || '',
          status: latest.status,
          created_at: latest.created_at || '',
          updated_at: latest.updated_at || '',
        })
        sessionStorage.setItem('last_analysis_task_id', taskId)
        sessionStorage.setItem(`analysis_task_${taskId}`, JSON.stringify({ task_id: taskId, stock_code: latest.stock_code || latest.symbol || '', stock_name: latest.stock_name || '', status: latest.status, created_at: latest.created_at || '', updated_at: latest.updated_at || '' }))
        analysisApi.getTaskResult(taskId).then(r => setTaskResult(r)).catch(() => {})
      }
    }).catch(() => {})
  }, [])

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // WebSocket for real-time updates
  useEffect(() => {
    if (!currentTask?.task_id) return
    const ws = analysisApi.createTaskWebSocket(currentTask.task_id)
    wsRef.current = ws

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'progress') {
        setCurrentTask(prev => prev ? {
          ...prev,
          progress: data.progress ?? data.data?.progress,
          current_step: data.step_name ?? data.data?.current_step_name ?? data.step ?? data.current_step,
          current_step_name: data.step_name ?? data.data?.current_step_name,
          current_step_description: data.step_description ?? data.data?.current_step_description,
        } : null)
      } else if (data.type === 'status') {
        const status = data.status === 'processing' || data.status === 'queued' ? 'running' : data.status
        setCurrentTask(prev => prev ? { ...prev, status, current_step: data.step || data.current_step } : null)
      } else if (data.type === 'step') {
        setCurrentTask(prev => prev ? {
          ...prev,
          current_step: data.step_name || data.step,
          current_step_name: data.step_name,
          current_step_description: data.step_description,
          progress: data.progress,
        } : null)
      } else if (data.type === 'step_completed') {
        // 后端推送步骤完成事件：标记该步骤为 completed
        const stepName = data.step_name || data.step
        if (stepName) {
          setCurrentTask(prev => prev ? { ...prev, current_step: stepName } : null)
        }
      } else if (data.type === 'step_update') {
        // 后端推送步骤更新（name/status/duration 变化）
        const stepName = data.step_name || data.data?.step_name
        const stepIndex = data.step_index ?? data.data?.step_index
        if (stepName) {
          setCurrentTask(prev => prev ? {
            ...prev,
            current_step_name: stepName,
            current_step_index: stepIndex ?? prev.current_step_index,
            // 同步 steps 数组
            steps: data.steps ? data.steps : prev.steps,
          } : null)
        }
      } else if (data.type === 'result') {
        setTaskResult(data.result)
        setLoading(false)
        // Persist result to sessionStorage for page refresh recovery
        if (currentTask?.task_id) {
          sessionStorage.setItem(`analysis_result_${currentTask.task_id}`, JSON.stringify(data.result))
        }
        setMessages(prev => [
          ...prev,
          { role: 'assistant', content: `分析完成！\n\n结论：${data.result.conclusion?.summary || '已完成分析'}`, timestamp: new Date() },
        ])
        ws.close()
      }
    }

    ws.onerror = () => { /* Fall back to polling */ }
    ws.onclose = () => { /* Polling will pick it up */ }

    return () => { ws.close() }
  }, [currentTask?.task_id])

  // Build analyst tabs from result
  const analystTabs = taskResult ? extractAnalystTabs(taskResult) : FULL_REPORT_TABS

  // When a pipeline node is clicked
  const handleNodeClick = (nodeId: string) => {
    setSelectedNodeId(prev => {
      const next = prev === nodeId ? null : nodeId
      if (next !== null) setDrawerOpen(true)
      return next
    })
  }

  const handleAnalyze = async () => {
    if (!prompt.trim()) {
      toast.error('请输入股票代码或分析需求描述')
      return
    }

    setLoading(true)
    setSelectedNodeId(null)
    setDrawerOpen(false)
    setMessages(prev => [
      ...prev,
      { role: 'user', content: prompt.trim(), timestamp: new Date() },
      { role: 'assistant', content: '正在识别股票...', timestamp: new Date() },
    ])
    setExtractedStock(null)

    try {
      // Step 1: Extract stock from natural language
      const extractResult = await analysisApi.extractStock(prompt.trim())
      setExtractedStock(extractResult)

      if (!extractResult.matched || !extractResult.stock_code) {
        setMessages(prev => {
          const last = prev[prev.length - 1]
          last.content = `无法识别股票：${extractResult.reason || '未找到匹配的股票'}`
          return [...prev.slice(0, -1), last]
        })
        setLoading(false)
        return
      }

      // Update message with recognized stock
      setMessages(prev => {
        const last = prev[prev.length - 1]
        const stockLabel = extractResult.stock_name
          ? `${extractResult.stock_name}(${extractResult.stock_code})`
          : extractResult.stock_code
        last.content = `识别到股票: ${stockLabel}，正在启动分析...`
        return [...prev.slice(0, -1), last]
      })

      // Step 2: Submit analysis
      const marketMap: Record<string, 'A股' | '港股' | '美股'> = {
        CN: 'A股', HK: '港股', US: '美股',
      }
      const marketType = marketMap[extractResult.market] || 'A股'
      const result = await analysisApi.analyze({
        stock_code: extractResult.stock_code,
        parameters: { market_type: marketType },
      })
      const taskToSave = {
        task_id: result.task_id,
        stock_code: extractResult.stock_code,
        stock_name: extractResult.stock_name || extractResult.stock_code,
        status: result.status || 'pending',
        progress: 0,
        current_step: result.message || '等待执行',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      setCurrentTask(taskToSave)
      sessionStorage.setItem('last_analysis_task_id', result.task_id)
      sessionStorage.setItem(`analysis_task_${result.task_id}`, JSON.stringify(taskToSave))
      setTaskResult(null)
      toast.success('分析任务已启动')
    } catch (error: any) {
      toast.error(error.response?.data?.message || '启动分析失败')
      setLoading(false)
      setMessages(prev => prev.slice(0, -2))
    }
  }

  return (
    <div className="h-[calc(100vh-120px)] flex gap-6">
      {/* Left: Chat panel */}
      <div className="w-[420px] flex flex-col gradient-card rounded-2xl border border-white/5 overflow-hidden flex-shrink-0">
        <div className="px-5 py-4 border-b border-white/5 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-white font-semibold">AI 分析师</h2>
            <p className="text-white/40 text-sm">多 Agent 协作分析</p>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <Bot className="w-12 h-12 text-white/20 mx-auto mb-3" />
              <p className="text-white/40">输入股票代码或描述分析需求</p>
              <p className="text-white/20 text-sm mt-1">例如: 000001, 贵州茅台, 帮我分析一下腾讯的走势</p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={clsx('flex gap-3', msg.role === 'user' ? 'flex-row-reverse' : '')}>
              <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0', msg.role === 'user' ? 'bg-blue-500' : 'bg-white/10')}>
                {msg.role === 'user' ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
              </div>
              <div className={clsx(
                'max-w-[80%] px-4 py-3 rounded-2xl text-sm whitespace-pre-wrap',
                msg.role === 'user' ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-tr-sm' : 'bg-white/5 text-white/80 rounded-tl-sm'
              )}>
                {msg.content}
              </div>
            </div>
          ))}
          {loading && currentTask && isActiveTask && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-white/5 px-4 py-3 rounded-2xl rounded-tl-sm">
                <div className="flex items-center gap-2 text-white/60">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{getTaskStepText(currentTask)}</span>
                </div>
                {currentTask.progress !== undefined && (
                  <div className="mt-2 w-48 h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all" style={{ width: `${currentTask.progress}%` }} />
                  </div>
                )}
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-white/5">
          <div className="flex gap-2">
            <input
              type="text"
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !loading && handleAnalyze()}
              placeholder="输入股票代码或描述分析需求..."
              className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50"
            />
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="px-4 py-3 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 text-white disabled:opacity-50 hover:opacity-90 transition-opacity"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </button>
          </div>
          {extractedStock?.matched && (
            <p className="text-white/40 text-xs mt-2 px-1">
              识别到: {extractedStock.stock_name}({extractedStock.stock_code}) · {extractedStock.market}
            </p>
          )}
        </div>
      </div>

      {/* Right: Agent Pipeline + Result */}
      <div className="flex-1 flex flex-col gap-4 min-w-0 overflow-hidden">
        {/* Agent Pipeline */}
        <div className="gradient-card rounded-2xl border border-white/5 overflow-hidden flex-shrink-0">
          <button
            onClick={() => setPipelineCollapsed(v => !v)}
            className="w-full px-5 py-3 flex items-center justify-between hover:bg-white/5 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-blue-400" />
              <span className="text-white font-medium text-sm">多 Agent 协作流程</span>
              {currentTask && (
                <span className={clsx(
                  'px-2 py-0.5 rounded-full text-xs',
                  currentTask.status === 'running' ? 'bg-blue-500/20 text-blue-400' :
                  currentTask.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                  currentTask.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                  'bg-white/10 text-white/40'
                )}>
                  {currentTask.status === 'running' ? '运行中' :
                   currentTask.status === 'completed' ? '已完成' :
                   currentTask.status === 'failed' ? '失败' : '等待'}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {selectedNodeId && (
                <span className="text-blue-400 text-xs">
                  已选: {NODE_LABELS[selectedNodeId] || selectedNodeId}
                </span>
              )}
              {pipelineCollapsed ? <ChevronDown className="w-4 h-4 text-white/40" /> : <ChevronUp className="w-4 h-4 text-white/40" />}
            </div>
          </button>

          {!pipelineCollapsed && (
            <div className="px-5 pb-5">
              <AgentCollaboration
                task={currentTask}
                selectedNodeId={selectedNodeId}
                onNodeClick={handleNodeClick}
              />
            </div>
          )}
        </div>

        {/* Result conclusion */}
        {taskResult?.conclusion && (
          <div className="gradient-card rounded-2xl border border-white/5 p-5 overflow-y-auto">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <Bot className="w-4 h-4 text-green-400" />
              分析结论
            </h3>
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="bg-white/5 rounded-xl p-3">
                <p className="text-white/40 text-xs">方向</p>
                <p className={clsx(
                  'text-lg font-semibold mt-1',
                  taskResult.conclusion.direction === 'bullish' ? 'text-green-400' :
                  taskResult.conclusion.direction === 'bearish' ? 'text-red-400' : 'text-yellow-400'
                )}>
                  {taskResult.conclusion.direction === 'bullish' ? '📈 看多' :
                   taskResult.conclusion.direction === 'bearish' ? '📉 看空' : '➡️ 中性'}
                </p>
              </div>
              <div className="bg-white/5 rounded-xl p-3">
                <p className="text-white/40 text-xs">置信度</p>
                <p className="text-lg font-semibold text-white mt-1">{taskResult.conclusion.confidence}</p>
              </div>
              {taskResult.conclusion.target_price && (
                <div className="bg-white/5 rounded-xl p-3">
                  <p className="text-white/40 text-xs">目标价</p>
                  <p className="text-lg font-semibold text-blue-400 mt-1">¥{taskResult.conclusion.target_price}</p>
                </div>
              )}
            </div>
            {taskResult.conclusion.key_risks?.length > 0 && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3">
                <p className="text-red-400 text-xs font-medium mb-2">⚠️ 关键风险</p>
                <ul className="space-y-1">
                  {taskResult.conclusion.key_risks.map((r, i) => (
                    <li key={i} className="text-white/60 text-xs">• {r}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="mt-4">
              <p className="text-white/60 text-xs mb-1">摘要</p>
              <div className="prose prose-invert prose-sm max-w-none text-white/80">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {taskResult.conclusion.summary}
                </ReactMarkdown>
              </div>
            </div>

            {/* Analyst tabs - show when result is ready */}
            {analystTabs.length > 0 && (
              <div className="mt-4 pt-4 border-t border-white/5">
                <p className="text-white/40 text-xs mb-3">分析师报告</p>
                <div className="flex flex-wrap gap-2">
                  {analystTabs.map(tab => (
                    <button
                      key={tab.id}
                      onClick={() => {
                        setSelectedNodeId(tab.id)
                        setDrawerOpen(true)
                      }}
                      className={clsx(
                        'px-3 py-1.5 rounded-lg text-xs border transition-colors',
                        selectedNodeId === tab.id
                          ? 'bg-blue-500/20 border-blue-500/40 text-blue-400'
                          : 'bg-white/5 border-white/10 text-white/60 hover:border-white/30 hover:text-white/80'
                      )}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Analyst detail drawer */}
      <Drawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        title={selectedNodeId ? (NODE_LABELS[selectedNodeId] || '分析师报告') : '分析师报告'}
      >
        <AnalystReportViewer
          tabs={analystTabs}
          activeTab={selectedNodeId || undefined}
          onTabChange={(tabId) => setSelectedNodeId(tabId)}
        />
      </Drawer>
    </div>
  )
}
