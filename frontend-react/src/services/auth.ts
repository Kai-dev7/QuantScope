import apiClient from '@/lib/api'

export const authApi = {
  login: async (username: string, password: string) => {
    const response = await apiClient.post('/auth/login', { username, password })
    return response.data
  },

  logout: async () => {
    const response = await apiClient.post('/auth/logout')
    return response.data
  },

  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me')
    return response.data
  },

  // 发送验证码
  sendVerificationCode: async (email: string, purpose: 'login' | 'register' = 'login') => {
    const response = await apiClient.post('/auth/send-code', { email, purpose })
    return response.data
  },

  // 验证验证码并登录
  verifyCode: async (email: string, code: string) => {
    const response = await apiClient.post('/auth/verify-code', { email, code })
    return response.data
  },

  // 邮箱注册
  registerWithEmail: async (email: string, username: string, password: string, code: string) => {
    const response = await apiClient.post('/auth/register-email', { email, username, password, code })
    return response.data
  },
}
