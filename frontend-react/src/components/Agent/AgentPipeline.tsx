import { useState, useEffect } from 'react'
import { Loader2, CheckCircle2, XCircle, Zap, BarChart3, TrendingUp as TrendingUpIcon, Newspaper, MessageSquare, TrendingUp, Users, Shield, Brain } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { clsx } from 'clsx'

// ============================================================
// QuantScope 分析流程节点定义
// 注意：节点ID必须与后端 tracker.py _generate_dynamic_steps() 步骤名后缀一一对应
// ============================================================
export interface PipelineNode {
  id: string
  label: string
  icon: any
  color: string
  bgColor: string
  borderColor: string
  phase: number
  description: string
}

// 后端步骤名 → 前端节点ID 精确后缀映射
// 例如: "📊 市场分析师".endsWith("市场分析师") → market
const NODE_SUFFIX_MAP: Record<string, string[]> = {
  market:           ['市场分析师', '市场技术分析', 'market', 'market_analyst', 'market_analysis'],
  fundamentals:     ['基本面分析师', '基本面分析', 'fundamentals', 'fundamental', 'fundamentals_analyst'],
  news:             ['新闻分析师', '新闻舆情分析', 'news', 'news_analyst'],
  social:           ['社交媒体分析师', '社区情绪分析', 'social', 'sentiment', 'social_analyst'],
  bull:             ['看涨研究员', '研究辩论', 'bull', 'bullish'],
  bear:             ['看跌研究员', '研究辩论', 'bear', 'bearish'],
  research_manager: ['研究经理', 'research_manager'],
  trader:           ['交易员决策', '交易员', 'trader', 'trading'],
  risk:             ['风险经理', '风险评估', '激进风险评估', '保守风险评估', '中性风险评估', 'risk', 'risk_management'],
}

function matchNodeBySuffix(stepName: string, nodeId: string): boolean {
  const normalizedStepName = String(stepName || '').toLowerCase()
  const suffixes = NODE_SUFFIX_MAP[nodeId] || []
  return suffixes.some(suffix => {
    const normalizedSuffix = suffix.toLowerCase()
    return normalizedStepName.endsWith(normalizedSuffix) || normalizedStepName.includes(normalizedSuffix)
  })
}

