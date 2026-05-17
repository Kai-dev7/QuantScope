import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/services/auth'
import { toast } from 'sonner'
import { Zap, Eye, EyeOff, Mail, Lock, User, ArrowLeft, ArrowRight, Shield } from 'lucide-react'

type LoginStep = 'email' | 'code' | 'register'
type AuthMode = 'login' | 'register'

export default function Login() {
  const navigate = useNavigate()
  const { setToken } = useAuthStore()

  // 模式: 登录或注册
  const [mode, setMode] = useState<AuthMode>('login')

  // 步骤: email -> code -> register
  const [step, setStep] = useState<LoginStep>('email')

  // 表单数据
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  // UI状态
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [sendingCode, setSendingCode] = useState(false)
  const [devCode, setDevCode] = useState<string | null>(null)  // 开发环境显示的验证码
  const [countdown, setCountdown] = useState(0)

  // 发送验证码
  const handleSendCode = async () => {
    if (!email || !/^[^@]+@[^@]+\.[^@]+$/.test(email)) {
      toast.error('请输入有效的邮箱地址')
      return
    }

    setSendingCode(true)
    try {
      const data = await authApi.sendVerificationCode(email, mode === 'register' ? 'register' : 'login')

      if (data.data?.dev_code) {
        // 开发环境：显示验证码
        setDevCode(data.data.dev_code)
        toast.success('验证码已生成（开发模式）')
      } else {
        // 生产环境
        toast.success('验证码已发送到邮箱')
      }

      setStep('code')
      setCountdown(60)  // 60秒倒计时

      // 开始倒计时
      const timer = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            clearInterval(timer)
            return 0
          }
          return prev - 1
        })
      }, 1000)

    } catch (error: any) {
      toast.error(error.response?.data?.detail || '发送验证码失败')
    } finally {
      setSendingCode(false)
    }
  }

  // 验证验证码并登录/注册
  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!code || code.length !== 6) {
      toast.error('请输入6位验证码')
      return
    }

    setLoading(true)
    try {
      if (mode === 'login') {
        // 验证登录
        const data = await authApi.verifyCode(email, code)
        setToken(data.data?.access_token)
        toast.success('登录成功')
        navigate('/dashboard')
      } else {
        // 注册流程：验证通过后进入设置用户名密码
        setStep('register')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '验证码错误或已过期')
    } finally {
      setLoading(false)
    }
  }

  // 完成注册
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!username || username.length < 3) {
      toast.error('用户名至少3个字符')
      return
    }

    if (!password || password.length < 6) {
      toast.error('密码至少6个字符')
      return
    }

    if (password !== confirmPassword) {
      toast.error('两次密码输入不一致')
      return
    }

    setLoading(true)
    try {
      const data = await authApi.registerWithEmail(email, username, password, code)
      setToken(data.data?.access_token)
      toast.success('注册成功')
      navigate('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '注册失败')
    } finally {
      setLoading(false)
    }
  }

  // 返回上一步
  const handleBack = () => {
    if (step === 'code') {
      setStep('email')
      setCode('')
      setDevCode(null)
    } else if (step === 'register') {
      setStep('code')
      setUsername('')
      setPassword('')
      setConfirmPassword('')
    }
  }

  // 切换登录/注册模式
  const toggleMode = () => {
    setMode(prev => prev === 'login' ? 'register' : 'login')
    setStep('email')
    setCode('')
    setDevCode(null)
    setEmail('')
    setUsername('')
    setPassword('')
    setConfirmPassword('')
  }

  return (
    <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center p-4">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />
      </div>

      {/* Login card */}
      <div className="relative w-full max-w-md">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-cyan-500/20 rounded-3xl blur-xl" />
        <div className="relative gradient-card rounded-3xl p-8 shadow-2xl">

          {/* Logo */}
          <div className="flex flex-col items-center mb-6">
            <div className="relative mb-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/30">
                <Zap className="w-8 h-8 text-white" />
              </div>
              <div className="absolute -inset-2 bg-gradient-to-r from-blue-500 to-cyan-400 rounded-2xl blur opacity-40" />
            </div>
            <h1 className="text-2xl font-bold text-white">QuantScope</h1>
            <p className="text-white/40 text-sm mt-1">AI 智能投研平台</p>
          </div>

          {/* Step indicator */}
          <div className="flex items-center justify-center gap-2 mb-6">
            <div className={`flex items-center gap-2 ${step === 'email' ? 'text-blue-400' : 'text-green-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step === 'email' ? 'bg-blue-500/30 border-2 border-blue-500' : 'bg-green-500/30 border-2 border-green-500'
              }`}>
                {step === 'email' ? '1' : <Shield className="w-4 h-4" />}
              </div>
              <span className="text-sm">{mode === 'login' ? '输入邮箱' : '验证邮箱'}</span>
            </div>
            <ArrowRight className="w-4 h-4 text-white/30" />
            <div className={`flex items-center gap-2 ${step === 'code' ? 'text-blue-400' : step === 'register' ? 'text-green-400' : 'text-white/30'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step === 'code' ? 'bg-blue-500/30 border-2 border-blue-500' : step === 'register' ? 'bg-green-500/30 border-2 border-green-500' : 'bg-white/10 border-2 border-white/30'
              }`}>
                {step === 'code' ? '2' : step === 'register' ? <Shield className="w-4 h-4" /> : '2'}
              </div>
              <span className="text-sm">{mode === 'login' ? '输入验证码' : '设置密码'}</span>
            </div>
            {mode === 'register' && (
              <>
                <ArrowRight className="w-4 h-4 text-white/30" />
                <div className={`flex items-center gap-2 ${step === 'register' ? 'text-blue-400' : 'text-white/30'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    step === 'register' ? 'bg-blue-500/30 border-2 border-blue-500' : 'bg-white/10 border-2 border-white/30'
                  }`}>
                    3
                  </div>
                  <span className="text-sm">完成注册</span>
                </div>
              </>
            )}
          </div>

          {/* Forms */}
          {step === 'email' && (
            <form onSubmit={(e) => { e.preventDefault(); handleSendCode(); }} className="space-y-4">
              <div>
                <label className="block text-sm text-white/60 mb-2">邮箱</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50 focus:bg-white/10 transition-all"
                    placeholder="请输入邮箱地址"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={sendingCode}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {sendingCode ? (
                  '发送中...'
                ) : (
                  <>
                    <Mail className="w-5 h-5" />
                    {mode === 'login' ? '发送登录验证码' : '发送注册验证码'}
                  </>
                )}
              </button>
            </form>
          )}

          {step === 'code' && (
            <form onSubmit={handleVerifyCode} className="space-y-4">
              {/* 开发环境显示验证码 */}
              {devCode && (
                <div className="bg-green-500/20 border border-green-500/30 rounded-xl p-4 text-center">
                  <p className="text-green-400 text-sm mb-1">开发模式 - 验证码</p>
                  <p className="text-green-300 text-2xl font-bold tracking-widest">{devCode}</p>
                </div>
              )}

              <div>
                <label className="block text-sm text-white/60 mb-2">验证码</label>
                <div className="relative">
                  <Shield className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
                  <input
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50 focus:bg-white/10 transition-all text-center text-xl tracking-widest font-mono"
                    placeholder="请输入6位验证码"
                    maxLength={6}
                  />
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={handleBack}
                  className="flex-1 py-3 rounded-xl bg-white/5 border border-white/10 text-white/70 font-medium hover:bg-white/10 transition-all flex items-center justify-center gap-2"
                >
                  <ArrowLeft className="w-5 h-5" />
                  返回
                </button>
                <button
                  type="submit"
                  disabled={loading || code.length !== 6}
                  className="flex-1 py-3 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? '验证中...' : (
                    <>
                      {mode === 'login' ? '登录' : '下一步'}
                      <ArrowRight className="w-5 h-5" />
                    </>
                  )}
                </button>
              </div>

              {/* 重新发送 */}
              <div className="text-center">
                <button
                  type="button"
                  onClick={handleSendCode}
                  disabled={countdown > 0 || sendingCode}
                  className="text-sm text-blue-400 hover:text-blue-300 disabled:text-white/30"
                >
                  {countdown > 0 ? `${countdown}秒后可重新发送` : '重新发送验证码'}
                </button>
              </div>
            </form>
          )}

          {step === 'register' && (
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="block text-sm text-white/60 mb-2">邮箱</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
                  <input
                    type="email"
                    value={email}
                    disabled
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white/50 cursor-not-allowed"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm text-white/60 mb-2">用户名</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50 focus:bg-white/10 transition-all"
                    placeholder="3-50个字符"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm text-white/60 mb-2">密码</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-12 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50 focus:bg-white/10 transition-all"
                    placeholder="至少6个字符"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm text-white/60 mb-2">确认密码</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50 focus:bg-white/10 transition-all"
                    placeholder="再次输入密码"
                  />
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={handleBack}
                  className="flex-1 py-3 rounded-xl bg-white/5 border border-white/10 text-white/70 font-medium hover:bg-white/10 transition-all flex items-center justify-center gap-2"
                >
                  <ArrowLeft className="w-5 h-5" />
                  返回
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 py-3 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? '注册中...' : '完成注册'}
                </button>
              </div>
            </form>
          )}

          {/* Footer */}
          <div className="mt-6 pt-6 border-t border-white/10">
            <div className="flex items-center justify-between text-sm">
              <button
                onClick={toggleMode}
                className="text-blue-400 hover:text-blue-300 transition-colors"
              >
                {mode === 'login' ? '没有账号？立即注册' : '已有账号？立即登录'}
              </button>
              {mode === 'login' && (
                <button
                  onClick={() => {
                    setMode('login')
                    setStep('email')
                  }}
                  className="text-white/40 hover:text-white/60 transition-colors"
                >
                  账号密码登录
                </button>
              )}
            </div>

            {mode === 'login' && (
              <p className="text-center text-white/30 text-xs mt-4">
                默认账号: admin / admin123
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}