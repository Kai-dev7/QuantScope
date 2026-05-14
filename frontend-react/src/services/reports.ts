import apiClient from '@/lib/api'

export interface Report {
  id: string
  stock_code: string
  stock_name: string
  status?: string
  summary?: string
  recommendation?: string
  market_type?: string
  task_id?: string
  analysis_id?: string
  conclusion: {
    direction: 'bullish' | 'bearish' | 'neutral'
    confidence: 'high' | 'medium' | 'low'
    target_price?: number
    stop_loss?: number
    key_risks: string[]
    summary: string
  }
  created_at: string
  updated_at: string
}

export interface ReportDetail extends Report {
  modules: {
    financial?: any
    valuation?: any
    risk?: any
    industry?: any
    [key: string]: any
  }
  reports?: Record<string, string>
  analysts?: string[]
  research_depth?: string | number
  analysis_date?: string
  execution_time?: number
  tokens_used?: number
  events?: any[]
}

const unwrap = (payload: any) => payload?.data ?? payload

const normalizeReportListPayload = (payload: any) => {
  const data = unwrap(payload)
  const reports = Array.isArray(data?.reports)
    ? data.reports
    : Array.isArray(data)
      ? data
      : []

  return {
    ...data,
    reports: reports.map(normalizeReport),
    total: Number(data?.total ?? reports.length),
    page: Number(data?.page ?? 1),
    page_size: Number(data?.page_size ?? reports.length),
  }
}

const inferDirection = (raw: any): Report['conclusion']['direction'] => {
  const text = String(
    raw?.decision?.action ||
    raw?.recommendation ||
    raw?.summary ||
    ''
  ).toLowerCase()

  if (text.includes('buy') || text.includes('买入') || text.includes('增持') || text.includes('看多')) return 'bullish'
  if (text.includes('sell') || text.includes('卖出') || text.includes('减持') || text.includes('看空')) return 'bearish'
  return 'neutral'
}

const inferConfidence = (raw: any): Report['conclusion']['confidence'] => {
  const confidence = Number(raw?.decision?.confidence ?? raw?.confidence_score ?? 0)
  if (confidence >= 0.7) return 'high'
  if (confidence >= 0.4) return 'medium'
  return 'low'
}

const normalizeReport = (raw: any): Report => {
  const stockCode = raw?.stock_code || raw?.stock_symbol || raw?.symbol || ''
  const summary = raw?.conclusion?.summary || raw?.summary || raw?.recommendation || ''
  const keyRisks = raw?.conclusion?.key_risks || raw?.key_points || []

  return {
    ...raw,
    id: String(raw?.id || raw?._id || raw?.analysis_id || raw?.task_id || ''),
    stock_code: stockCode,
    stock_name: raw?.stock_name || stockCode,
    summary,
    conclusion: {
      direction: raw?.conclusion?.direction || inferDirection(raw),
      confidence: raw?.conclusion?.confidence || inferConfidence(raw),
      target_price: raw?.conclusion?.target_price || raw?.decision?.target_price,
      stop_loss: raw?.conclusion?.stop_loss,
      key_risks: Array.isArray(keyRisks) ? keyRisks : [],
      summary,
    },
    created_at: raw?.created_at || raw?.analysis_date || '',
    updated_at: raw?.updated_at || raw?.created_at || '',
  }
}

const normalizeDetail = (raw: any): ReportDetail => {
  const report = normalizeReport(raw)
  const reports = raw?.reports && typeof raw.reports === 'object' ? raw.reports : {}

  return {
    ...report,
    ...raw,
    id: report.id,
    stock_code: report.stock_code,
    stock_name: report.stock_name,
    conclusion: report.conclusion,
    modules: raw?.modules || reports || {},
    reports,
  }
}

export const reportsApi = {
  // Get report list
  getList: async (params?: {
    page?: number
    page_size?: number
    search_keyword?: string
    stock_code?: string
    market_filter?: string
    start_date?: string
    end_date?: string
  }) => {
    const response = await apiClient.get('/reports/list', { params })
    return normalizeReportListPayload(response.data)
  },

  // Get report detail
  getDetail: async (reportId: string): Promise<ReportDetail> => {
    const response = await apiClient.get(`/reports/${reportId}/detail`)
    return normalizeDetail(unwrap(response.data))
  },

  // Get module content
  getModuleContent: async (reportId: string, module: string) => {
    const response = await apiClient.get(`/reports/${reportId}/content/${module}`)
    return response.data
  },

  // Delete report
  deleteReport: async (reportId: string) => {
    const response = await apiClient.delete(`/reports/${reportId}`)
    return response.data
  },

  // Download report
  downloadReport: async (reportId: string) => {
    const response = await apiClient.get(`/reports/${reportId}/download`, {
      responseType: 'blob',
    })
    return response.data
  },
}