export const PIPELINE_NODES: PipelineNode[] = [
  // Phase 1: 并行采集
  { id: 'market',           label: '📊 市场分析师',       icon: BarChart3,       color: 'text-blue-400',    bgColor: 'bg-blue-500/10',    borderColor: 'border-blue-500/30',    phase: 1, description: 'K线形态/均线/成交量' },
  { id: 'fundamentals',     label: '💼 基本面分析师',     icon: TrendingUpIcon,  color: 'text-green-400',   bgColor: 'bg-green-500/10',   borderColor: 'border-green-500/30',   phase: 1, description: '财务指标/估值/业绩' },
  { id: 'news',             label: '📰 新闻分析师',       icon: Newspaper,       color: 'text-yellow-400',  bgColor: 'bg-yellow-500/10',  borderColor: 'border-yellow-500/30',  phase: 1, description: '政策/公告/重大事件' },
  { id: 'social',           label: '💬 社交媒体分析师',   icon: MessageSquare,   color: 'text-purple-400',  bgColor: 'bg-purple-500/10',  borderColor: 'border-purple-500/30',  phase: 1, description: '股吧/论坛/社交媒体' },
  // Phase 2: 多空辩论
  { id: 'bull',             label: '🐂 看涨研究员',       icon: TrendingUp,      color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', borderColor: 'border-emerald-500/30', phase: 2, description: '构建看多论点论据' },
  { id: 'bear',             label: '🐻 看跌研究员',         icon: TrendingUp,      color: 'text-red-400',     bgColor: 'bg-red-500/10',     borderColor: 'border-red-500/30',     phase: 2, description: '构建看空论点论据' },
  // Phase 3: 交易决策
  { id: 'trader',           label: '💼 交易员决策',        icon: Users,           color: 'text-cyan-400',    bgColor: 'bg-cyan-500/10',    borderColor: 'border-cyan-500/30',    phase: 3, description: '综合辩论给出操作建议' },
  // Phase 4: 风险评估
  { id: 'risk',             label: '🎯 风险评估',           icon: Shield,          color: 'text-orange-400', bgColor: 'bg-orange-500/10',  borderColor: 'border-orange-500/30',  phase: 4, description: '综合风险评估，制定风控策略' },
]

// 节点状态
export type NodeStatus = 'idle' | 'running' | 'completed' | 'failed' | 'skipped'

// 从 current_step_name 映射节点状态
export function getNodeStatus(currentStep: string, nodeId: string, taskStatus: string): NodeStatus {
  if (taskStatus === 'completed') return 'completed'
  if (taskStatus === 'failed') {
    return matchNodeBySuffix(currentStep, nodeId) ? 'failed' : 'completed'
  }
  if (taskStatus === 'running') {
    return matchNodeBySuffix(currentStep, nodeId) ? 'running' : 'idle'
  }
  return 'idle'
}

function normalizeTaskStatus(status: string): string {
  return status === 'processing' || status === 'queued' ? 'running' : status
}

// 从后端 API 提取当前步骤的显示文本
function getStepName(task: any): string {
  const stepName = task.current_step_name || ''
  if (stepName) return stepName
  // Fallback: 用 steps 数组 + 整数索引
  const idx = typeof task.current_step === 'number' ? task.current_step : parseInt(String(task.current_step), 10)
  const steps: any[] = task.steps || []
  if (steps.length > 0 && idx >= 0 && idx < steps.length) {
    return steps[idx].name || ''
  }
  return String(task.current_step || '')
}

function getStepText(task: any): string {
  return task.current_step_description || getStepName(task) || task.message || ''
}

// 从 steps 数组获取指定节点的状态
function getNodeStepStatus(task: any, nodeId: string): 'pending' | 'current' | 'completed' | 'failed' | 'idle' {
  if (!task?.steps || !Array.isArray(task.steps)) return 'idle'
  const matchingSteps = task.steps.filter((step: any) => matchNodeBySuffix(step.name || '', nodeId))
  if (matchingSteps.length === 0) return 'idle'

  if (matchingSteps.some((step: any) => step.status === 'current' || step.status === 'running')) return 'current'
  if (matchingSteps.some((step: any) => step.status === 'failed')) return 'failed'
  if (matchingSteps.some((step: any) => step.status === 'completed')) return 'completed'
  if (matchingSteps.some((step: any) => step.status === 'pending')) return 'pending'
  return 'idle'
}

function hasNodeStep(task: any, nodeId: string): boolean {
  if (!task?.steps || !Array.isArray(task.steps)) return false
  return task.steps.some((step: any) => matchNodeBySuffix(step.name || '', nodeId))
}

function getNodeProgressStatus(task: any, nodeId: string): NodeStatus {
  const status = normalizeTaskStatus(task?.status || '')
  const progress = Number(task?.progress || 0)
  const nodeIndex = PIPELINE_NODES.findIndex(node => node.id === nodeId)
  const currentStepName = getStepName(task)

  if (status === 'completed') return 'completed'
  if (status === 'failed') return matchNodeBySuffix(currentStepName, nodeId) ? 'failed' : (progress > 0 ? 'completed' : 'idle')
  if (status !== 'running') return 'idle'
  if (matchNodeBySuffix(currentStepName, nodeId)) return 'running'

  const currentNodeIndex = PIPELINE_NODES.findIndex(node => matchNodeBySuffix(currentStepName, node.id))
  if (currentNodeIndex >= 0 && nodeIndex >= 0 && nodeIndex < currentNodeIndex) return 'completed'

  return 'idle'
}

function getNodeDuration(task: any, nodeId: string): number | null {
  if (!task?.steps || !Array.isArray(task.steps)) return null
  const durations: number[] = []
  for (const step of task.steps) {
    if (matchNodeBySuffix(step.name || '', nodeId) && step.start_time && step.end_time) {
      durations.push(step.end_time - step.start_time)
    }
  }
  return durations.length > 0 ? durations.reduce((sum, value) => sum + value, 0) : null
}

// 格式化时间（秒）为人类可读字符串
function formatDuration(seconds: number | undefined | null): string {
  if (!seconds) return ''
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`
}

const PHASE_LABELS = ['并行采集', '多空辩论', '交易决策', '风险评估']
const PHASE_COLORS = ['text-blue-400', 'text-emerald-400', 'text-cyan-400', 'text-orange-400']
const PHASE_BG = ['bg-blue-500/5', 'bg-emerald-500/5', 'bg-cyan-500/5', 'bg-orange-500/5']

// ============================================================
// AgentPipeline 组件
// ============================================================
interface AgentPipelineProps {
  task: any | null
  compact?: boolean
  selectedNodeId?: string | null
  onNodeClick?: (nodeId: string) => void
}

export function AgentPipeline({ task, compact = false, selectedNodeId, onNodeClick }: AgentPipelineProps) {
  const [animatedNodes, setAnimatedNodes] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (task?.current_step_name) {
      // 找出当前步骤对应的节点ID并触发动画
      for (const [nodeId, suffixes] of Object.entries(NODE_SUFFIX_MAP)) {
        if (suffixes.some(suffix => task.current_step_name.endsWith(suffix))) {
          setAnimatedNodes(prev => new Set([...prev, nodeId]))
          break
        }
      }
    }
  }, [task?.current_step_name])

  if (!task) {
    if (compact) {
      return (
        <div className="space-y-2">
          {PIPELINE_NODES.map(node => (
            <Skeleton key={node.id} className="h-10 w-full" />
          ))}
        </div>
      )
    }
    return (
      <div className="space-y-3">
        {PIPELINE_NODES.map(node => (
          <Skeleton key={node.id} className="h-14 w-full" />
        ))}
      </div>
    )
  }

  const { stock_name, progress } = task
  const status = normalizeTaskStatus(task.status)
  const currentStepName = getStepName(task)
  const currentStepText = getStepText(task)

  return (
    <div className={compact ? 'space-y-3' : 'space-y-4'}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-yellow-400" />
          <span className="text-white font-medium text-sm">分析流程</span>
          {stock_name && <span className="text-blue-400 text-xs">({stock_name})</span>}
        </div>
        <div className="flex items-center gap-2">
          {status === 'running' && (
            <>
              <div className="flex items-center gap-1">
                <Loader2 className="w-3 h-3 text-blue-400 animate-spin" />
                <span className="text-blue-400 text-xs">{progress ?? 0}%</span>
              </div>
              <span className="text-white/40 text-xs max-w-[120px] truncate">{currentStepText}</span>
            </>
          )}
          {status === 'completed' && (
            <span className="text-green-400 text-xs">✅ 分析完成</span>
          )}
          {status === 'failed' && (
            <span className="text-red-400 text-xs">❌ 分析失败</span>
          )}
        </div>
      </div>

      {/* Phase-by-phase nodes */}
      {[1, 2, 3, 4].map(phase => {
        const phaseNodes = PIPELINE_NODES.filter(n => n.phase === phase)
        return (
          <div key={phase} className="space-y-1.5">
            {/* Phase label */}
            <div className={clsx('flex items-center gap-2 text-xs font-medium', PHASE_COLORS[phase - 1])}>
              <span className={clsx('w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold', PHASE_BG[phase - 1], 'border border-current/20')}>{phase}</span>
              {PHASE_LABELS[phase - 1]}
              {phase < 4 && <div className="flex-1 h-px bg-white/10 ml-2" />}
            </div>

            {/* Nodes */}
            <div className={clsx('grid gap-1.5', phase === 1 ? 'grid-cols-2' : 'grid-cols-1')}>
              {phaseNodes.map(node => {
                // 优先用 steps 数组中的状态，否则用 current_step_name / progress 推断
                const stepStatus = getNodeStepStatus(task, node.id)
                const isRunningFromSteps = stepStatus === 'current'
                const isCompletedFromSteps = stepStatus === 'completed'
                const isFailedFromSteps = stepStatus === 'failed'
                const hasStep = hasNodeStep(task, node.id)

                // 如果 steps 数组没有该节点信息，用 current_step_name 推断
                const nodeStatus: NodeStatus = !hasStep
                  ? getNodeProgressStatus(task, node.id)
                  : isRunningFromSteps ? 'running'
                  : isCompletedFromSteps ? 'completed'
                  : isFailedFromSteps ? 'failed'
                  : 'idle'

                const isAnimated = animatedNodes.has(node.id) || nodeStatus === 'running'
                const isSelected = selectedNodeId === node.id
                const Icon = node.icon
                const duration = getNodeDuration(task, node.id)

                return (
                  <button
                    key={node.id}
                    onClick={() => onNodeClick?.(node.id)}
                    className={clsx(
                      'relative flex items-center gap-2.5 px-3 py-2 rounded-xl border transition-all duration-500 text-left w-full',
                      node.borderColor,
                      isSelected
                        ? `${node.bgColor} ring-1 ring-offset-1 ring-offset-[#0a0e17] ${node.color.replace('text-', 'ring-')}`
                        : nodeStatus === 'idle' ? 'bg-white/3 opacity-50'
                        : nodeStatus === 'running' ? `${node.bgColor} opacity-100`
                        : nodeStatus === 'completed' ? `${node.bgColor} opacity-80`
                        : nodeStatus === 'failed' ? 'bg-red-500/10'
                        : 'bg-white/3 opacity-50',
                      nodeStatus !== 'idle' && 'cursor-pointer hover:opacity-100 hover:ring-1',
                    )}
                  >
                    {/* Status indicator */}
                    <div className={clsx(
                      'w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0',
                      nodeStatus === 'idle' ? 'bg-white/5' :
                      nodeStatus === 'running' ? `${node.bgColor} border ${node.borderColor}` :
                      nodeStatus === 'completed' ? `${node.bgColor}` :
                      nodeStatus === 'failed' ? 'bg-red-500/20' : 'bg-white/5'
                    )}>
                      {nodeStatus === 'idle' ? (
                        <div className="w-1.5 h-1.5 rounded-full bg-white/20" />
                      ) : nodeStatus === 'running' ? (
                        <Loader2 className={clsx('w-3 h-3 animate-spin', node.color)} />
                      ) : nodeStatus === 'completed' ? (
                        <CheckCircle2 className={clsx('w-3 h-3', node.color)} />
                      ) : nodeStatus === 'failed' ? (
                        <XCircle className="w-3 h-3 text-red-400" />
                      ) : null}
                    </div>

                    {/* Node info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <p className={clsx(
                          'text-xs font-medium truncate',
                          nodeStatus === 'idle' ? 'text-white/40' :
                          nodeStatus === 'running' ? 'text-white' :
                          nodeStatus === 'completed' ? 'text-white/90' :
                          'text-red-400'
                        )}>
                          {node.label}
                        </p>
                        {nodeStatus === 'running' && (
                          <span className={clsx('text-[10px] px-1 py-0.5 rounded bg-blue-500/20 text-blue-400', node.color)}>
                            运行中
                          </span>
                        )}
                        {nodeStatus === 'completed' && duration !== null && (
                          <span className="text-[10px] text-white/30">{formatDuration(duration)}</span>
                        )}
                      </div>
                      <p className="text-[10px] text-white/30 truncate">{node.description}</p>
                    </div>

                    {/* Selected indicator */}
                    {isSelected && (
                      <div className={clsx('w-1.5 h-1.5 rounded-full', node.color.replace('text-', 'bg-'))} />
                    )}

                    {/* Running pulse effect */}
                    {nodeStatus === 'running' && isAnimated && (
                      <div
                        className={clsx(
                          'absolute inset-0 rounded-xl opacity-20 animate-pulse pointer-events-none',
                          node.bgColor
                        )}
                      />
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
