import apiClient from '@/lib/api'

export interface AnalysisStep {
  name: string
  description: string
  status: 'pending' | 'current' | 'completed' | 'failed'
  weight: number
  start_time?: number
  end_time?: number
}

export interface AnalysisTask {
  task_id: string
  stock_code: string
  stock_name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress?: number
  current_step?: string | number
  current_step_index?: number
  current_step_name?: string
  current_step_description?: string
  message?: string
  error_message?: string
  last_error?: string
  created_at: string
  updated_at: string
  start_time?: string
  end_time?: string
  steps?: AnalysisStep[]
}

export interface AnalysisResult {
  task_id: string
  stock_code: string
  stock_name: string
  status: string
  conclusion?: {
    direction: 'bullish' | 'bearish' | 'neutral'
    confidence: 'high' | 'medium' | 'low'
    target_price?: number
    stop_loss?: number
    key_risks: string[]
    summary: string
  }
  modules: {
    financial?: any
    valuation?: any
    risk?: any
    industry?: any
  }
}

export interface AnalyzeRequest {
  stock_code: string
  period?: 'short' | 'medium' | 'long'
  parameters?: {
    market_type?: 'A股' | '港股' | '美股'
  }
}

export interface DashboardStats {
  total_analyses: number
  successful_analyses: number
  failed_analyses: number
  report_count: number
}

type RawTaskStatus = AnalysisTask['status'] | 'processing' | 'queued' | string

const normalizeStatus = (status: RawTaskStatus): AnalysisTask['status'] => {
  if (status === 'processing' || status === 'queued') return 'running'
  if (status === 'cancelled') return 'cancelled'
  if (status === 'completed' || status === 'failed' || status === 'running' || status === 'pending') return status
  return 'pending'
}

const normalizeTask = (task: any): AnalysisTask => ({
  ...task,
  task_id: task?.task_id || task?.id || task?._id || '',
  status: normalizeStatus(task?.status),
  stock_code: task?.stock_code || task?.stock_symbol || task?.symbol || '',
  stock_name: task?.stock_name || task?.stock_code || task?.stock_symbol || task?.symbol || '',
  error_message: task?.error_message || task?.last_error,
  created_at: task?.created_at || task?.start_time || new Date().toISOString(),
  updated_at: task?.updated_at || task?.last_update || task?.end_time || new Date().toISOString(),
})

const getSummary = (result: any): string =>
  result?.conclusion?.summary || result?.summary || result?.recommendation || '已完成分析'

const normalizeResult = (result: any): AnalysisResult => {
  if (result?.conclusion) return result

  const decision = result?.decision || {}
  const action = String(decision?.action || result?.recommendation || '').toLowerCase()
  const direction: NonNullable<AnalysisResult['conclusion']>['direction'] =
    action.includes('buy') || action.includes('买') || action.includes('看多') ? 'bullish' :
    action.includes('sell') || action.includes('卖') || action.includes('看空') ? 'bearish' :
    'neutral'

  return {
    ...result,
    task_id: result?.task_id || result?.analysis_id || '',
    stock_code: result?.stock_code || result?.stock_symbol || '',
    stock_name: result?.stock_name || result?.stock_code || result?.stock_symbol || '',
    status: result?.status || 'completed',
    modules: result?.modules || result?.reports || {},
    conclusion: {
      direction,
      confidence: decision?.confidence >= 0.7 || result?.confidence_score >= 0.7 ? 'high' :
        decision?.confidence >= 0.4 || result?.confidence_score >= 0.4 ? 'medium' : 'low',
      target_price: decision?.target_price,
      key_risks: result?.key_points || [],
      summary: getSummary(result),
    },
  }
}

export interface StockExtractResult {
  stock_name: string
  stock_code: string
  market: string
  confidence: number
  reason: string
  matched: boolean
}

export const analysisApi = {
  // Extract stock from natural language prompt
  extractStock: async (prompt: string): Promise<StockExtractResult> => {
    const response = await apiClient.post('/analysis/extract-stock', { prompt })
    // Backend wraps in {success, data: {...}}
    return response.data.data
  },

  // Start single stock analysis
  analyze: async (data: AnalyzeRequest) => {
    const response = await apiClient.post('/analysis/single', data)
    // Backend wraps in {success, data: {task_id, ...}}
    return normalizeTask(response.data.data)
  },

  // Start batch analysis
  analyzeBatch: async (stockCodes: string[]) => {
    const response = await apiClient.post('/analysis/batch', { stock_codes: stockCodes })
    return response.data
  },

  // Get task status
  getTaskStatus: async (taskId: string): Promise<AnalysisTask> => {
    const response = await apiClient.get(`/analysis/tasks/${taskId}/status`)
    // Backend wraps in {success, data: {task_id, status, ...}}
    return normalizeTask(response.data.data)
  },

  // Get task result
  getTaskResult: async (taskId: string): Promise<AnalysisResult> => {
    const response = await apiClient.get(`/analysis/tasks/${taskId}/result`)
    return normalizeResult(response.data.data)
  },

  // Get all tasks
  getTasks: async (params?: { page?: number; page_size?: number; limit?: number; offset?: number }) => {
    const limit = params?.limit ?? params?.page_size ?? 20
    const offset = params?.offset ?? ((params?.page && params.page > 1) ? (params.page - 1) * limit : 0)
    const response = await apiClient.get('/analysis/tasks', { params: { limit, offset } })
    const data = response.data?.data ?? response.data ?? {}
    return {
      ...data,
      tasks: Array.isArray(data?.tasks) ? data.tasks.map(normalizeTask) : [],
      total: Number(data?.total ?? 0),
    }
  },

  // Get lightweight dashboard stats
  getDashboardStats: async (): Promise<DashboardStats> => {
    const response = await apiClient.get('/analysis/dashboard/stats')
    const data = response.data?.data ?? response.data ?? {}
    return {
      total_analyses: Number(data?.total_analyses ?? 0),
      successful_analyses: Number(data?.successful_analyses ?? 0),
      failed_analyses: Number(data?.failed_analyses ?? 0),
      report_count: Number(data?.report_count ?? 0),
    }
  },

  // Get user history
  getHistory: async (params?: { page?: number; page_size?: number }) => {
    const response = await apiClient.get('/analysis/user/history', { params })
    return response.data.data
  },

  // Cancel task
  cancelTask: async (taskId: string) => {
    const response = await apiClient.post(`/analysis/tasks/${taskId}/cancel`)
    return response.data
  },

  // Retry failed task
  retryTask: async (taskId: string) => {
    const response = await apiClient.post(`/analysis/tasks/${taskId}/retry`)
    return response.data
  },

  // WebSocket for real-time updates
  createTaskWebSocket: (taskId: string) => {
    // In preview/production, Vite's http proxy doesn't forward WebSocket reliably,
    // so connect directly to the backend on its own port (8000).
    const envWsUrl = import.meta.env.VITE_API_WS_URL
    const wsBase = envWsUrl
      || (window.location.port === '4174'
          ? 'ws://localhost:8000'
          : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`)
    const wsUrl = `${wsBase}/api/analysis/ws/task/${taskId}`
    return new WebSocket(wsUrl)
  },
}
