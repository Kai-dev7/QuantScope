import apiClient from '@/lib/api'

export const authApi = {
  login: async (username: string, password: string) => {
    const response = await apiClient.post('/auth/login', { username, password })
    return response.data
  },

  logout: async (token?: string | null) => {
    const response = await apiClient.post('/auth/logout', undefined, {
      timeout: 3000,
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      _skipAuthRedirect: true,
    })
    return response.data
  },

  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me')
    return response.data.data  // unwrap {success, data: user} → user
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

  // 账号密码登录（login 的别名）
  loginWithPassword: async (username: string, password: string) => {
    const response = await apiClient.post('/auth/login', { username, password })
    return response.data
  },
}
