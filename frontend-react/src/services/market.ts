import apiClient from '@/lib/api'

export interface KLineRecord {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  change?: number
  turnover?: number
}

export interface KLineResponse {
  success: boolean
  symbol: string
  name?: string
  market?: string
  records: KLineRecord[]
  count: number
  period: string
}

export interface RealtimeQuote {
  success: boolean
  symbol: string
  name: string
  price: number
  change: number
  open: number
  high: number
  low: number
  volume: number
  amount: number
}

export interface MarketIndex {
  name: string
  code: string
  price: number
  change: number
  up: boolean
  market?: string
}

export interface MarketOverviewGroup {
  market: string
  indices: MarketIndex[]
}

export interface MarketOverviewResponse {
  success: boolean
  markets?: MarketOverviewGroup[]
  indices: MarketIndex[]
  updated_at: string
}

export const marketApi = {
  // K线数据
  getKLine: async (symbol: string, params?: { period?: string; limit?: number }) => {
    const response = await apiClient.get<KLineResponse>(`/kline/${symbol}`, { params })
    return response.data
  },

  // 实时行情
  getRealtime: async (symbol: string): Promise<RealtimeQuote> => {
    const response = await apiClient.get<RealtimeQuote>(`/kline/${symbol}/realtime`)
    return response.data
  },

  // 市场概览（主要指数）
  getOverview: async (): Promise<MarketOverviewResponse> => {
    const response = await apiClient.get<MarketOverviewResponse>(`/kline/overview`)
    return response.data
  },
}
