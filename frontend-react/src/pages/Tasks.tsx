import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { analysisApi, AnalysisTask } from '@/services/analysis'
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
  ListTodo,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw,
  Trash2,
  Play,
} from 'lucide-react'
import { clsx } from 'clsx'
import { toast } from 'sonner'

export default function Tasks() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => analysisApi.getTasks({ page_size: 100 }),
  })

  const retryMutation = useMutation({
    mutationFn: (taskId: string) => analysisApi.retryTask(taskId),
    onSuccess: () => {
      toast.success('任务已重新启动')
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
    onError: () => toast.error('重试失败'),
  })

  const cancelMutation = useMutation({
    mutationFn: (taskId: string) => analysisApi.cancelTask(taskId),
    onSuccess: () => {
      toast.success('任务已取消')
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
    onError: () => toast.error('取消失败'),
  })

  const tasks: AnalysisTask[] = data?.tasks || []

  const statusGroups = {
    running: tasks.filter((t) => t.status === 'running'),
    pending: tasks.filter((t) => t.status === 'pending'),
    completed: tasks.filter((t) => t.status === 'completed'),
    failed: tasks.filter((t) => t.status === 'failed'),
  }

  const TaskItem = ({ task }: { task: AnalysisTask }) => (
    <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
      <div className="flex items-center gap-4">
        {task.status === 'running' && <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />}
        {task.status === 'completed' && <CheckCircle2 className="w-5 h-5 text-green-400" />}
        {task.status === 'failed' && <XCircle className="w-5 h-5 text-red-400" />}
        {task.status === 'pending' && <Clock className="w-5 h-5 text-white/40" />}
        <div>
          <p className="text-white font-medium">{task.stock_name}</p>
          <p className="text-white/40 text-sm">{task.stock_code}</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <span
          className={clsx(
            'px-3 py-1 rounded-full text-xs font-medium',
            task.status === 'completed'
              ? 'bg-green-500/10 text-green-400'
              : task.status === 'failed'
              ? 'bg-red-500/10 text-red-400'
              : task.status === 'running'
              ? 'bg-blue-500/10 text-blue-400'
              : 'bg-white/5 text-white/40'
          )}
        >
          {task.status === 'completed'
            ? '已完成'
            : task.status === 'failed'
            ? '失败'
            : task.status === 'running'
            ? '运行中'
            : '等待中'}
        </span>
        <span className="text-white/30 text-sm">
          {safeFormat(task.created_at)}
        </span>
        {task.status === 'failed' && (
          <button
            onClick={() => retryMutation.mutate(task.task_id)}
            className="p-2 rounded-lg hover:bg-white/10 text-white/40 hover:text-blue-400"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        )}
        {(task.status === 'running' || task.status === 'pending') && (
          <button
            onClick={() => cancelMutation.mutate(task.task_id)}
            className="p-2 rounded-lg hover:bg-white/10 text-white/40 hover:text-red-400"
          >
            <XCircle className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )

  const TaskGroup = ({
    title,
    icon: Icon,
    tasks,
    color,
  }: {
    title: string
    icon: any
    tasks: AnalysisTask[]
    color: string
  }) => (
    <Card className="gradient-card border-white/5">
      <CardHeader className="pb-3">
        <CardTitle className="text-white flex items-center gap-2">
          <Icon className={clsx('w-5 h-5', `text-${color}-400`)} />
          {title}
          <span className="ml-auto text-white/40 text-sm font-normal">{tasks.length}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-14" />)
        ) : tasks.length === 0 ? (
          <p className="text-center py-6 text-white/30">暂无任务</p>
        ) : (
          tasks.map((task) => <TaskItem key={task.task_id} task={task} />)
        )}
      </CardContent>
    </Card>
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">任务队列</h1>
        <p className="text-white/40 mt-1">管理和监控分析任务</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TaskGroup
          title="运行中"
          icon={Loader2}
          tasks={statusGroups.running}
          color="blue"
        />
        <TaskGroup
          title="等待中"
          icon={Clock}
          tasks={statusGroups.pending}
          color="yellow"
        />
        <TaskGroup
          title="已完成"
          icon={CheckCircle2}
          tasks={statusGroups.completed}
          color="green"
        />
        <TaskGroup
          title="失败"
          icon={XCircle}
          tasks={statusGroups.failed}
          color="red"
        />
      </div>
    </div>
  )
}
