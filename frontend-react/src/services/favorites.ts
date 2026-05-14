import apiClient from '@/lib/api'

const unwrap = (payload: any) => payload?.data ?? payload

export interface FavoriteStock {
  stock_code: string
  stock_name: string
  market?: string
  added_at?: string
  tags?: string[]
  notes?: string
  alert_price_high?: number | null
  alert_price_low?: number | null
  current_price?: number | null
  change_percent?: number | null
}

export const favoritesApi = {
  getList: async (): Promise<FavoriteStock[]> => {
    const response = await apiClient.get('/favorites/')
    const data = unwrap(response.data)
    return Array.isArray(data) ? data : []
  },

  add: async (payload: {
    stock_code: string
    stock_name: string
    market?: string
    tags?: string[]
    notes?: string
  }) => {
    const response = await apiClient.post('/favorites/', payload)
    return response.data
  },

  remove: async (stockCode: string) => {
    const response = await apiClient.delete(`/favorites/${stockCode}`)
    return response.data
  },
}
