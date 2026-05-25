import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type LogoutOptions = {
  notifyServer?: boolean
  redirect?: boolean
}

export interface AuthUser {
  id: string
  username: string
  email: string
  name?: string
  is_admin?: boolean
}

interface AuthState {
  token: string | null
  user: AuthUser | null
  isAuthenticated: boolean
  setToken: (token: string | null, user?: AuthUser | null) => void
  setUser: (user: AuthUser | null) => void
  logout: (options?: LogoutOptions) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      setToken: (token, user) => set((state) => ({
        token,
        user: token ? (user !== undefined ? user : state.user) : null,
        isAuthenticated: !!token,
      })),
      setUser: (user) => set({ user }),
      logout: (options = {}) => {
        const { notifyServer = true, redirect = true } = options
        const token = useAuthStore.getState().token

        set({ token: null, user: null, isAuthenticated: false })

        if (redirect && !window.location.pathname.startsWith('/login')) {
          window.location.href = '/login'
        }

        if (notifyServer && token) {
          fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${token}`,
            },
            keepalive: true,
          }).catch((error) => {
            console.error('Logout API failed:', error)
          })
        }
      },
    }),
    {
      name: 'quantscope-auth',
    }
  )
)
