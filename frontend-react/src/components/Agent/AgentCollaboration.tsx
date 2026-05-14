import { memo, useMemo } from 'react'
import {
  ReactFlow,
  Handle,
  Position,
  MarkerType,
  type NodeProps,
  type NodeTypes,
  type Node,
  type Edge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {
  BarChart3, TrendingUp as TrendingUpIcon, Newspaper, MessageSquare,
  TrendingUp, TrendingDown, Users, Shield, CheckCircle2,
  Loader2, Zap, Brain,
} from 'lucide-react'
import { clsx } from 'clsx'

// ── Agent 元数据 ──────────────────────────────────────────────────────────────

interface AgentMeta {
  id: string
  name: string        // 英文名，用于匹配 current_step_name 后缀
  label: string       // 显示名称（含 emoji）
  goal: string        // 分析目标
  Icon: React.FC<{ className?: string; style?: React.CSSProperties }>
  badgeBg: string
  badgeText: string
  phase: number       // 阶段：1=并行采集, 2=多空辩论, 3=交易决策, 4=风险评估
}

const META: AgentMeta[] = [
  // Phase 1: 并行采集
  { id: 'market',          name: '市场分析师',     label: '📊 市场分析师',       goal: 'K线形态/均线/成交量分析',         Icon: BarChart3,       badgeBg: 'bg-blue-500/10',    badgeText: 'text-blue-400',    phase: 1 },
  { id: 'fundamentals',    name: '基本面分析师',   label: '💼 基本面分析师',     goal: '财务指标/估值/业绩分析',          Icon: TrendingUpIcon,  badgeBg: 'bg-green-500/10',   badgeText: 'text-green-400',   phase: 1 },
  { id: 'news',            name: '新闻分析师',     label: '📰 新闻分析师',       goal: '政策资讯/公告/重大事件分析',      Icon: Newspaper,       badgeBg: 'bg-yellow-500/10',  badgeText: 'text-yellow-400',  phase: 1 },
  { id: 'social',          name: '社交媒体分析师', label: '💬 社交媒体分析师',   goal: '股吧/论坛/社交媒体舆情分析',      Icon: MessageSquare,   badgeBg: 'bg-purple-500/10',  badgeText: 'text-purple-400',  phase: 1 },
  // Phase 2: 多空辩论
  { id: 'bull',            name: '看涨研究员',     label: '🐂 看涨研究员',        goal: '评估投资价值与上行潜力',          Icon: TrendingUp,     badgeBg: 'bg-emerald-500/10', badgeText: 'text-emerald-400', phase: 2 },
  { id: 'bear',            name: '看跌研究员',     label: '🐻 看跌研究员',        goal: '评估下行风险与潜在危机',          Icon: TrendingDown,   badgeBg: 'bg-red-500/10',     badgeText: 'text-red-400',     phase: 2 },
  // Phase 3: 交易决策
  { id: 'trader',          name: '交易员决策',     label: '💼 交易员决策',        goal: '综合辩论给出操作建议',            Icon: Users,          badgeBg: 'bg-cyan-500/10',    badgeText: 'text-cyan-400',    phase: 3 },
  // Phase 4: 风险评估（3个视角并行 → 汇总到风险经理）
  { id: 'risk_aggressive', name: '激进风险评估',  label: '🔥 激进风险评估',      goal: '从激进角度评估投资风险',          Icon: TrendingUp,     badgeBg: 'bg-red-500/10',     badgeText: 'text-red-400',     phase: 4 },
  { id: 'risk_conservative',name: '保守风险评估',  label: '🛡️ 保守风险评估',      goal: '从保守角度评估投资风险',          Icon: Shield,         badgeBg: 'bg-blue-500/10',    badgeText: 'text-blue-400',    phase: 4 },
  { id: 'risk_neutral',    name: '中性风险评估',  label: '⚖️ 中性风险评估',       goal: '从中性角度评估投资风险',          Icon: BarChart3,      badgeBg: 'bg-yellow-500/10',  badgeText: 'text-yellow-400',  phase: 4 },
  { id: 'risk_manager',    name: '风险经理',       label: '🎯 风险经理',          goal: '综合风险评估，制定风控策略',      Icon: Shield,         badgeBg: 'bg-orange-500/10',  badgeText: 'text-orange-400',  phase: 4 },
]

// 节点位置（4列布局：采集→辩论→交易→风险）
// x: 0=采集, 420=辩论, 820=交易, 1220=风险
// y: 130px/节点
const NODE_POSITIONS: Record<string, { x: number; y: number }> = {
  // Phase 1: 并行采集 (x=0)
  market:        { x: 0,    y: 0 },
  fundamentals:  { x: 0,    y: 130 },
  news:          { x: 0,    y: 260 },
  social:        { x: 0,    y: 390 },
  // Phase 2: 多空辩论 (x=420)
  bull:          { x: 420,  y: 80 },
  bear:          { x: 420,  y: 260 },
  // Phase 3: 交易决策 (x=820)
  trader:        { x: 820,  y: 195 },
  // Phase 4: 风险评估 (x=1220) — 3视角并行,风险经理在右侧(x=1450)
  risk_aggressive:   { x: 1220, y: 0 },
  risk_conservative: { x: 1220, y: 130 },
  risk_neutral:      { x: 1220, y: 260 },
  risk_manager:      { x: 1500, y: 112 },  // 居中于"风险汇总"分组内
}

// 边定义
interface EdgeDef {
  source: string
  target: string
  label?: string
  thin?: boolean
  bidirectional?: boolean
}

const EDGE_DEFS: EdgeDef[] = [
  // Phase 1 → Phase 2 (所有采集分析师 → 多空研究员)
  ...['market', 'fundamentals', 'news', 'social'].map(s => ({ source: s, target: 'bull', thin: true } as EdgeDef)),
  ...['market', 'fundamentals', 'news', 'social'].map(s => ({ source: s, target: 'bear', thin: true } as EdgeDef)),
  // Phase 2: 多空辩论（双向边）
  { source: 'bull', target: 'bear', label: '辩论', bidirectional: true },
  // Phase 2 → Phase 3
  { source: 'bull',  target: 'trader' },
  { source: 'bear',  target: 'trader', label: '投资计划' },
  // Phase 3 → Phase 4 (3个风险视角并行)
  { source: 'trader', target: 'risk_aggressive', label: '交易方案' },
  { source: 'trader', target: 'risk_conservative', thin: true },
  { source: 'trader', target: 'risk_neutral', thin: true },
  // Phase 4: 3视角 → 风险经理汇总
  { source: 'risk_aggressive',   target: 'risk_manager', thin: true },
  { source: 'risk_conservative', target: 'risk_manager', thin: true },
  { source: 'risk_neutral',      target: 'risk_manager', label: '风险汇总' },
]

// 分组背景
const GROUP_LABELS = [
  { id: 'group-phase1', label: '并行采集', position: { x: -16, y: -30 },   width: 300, height: 560, phase: 1 },
  { id: 'group-phase2', label: '多空辩论', position: { x: 404, y: 44 },    width: 360, height: 290, phase: 2 },
  { id: 'group-phase3', label: '交易决策', position: { x: 804, y: 159 },   width: 280, height: 120, phase: 3 },
  // Phase 4: 风险评估（3视角并行）和风险汇总（经理）分成两个分组
  { id: 'group-phase4', label: '风险评估', position: { x: 1204, y: -30 },  width: 260, height: 560, phase: 4 },
  { id: 'group-phase5', label: '风险汇总', position: { x: 1470, y: 44 },   width: 230, height: 180, phase: 4 },
]

// ── 节点数据 ──────────────────────────────────────────────────────────────────

type NodeStatus = 'idle' | 'in_progress' | 'completed' | 'skipped' | 'error'

interface AgentNodeData {
  meta: AgentMeta
  status: NodeStatus
  duration?: number  // 秒
  selected?: boolean
  onSelect?: (id: string) => void
  [key: string]: unknown  // 必须：满足 @xyflow/react Node<>.data 约束
}

type AgentFlowNode = Node<AgentNodeData, 'agent'>
type GroupLabelNodeData = {
  label: string
  width: number
  height: number
  phase: number
  [key: string]: unknown
}
type GroupLabelFlowNode = Node<GroupLabelNodeData, 'groupLabel'>

// ── 匹配逻辑：根据 current_step_name 判断节点状态 ───────────────────────────────

function matchSuffix(stepName: string, agentId: string): boolean {
  const agent = META.find(a => a.id === agentId)
  if (!agent) return false
  return stepName.includes(agent.name) || stepName.endsWith(agent.name.replace(/[📊💼📰💬🐂🐻💼🎯]/g, '').trim())
}

// 并行分析师 ID 集合（Phase 1）
const PARALLEL_ANALYST_IDS = new Set(['market', 'fundamentals', 'news', 'social'])

// 并行风险评估节点（Phase 4 — 激进/保守/中性三视角并行）
const PARALLEL_RISK_IDS = new Set(['risk_aggressive', 'risk_conservative', 'risk_neutral'])

// 判断 stepName 是否属于并行采集阶段（Phase 1）
function isParallelPhase(stepName: string): boolean {
  return META.filter(a => a.phase === 1).some(a => matchSuffix(stepName, a.id))
}

// 判断 agentId 是否属于 Phase 1 并行分析师
function isParallelAnalyst(agentId: string): boolean {
  return PARALLEL_ANALYST_IDS.has(agentId)
}

// 判断 agentId 是否属于 Phase 4 并行风险评估（不包括 risk_manager）
function isParallelRiskNode(agentId: string): boolean {
  return PARALLEL_RISK_IDS.has(agentId)
}

// 判断 stepName 是否属于 Phase 4 并行风险评估
function isParallelRiskPhase(stepName: string): boolean {
  return ['激进风险评估', '保守风险评估', '中性风险评估'].some(name => stepName.includes(name))
}

// 格式化耗时
function formatDuration(seconds: number | undefined | null): string {
  if (!seconds) return ''
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`
}

// ── Agent 节点组件 ───────────────────────────────────────────────────────────

const STATUS_LABEL: Record<NodeStatus, string> = {
  idle: '待命', in_progress: '分析中', completed: '完成', skipped: '跳过', error: '异常',
}

function AgentNodeComponent({ data }: NodeProps<AgentFlowNode>) {
  const { meta, status, duration, selected, onSelect } = data
  const active = status === 'in_progress'
  const done = status === 'completed'
  const skipped = status === 'skipped'
  const failed = status === 'error'
  const { Icon } = meta

  return (
    <div
      className={clsx(
        'relative px-4 py-3 rounded-2xl border-2 transition-all duration-300 min-w-[220px] cursor-pointer',
        selected
          ? 'border-blue-500 bg-blue-500/10 shadow-[0_0_16px_rgba(59,130,246,0.3)] ring-2 ring-blue-400/30'
          : active
            ? 'border-blue-400 dark:border-blue-500/60 bg-white dark:bg-slate-800 shadow-[0_0_14px_rgba(59,130,246,0.25)]'
            : done
              ? 'border-emerald-300 dark:border-emerald-500/50 bg-white dark:bg-slate-800/80'
              : skipped
                ? 'border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 opacity-40'
                : failed
                  ? 'border-red-400 bg-red-500/10'
                  : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800',
      )}
      onClick={() => onSelect?.(meta.id)}
    >
      {/* Handles */}
      <Handle
        type="target" position={Position.Left} id="left"
        className="!w-2 !h-2 !bg-slate-300 dark:!bg-slate-600 !border-0 !min-w-0 !min-h-0"
      />
      <Handle
        type="source" position={Position.Right} id="right"
        className="!w-2 !h-2 !bg-slate-300 dark:!bg-slate-600 !border-0 !min-w-0 !min-h-0"
      />

      {/* 第一行：图标 + 标签 + 状态标签 */}
      <div className="flex items-center gap-2.5">
        <div className={clsx('shrink-0 w-9 h-9 rounded-xl flex items-center justify-center', meta.badgeBg)}>
          {active ? (
            <Loader2 className="w-[18px] h-[18px] animate-spin" style={{ color: meta.badgeText }} />
          ) : (
            <Icon className="w-[18px] h-[18px]" style={{ color: meta.badgeText }} />
          )}
        </div>
        <span className={clsx(
          'flex-1 text-[15px] font-bold leading-tight',
          active ? 'text-blue-600 dark:text-blue-400'
            : done ? 'text-slate-700 dark:text-slate-200'
            : skipped ? 'text-slate-400'
            : 'text-slate-600 dark:text-slate-300',
        )}>
          {meta.label}
        </span>
        <span className={clsx(
          'shrink-0 text-[11px] px-2 py-0.5 rounded-full font-bold',
          active ? 'bg-blue-500 text-white animate-pulse'
            : done ? 'bg-emerald-500 text-white'
            : skipped ? 'bg-slate-200 text-slate-400 dark:bg-slate-700 dark:text-slate-500'
            : failed ? 'bg-red-500 text-white'
            : 'bg-slate-100 text-slate-400 dark:bg-slate-700 dark:text-slate-500',
        )}>
          {STATUS_LABEL[status]}
        </span>
      </div>

      {/* 分析中动画 */}
      {active && (
        <div className="flex items-center gap-2 mt-2">
          <span className="flex gap-1">
            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" />
          </span>
          <span className="text-[12px] text-blue-500 font-medium">研判中...</span>
        </div>
      )}

      {/* 完成：耗时 */}
      {done && duration !== undefined && (
        <div className="flex items-center gap-1.5 mt-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
          <span className="text-[12px] text-emerald-600 dark:text-emerald-400 font-medium">完成</span>
          {duration > 0 && (
            <span className="text-[11px] text-slate-400 ml-1">{formatDuration(duration)}</span>
          )}
        </div>
      )}

      {done && duration === undefined && (
        <div className="flex items-center gap-1.5 mt-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
          <span className="text-[12px] text-emerald-600 dark:text-emerald-400 font-medium">完成</span>
        </div>
      )}

      {/* 跳过 */}
      {skipped && (
        <p className="text-[11px] text-slate-400 mt-1.5">已跳过</p>
      )}

      {/* 异常 */}
      {failed && (
        <p className="text-[11px] text-red-500 mt-1.5 font-medium">执行异常</p>
      )}

      {/* 脉冲动画（运行中） */}
      {active && (
        <div
          className="absolute inset-0 rounded-2xl opacity-15 animate-pulse pointer-events-none"
          style={{ backgroundColor: 'rgba(59,130,246,0.2)' }}
        />
      )}

      {/* Phase 标签角标 */}
      <div className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-slate-700 dark:bg-slate-600 flex items-center justify-center">
        <span className="text-[10px] font-bold text-white">{meta.phase}</span>
      </div>
    </div>
  )
}

// ── 分组标签节点 ──────────────────────────────────────────────────────────────

function GroupLabelNode({ data }: NodeProps<GroupLabelFlowNode>) {
  const phaseColors = ['text-blue-400', 'text-emerald-400', 'text-cyan-400', 'text-orange-400']
  return (
    <div
      className="rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-700/60 pointer-events-none bg-transparent"
      style={{ width: data.width, height: data.height }}
    >
      <div className="absolute -top-3 left-4 px-2 bg-[#0a0e17]">
        <span className={clsx('text-[10px] font-bold uppercase tracking-widest', phaseColors[data.phase - 1])}>
          {data.label}
        </span>
      </div>
    </div>
  )
}

const nodeTypes: NodeTypes = {
  agent: memo(AgentNodeComponent),
  groupLabel: memo(GroupLabelNode),
}

// ── 主组件 ────────────────────────────────────────────────────────────────────

interface AgentCollaborationProps {
  task: any | null
  selectedNodeId?: string | null
  onNodeClick?: (nodeId: string) => void
}

export function AgentCollaboration({ task, selectedNodeId, onNodeClick }: AgentCollaborationProps) {
  // 从 task 推断各节点状态
  const taskStatus = task?.status ?? 'idle'
  const currentStepName = task?.current_step_name || ''
  const steps: any[] = task?.steps || []

  const nodeDataList = useMemo(() => {
    return META.map(meta => {
      // 优先从 steps 数组获取状态
      const step = steps.find(s => {
        const name = s.name || ''
        return name.includes(meta.name) || name.endsWith(meta.name.replace(/[📊💼📰💬🐂🐻💼🎯]/g, '').trim())
      })

      let status: NodeStatus = 'idle'
      if (taskStatus === 'completed') {
        status = 'completed'
      } else if (taskStatus === 'failed') {
        // 判断失败时当前节点
        status = matchSuffix(currentStepName, meta.id) ? 'error' : 'completed'
      } else if (taskStatus === 'running' || taskStatus === 'processing') {
        // 并行采集阶段：currentStepName 匹配到任何一个分析师时，所有并行分析师都标记为运行中
        if (isParallelPhase(currentStepName) && isParallelAnalyst(meta.id)) {
          status = 'in_progress'
        // 并行风险评估阶段：任一风险视角运行时，三个并行风险节点都高亮（risk_manager 除外）
        } else if (isParallelRiskPhase(currentStepName) && isParallelRiskNode(meta.id)) {
          status = 'in_progress'
        } else if (matchSuffix(currentStepName, meta.id)) {
          status = 'in_progress'
        } else {
          // 检查 steps 数组中的状态
          if (step) {
            if (step.status === 'completed') status = 'completed'
            else if (step.status === 'current' || step.status === 'in_progress') status = 'in_progress'
            else if (step.status === 'failed') status = 'error'
            else if (step.status === 'skipped') status = 'skipped'
          }
        }
      }

      let duration: number | undefined = undefined
      if (step?.start_time && step?.end_time) {
        duration = step.end_time - step.start_time
      }

      return { meta, status, duration, selected: selectedNodeId === meta.id }
    })
  }, [task, currentStepName, steps, taskStatus, selectedNodeId])

  const cardMap = useMemo(() => new Map(nodeDataList.map(d => [d.meta.id, d])), [nodeDataList])
  const doneN = nodeDataList.filter(d => d.status === 'completed').length
  const activeN = nodeDataList.filter(d => d.status === 'in_progress').length
  const totalN = nodeDataList.filter(d => d.status !== 'skipped').length

  // 构建 ReactFlow 节点
  const nodes: (AgentFlowNode | GroupLabelFlowNode)[] = useMemo(() => {
    const groupNodes: GroupLabelFlowNode[] = GROUP_LABELS.map(g => ({
      id: g.id,
      type: 'groupLabel',
      position: g.position,
      data: { label: g.label, width: g.width, height: g.height, phase: g.phase },
      selectable: false,
      draggable: false,
      zIndex: -1,
    }))

    const agentNodes: AgentFlowNode[] = nodeDataList.map(d => ({
      id: d.meta.id,
      type: 'agent',
      position: NODE_POSITIONS[d.meta.id] ?? { x: 0, y: 0 },
      data: {
        meta: d.meta,
        status: d.status,
        duration: d.duration,
        selected: d.selected,
        onSelect: onNodeClick,
      },
    }))

    return [...groupNodes, ...agentNodes]
  }, [nodeDataList, selectedNodeId, onNodeClick])

  // 构建边
  const edges: Edge[] = useMemo(() => {
    return EDGE_DEFS.map((def, i) => {
      const srcCard = cardMap.get(def.source)
      const tgtCard = cardMap.get(def.target)
      const srcDone = srcCard?.status === 'completed'
      const tgtActive = tgtCard?.status === 'in_progress'
      const srcActive = srcCard?.status === 'in_progress'

      // 动态颜色：完成=绿色，运行中=蓝色，活跃边=脉冲
      let color = '#475569' // 灰色（默认）
      if (srcDone) color = '#10b981'           // 绿色-已完成
      else if (srcActive || tgtActive) color = '#3b82f6'  // 蓝色-进行中

      return {
        id: `e-${i}`,
        source: def.source,
        target: def.target,
        sourceHandle: 'right',
        targetHandle: 'left',
        type: 'default',
        animated: tgtActive,
        label: def.label,
        labelStyle: { fontSize: 10, fontWeight: 600, fill: '#64748b' },
        labelBgStyle: { fill: '#0a0e17', fillOpacity: 0.85 },
        labelBgPadding: [4, 2] as [number, number],
        labelBgBorderRadius: 4,
        style: {
          stroke: color,
          strokeWidth: def.thin ? 1 : 1.5,
          opacity: def.thin ? 0.6 : 1,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color,
          width: 16,
          height: 16,
        },
        ...(def.bidirectional && {
          markerStart: {
            type: MarkerType.ArrowClosed,
            color,
            width: 16,
            height: 16,
          },
        }),
      } satisfies Edge
    })
  }, [cardMap])

  const isRunning = taskStatus === 'running' || taskStatus === 'processing'

  return (
    <div className="relative">
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-4 border-b border-white/10 pb-3">
        <div className="flex items-center gap-3">
          <div className={clsx(
            'w-3 h-3 rounded-full',
            isRunning ? 'bg-blue-500 animate-pulse shadow-[0_0_12px_#3b82f6]'
              : taskStatus === 'completed' ? 'bg-emerald-500'
              : taskStatus === 'failed' ? 'bg-red-500'
              : 'bg-slate-500',
          )} />
          <h3 className="text-base font-bold text-white/90 tracking-tight uppercase">
            QuantScope 协同分析流
          </h3>
          {task?.stock_name && (
            <span className="text-blue-400 text-sm font-medium">{task.stock_name}</span>
          )}
        </div>
        {isRunning && (
          <div className="flex items-center gap-4">
            {activeN > 0 && (
              <span className="text-[11px] px-2 py-1 rounded-full bg-blue-500/20 text-blue-400 font-medium">
                {activeN} 节点运行中
              </span>
            )}
            {doneN > 0 && (
              <span className="text-right">
                <div className="text-xl font-black text-emerald-400 tabular-nums">
                  {totalN > 0 ? Math.round((doneN / totalN) * 100) : 0}%
                </div>
                <p className="text-[10px] text-slate-500 uppercase tracking-tighter">分析进度</p>
              </span>
            )}
          </div>
        )}
        {taskStatus === 'completed' && (
          <span className="text-emerald-400 text-xs font-medium">✅ 分析完成</span>
        )}
        {taskStatus === 'failed' && (
          <span className="text-red-400 text-xs font-medium">❌ 分析失败</span>
        )}
      </div>

      {/* React Flow 画布 */}
      <div className="h-[520px] w-full rounded-2xl border border-white/10 bg-[#0a0e17]/50">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodeClick={(_, node) => {
            const d = node.data as AgentNodeData
            if (d.onSelect && (d.status === 'completed' || d.status === 'in_progress')) {
              d.onSelect(d.meta.id)
            }
          }}
          defaultViewport={{ x: 10, y: 10, zoom: 0.85 }}
          nodesDraggable={false}
          nodesConnectable={false}
          nodesFocusable={false}
          edgesFocusable={false}
          panOnDrag
          panOnScroll={false}
          zoomOnScroll={false}
          zoomOnPinch={false}
          zoomOnDoubleClick={false}
          preventScrolling={false}
          translateExtent={[[-40, -40], [1900, 600]]}
          proOptions={{ hideAttribution: true }}
          fitView={false}
        />
      </div>
    </div>
  )
}