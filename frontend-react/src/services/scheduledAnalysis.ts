import apiClient from '@/lib/api'

const unwrap = (payload: any) => payload?.data ?? payload

export interface ScheduledAnalysisPlan {
  plan_id: string
  stock_code: string
  stock_name: string
  market_type: string
  frequency: 'daily' | 'weekly' | 'monthly'
  run_time: string
  weekdays: number[]
  research_depth: string
  enabled: boolean
  notes?: string
  created_at?: string
  updated_at?: string
  last_run_at?: string | null
  last_task_id?: string | null
}

export type ScheduledAnalysisPayload = Omit<
  ScheduledAnalysisPlan,
  'plan_id' | 'created_at' | 'updated_at' | 'last_run_at' | 'last_task_id'
>

export const scheduledAnalysisApi = {
  getList: async (): Promise<ScheduledAnalysisPlan[]> => {
    const response = await apiClient.get('/scheduled-analysis')
    const data = unwrap(response.data)
    return Array.isArray(data) ? data : []
  },

  create: async (payload: ScheduledAnalysisPayload) => {
    const response = await apiClient.post('/scheduled-analysis', payload)
    return response.data
  },

  update: async (planId: string, payload: Partial<ScheduledAnalysisPayload>) => {
    const response = await apiClient.put(`/scheduled-analysis/${planId}`, payload)
    return response.data
  },

  remove: async (planId: string) => {
    const response = await apiClient.delete(`/scheduled-analysis/${planId}`)
    return response.data
  },

  runNow: async (planId: string) => {
    const response = await apiClient.post(`/scheduled-analysis/${planId}/run`)
    return response.data
  },
}
