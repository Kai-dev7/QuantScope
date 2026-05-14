import apiClient from '@/lib/api'

const unwrap = (payload: any) => payload?.data ?? payload

export interface SchedulerJob {
  id?: string
  job_id?: string
  name?: string
  display_name?: string
  description?: string
  next_run_time?: string | null
  trigger?: string
  status?: string
  enabled?: boolean
  paused?: boolean
}

export interface SchedulerStats {
  total_jobs?: number
  running_jobs?: number
  paused_jobs?: number
  enabled_jobs?: number
  [key: string]: any
}

export const schedulerApi = {
  getJobs: async (): Promise<SchedulerJob[]> => {
    const response = await apiClient.get('/scheduler/jobs')
    const data = unwrap(response.data)
    return Array.isArray(data) ? data : []
  },

  getStats: async (): Promise<SchedulerStats> => {
    const response = await apiClient.get('/scheduler/stats')
    return unwrap(response.data) || {}
  },

  pause: async (jobId: string) => {
    const response = await apiClient.post(`/scheduler/jobs/${jobId}/pause`)
    return response.data
  },

  resume: async (jobId: string) => {
    const response = await apiClient.post(`/scheduler/jobs/${jobId}/resume`)
    return response.data
  },

  trigger: async (jobId: string) => {
    const response = await apiClient.post(`/scheduler/jobs/${jobId}/trigger`)
    return response.data
  },
}
