import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import apiClient from '@/lib/api'
import {
  Bell,
  CalendarClock,
  ChevronDown,
  Cpu,
  Database,
  Key,
  Loader2,
  Pause,
  Play,
  Plus,
  RefreshCw,
  Save,
  Settings as SettingsIcon,
  Trash2,
  TrendingUp,
  User,
} from 'lucide-react'
import { clsx } from 'clsx'
import { authApi } from '@/services/auth'
import { useAuthStore } from '@/stores/auth'

interface AppSettings {
  email: string
  language: string
  timezone: string
  defaultMarket: 'A股' | '美股' | '港股'
  defaultDepth: 1 | 2 | 3 | 4 | 5
  autoRefresh: boolean
  refreshInterval: number
  notifyAnalysisComplete: boolean
  notifyDesktop: boolean
}

interface LLMProvider {
  id: string
  name: string
  display_name: string
  description?: string
  is_active: boolean
  default_base_url?: string
  api_key?: string | null
  extra_config?: { has_api_key?: boolean }
}

interface LLMConfig {
  provider: string
  model_name: string
  model_display_name?: string
  api_base?: string
  max_tokens: number
  temperature: number
  timeout: number
  retry_times: number
  enabled: boolean
  description?: string
  capability_level?: number
  suitable_roles?: string[]
  features?: string[]
  recommended_depths?: string[]
}

type TabKey = 'general' | 'analysis' | 'models' | 'systemTasks' | 'notifications' | 'api' | 'cache'

interface SchedulerJob {
  id?: string
  job_id?: string
  name?: string
  display_name?: string
  description?: string
  trigger?: string
  next_run_time?: string | null
  status?: string
  enabled?: boolean
  paused?: boolean
}

const LEGACY_DEFAULT_EMAIL = 'admin@quantscope.com'

const DEFAULT_SETTINGS: AppSettings = {
  email: '',
  language: 'zh-CN',
  timezone: 'Asia/Shanghai',
  defaultMarket: 'A股',
  defaultDepth: 3,
  autoRefresh: true,
  refreshInterval: 30,
  notifyAnalysisComplete: true,
  notifyDesktop: true,
}

const TABS: { key: TabKey; label: string; icon: React.ElementType }[] = [
  { key: 'general', label: '通用设置', icon: SettingsIcon },
  { key: 'analysis', label: '分析偏好', icon: TrendingUp },
  { key: 'models', label: '模型配置', icon: Cpu },
  { key: 'systemTasks', label: '系统任务', icon: CalendarClock },
  { key: 'notifications', label: '通知设置', icon: Bell },

  { key: 'cache', label: '缓存管理', icon: Database },
]

const EMPTY_MODEL_FORM: LLMConfig = {
  provider: '',
  model_name: '',
  model_display_name: '',
  api_base: '',
  max_tokens: 4000,
  temperature: 0.7,
  timeout: 180,
  retry_times: 3,
  enabled: true,
  description: '',
  capability_level: 2,
  suitable_roles: ['both'],
  features: [],
  recommended_depths: ['快速', '基础', '标准'],
}

function loadSettings(): AppSettings {
  try {
    const raw = localStorage.getItem('app_settings')
    return raw ? { ...DEFAULT_SETTINGS, ...JSON.parse(raw) } : DEFAULT_SETTINGS
  } catch {
    return DEFAULT_SETTINGS
  }
}

function shouldUseLoginEmail(email: string): boolean {
  return !email || email === LEGACY_DEFAULT_EMAIL
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={clsx(
        'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/50',
        checked ? 'bg-blue-500' : 'bg-white/10'
      )}
    >
      <span className={clsx('inline-block h-4 w-4 rounded-full bg-white shadow transition-transform', checked ? 'translate-x-6' : 'translate-x-1')} />
    </button>
  )
}

function SettingRow({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-4 border-b border-white/5 last:border-0 gap-6">
      <div className="min-w-0">
        <p className="text-white font-medium">{title}</p>
        {description && <p className="text-white/40 text-sm mt-0.5">{description}</p>}
      </div>
      <div className="flex-shrink-0">{children}</div>
    </div>
  )
}

function Panel({ icon: Icon, title, children }: { icon: React.ElementType; title: string; children: React.ReactNode }) {
  return (
    <div className="gradient-card rounded-2xl border border-white/5 overflow-hidden">
      <div className="px-6 py-4 border-b border-white/5 flex items-center gap-3">
        <Icon className="w-4 h-4 text-blue-400" />
        <span className="text-white font-semibold">{title}</span>
      </div>
      <div className="p-6">{children}</div>
    </div>
  )
}

function inputClass(extra = '') {
  return clsx('px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-blue-500/50', extra)
}

export default function Settings() {
  const { token, user, setUser } = useAuthStore()
  const [activeTab, setActiveTab] = useState<TabKey>('general')
  const [settings, setSettings] = useState<AppSettings>(loadSettings)
  const [saving, setSaving] = useState(false)
  const [clearingCache, setClearingCache] = useState(false)

  const [modelLoading, setModelLoading] = useState(false)
  const [modelSaving, setModelSaving] = useState(false)
  const [providers, setProviders] = useState<LLMProvider[]>([])
  const [llmConfigs, setLlmConfigs] = useState<LLMConfig[]>([])
  const [systemSettings, setSystemSettings] = useState<Record<string, any>>({})
  const [providerKeys, setProviderKeys] = useState<Record<string, string>>({})
  const [modelForm, setModelForm] = useState<LLMConfig>(EMPTY_MODEL_FORM)
  const [modelDefaults, setModelDefaults] = useState({ quick: '', deep: '' })
  const [schedulerJobs, setSchedulerJobs] = useState<SchedulerJob[]>([])
  const [schedulerLoading, setSchedulerLoading] = useState(false)
  const [showAddProvider, setShowAddProvider] = useState(false)
  const [addProviderSaving, setAddProviderSaving] = useState(false)
  const [addProviderForm, setAddProviderForm] = useState({
    name: '',
    display_name: '',
    description: '',
    website: '',
    api_doc_url: '',
    default_base_url: '',
    api_key: '',
    supported_features: [] as string[],
    is_active: true,
  })
  const [selectedPreset, setSelectedPreset] = useState('')

  const enabledModels = useMemo(() => llmConfigs.filter(m => m.enabled), [llmConfigs])
  const quickModel = systemSettings.quick_analysis_model || systemSettings.default_llm || enabledModels[0]?.model_name || ''
  const deepModel = systemSettings.deep_analysis_model || systemSettings.default_llm || enabledModels[0]?.model_name || ''

  useEffect(() => {
    const applyLoginEmail = (email?: string) => {
      if (!email) return
      setSettings(prev => shouldUseLoginEmail(prev.email) ? { ...prev, email } : prev)
    }

    applyLoginEmail(user?.email)

    if (user?.email || !token) return

    authApi.getCurrentUser()
      .then(response => {
        const currentUser = response.data
        setUser(currentUser)
        applyLoginEmail(currentUser?.email)
      })
      .catch(() => {
        // 保持本地设置可用，获取用户信息失败不阻塞设置页。
      })
  }, [setUser, token, user?.email])

  useEffect(() => {
    if (settings.notifyDesktop && typeof Notification !== 'undefined' && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [settings.notifyDesktop])

  useEffect(() => {
    if (activeTab === 'models') loadModelConfig()
    if (activeTab === 'systemTasks') loadSchedulerJobs()
  }, [activeTab])

  const update = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  const loadModelConfig = async () => {
    setModelLoading(true)
    try {
      const [providerRes, modelRes, settingsRes] = await Promise.all([
        apiClient.get('/config/llm/providers'),
        apiClient.get('/config/llm'),
        apiClient.get('/config/settings'),
      ])
      const nextProviders = Array.isArray(providerRes.data) ? providerRes.data : []
      const nextModels = Array.isArray(modelRes.data) ? modelRes.data : []
      setProviders(nextProviders)
      setLlmConfigs(nextModels)
      const nextSettings = settingsRes.data || {}
      setSystemSettings(nextSettings)
      setModelDefaults({
        quick: nextSettings.quick_analysis_model || nextSettings.default_llm || nextModels[0]?.model_name || '',
        deep: nextSettings.deep_analysis_model || nextSettings.default_llm || nextModels[0]?.model_name || '',
      })
      setModelForm(prev => ({
        ...prev,
        provider: prev.provider || nextProviders.find((p: LLMProvider) => p.is_active)?.name || nextProviders[0]?.name || '',
      }))
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '加载模型配置失败')
    } finally {
      setModelLoading(false)
    }
  }

  const handleSaveLocalSettings = () => {
    setSaving(true)
    localStorage.setItem('app_settings', JSON.stringify(settings))
    setSaving(false)
    toast.success('本地设置已保存')
  }

  const handleSaveModelDefaults = async () => {
    const payload = {
      ...systemSettings,
      quick_analysis_model: modelDefaults.quick,
      deep_analysis_model: modelDefaults.deep,
    }
    setSystemSettings(payload)
    try {
      await apiClient.put('/config/settings', payload)
      toast.success('默认分析模型已保存')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '保存默认模型失败')
    }
  }

  const handleSaveProviderKey = async (provider: LLMProvider) => {
    const apiKey = providerKeys[provider.id]
    if (apiKey === undefined) {
      toast.message('请输入新的 API Key 后再保存')
      return
    }
    try {
      await apiClient.put(`/config/llm/providers/${provider.id}`, {
        name: provider.name,
        display_name: provider.display_name,
        description: provider.description || '',
        is_active: provider.is_active,
        default_base_url: provider.default_base_url || '',
        api_key: apiKey,
        supported_features: [],
        extra_config: provider.extra_config || {},
      })
      setProviderKeys(prev => ({ ...prev, [provider.id]: '' }))
      toast.success(`${provider.display_name || provider.name} API Key 已保存`)
      loadModelConfig()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '保存厂家配置失败')
    }
  }

  const PRESET_PROVIDERS = [
    { name: 'dashscope', display_name: '阿里云百炼', description: '阿里云百炼大模型服务平台，提供通义千问等模型', website: 'https://bailian.console.aliyun.com', api_doc_url: 'https://help.aliyun.com/zh/dashscope/', default_base_url: 'https://dashscope.aliyuncs.com/api/v1', supported_features: ['chat', 'completion', 'embedding', 'function_calling', 'streaming'] },
    { name: 'deepseek', display_name: 'DeepSeek', description: 'DeepSeek提供高性能的AI推理服务', website: 'https://www.deepseek.com', api_doc_url: 'https://platform.deepseek.com/api-docs', default_base_url: 'https://api.deepseek.com', supported_features: ['chat', 'completion', 'function_calling', 'streaming'] },
    { name: 'openai', display_name: 'OpenAI', description: 'OpenAI是人工智能领域的领先公司，提供GPT系列模型', website: 'https://openai.com', api_doc_url: 'https://platform.openai.com/docs', default_base_url: 'https://api.openai.com/v1', supported_features: ['chat', 'completion', 'embedding', 'vision', 'function_calling', 'streaming'] },
    { name: 'anthropic', display_name: 'Anthropic', description: 'Anthropic专注于AI安全研究，提供Claude系列模型', website: 'https://anthropic.com', api_doc_url: 'https://docs.anthropic.com', default_base_url: 'https://api.anthropic.com', supported_features: ['chat', 'completion', 'function_calling', 'streaming'] },
    { name: '302ai', display_name: '302.AI', description: '302.AI是企业级AI聚合平台', website: 'https://302.ai', api_doc_url: 'https://doc.302.ai', default_base_url: 'https://api.302.ai/v1', supported_features: ['chat', 'completion', 'embedding', 'vision', 'function_calling', 'streaming'] },
    { name: 'zhipu', display_name: '智谱AI', description: '智谱AI提供GLM系列中文大模型', website: 'https://zhipuai.cn', api_doc_url: 'https://open.bigmodel.cn/doc', default_base_url: 'https://open.bigmodel.cn/api/paas/v4', supported_features: ['chat', 'completion', 'embedding', 'function_calling', 'streaming'] },
    { name: 'baidu', display_name: '百度智能云', description: '百度提供的文心一言等AI服务', website: 'https://cloud.baidu.com', api_doc_url: 'https://cloud.baidu.com/doc/WENXINWORKSHOP/index.html', default_base_url: 'https://aip.baidubce.com', supported_features: ['chat', 'completion', 'embedding', 'streaming'] },
    { name: 'google', display_name: 'Google AI', description: 'Google的人工智能平台，提供Gemini系列模型', website: 'https://ai.google.dev', api_doc_url: 'https://ai.google.dev/docs', default_base_url: 'https://generativelanguage.googleapis.com/v1', supported_features: ['chat', 'completion', 'embedding', 'vision', 'function_calling', 'streaming'] },
  ]

  const handlePresetChange = (presetName: string) => {
    setSelectedPreset(presetName)
    if (!presetName) {
      setAddProviderForm({ name: '', display_name: '', description: '', website: '', api_doc_url: '', default_base_url: '', api_key: '', supported_features: [], is_active: true })
      return
    }
    const preset = PRESET_PROVIDERS.find(p => p.name === presetName)
    if (preset) {
      setAddProviderForm({ ...preset, api_key: '', is_active: true })
    }
  }

  const handleAddProvider = async () => {
    if (!addProviderForm.name.trim()) {
      toast.error('请输入厂家ID')
      return
    }
    if (!addProviderForm.display_name.trim()) {
      toast.error('请输入显示名称')
      return
    }
    if (addProviderForm.supported_features.length === 0) {
      toast.error('请至少选择一个支持的功能')
      return
    }
    setAddProviderSaving(true)
    try {
      const payload: any = { ...addProviderForm }
      // 如果 api_key 为空，删除该字段
      if (!payload.api_key) delete payload.api_key
      await apiClient.post('/config/llm/providers', payload)
      toast.success('厂家添加成功')
      setShowAddProvider(false)
      setAddProviderForm({ name: '', display_name: '', description: '', website: '', api_doc_url: '', default_base_url: '', api_key: '', supported_features: [], is_active: true })
      setSelectedPreset('')
      loadModelConfig()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '添加厂家失败')
    } finally {
      setAddProviderSaving(false)
    }
  }

  const handleSaveModel = async () => {
    if (!modelForm.provider || !modelForm.model_name.trim()) {
      toast.error('请选择厂家并填写模型名称')
      return
    }
    setModelSaving(true)
    try {
      await apiClient.post('/config/llm', {
        ...modelForm,
        model_name: modelForm.model_name.trim(),
        api_key: undefined,
      })
      toast.success('模型配置已保存')
      setModelForm(prev => ({ ...EMPTY_MODEL_FORM, provider: prev.provider }))
      loadModelConfig()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '保存模型配置失败')
    } finally {
      setModelSaving(false)
    }
  }

  const handleClearCache = async () => {
    setClearingCache(true)
    try {
      const keys = Object.keys(sessionStorage).filter(k => k.startsWith('analysis_'))
      keys.forEach(k => sessionStorage.removeItem(k))
      localStorage.removeItem('analysis_cache')
      toast.success(`已清除 ${keys.length} 条分析缓存`)
    } catch {
      toast.error('清除缓存失败')
    } finally {
      setClearingCache(false)
    }
  }

  const getJobId = (job: SchedulerJob) => String(job.job_id || job.id || '')

  const loadSchedulerJobs = async () => {
    setSchedulerLoading(true)
    try {
      const response = await apiClient.get('/scheduler/jobs')
      const data = response.data?.data ?? response.data
      setSchedulerJobs(Array.isArray(data) ? data : [])
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '加载系统任务失败')
    } finally {
      setSchedulerLoading(false)
    }
  }

  const handleSchedulerAction = async (action: 'pause' | 'resume' | 'trigger', jobId: string) => {
    try {
      await apiClient.post(`/scheduler/jobs/${jobId}/${action}`)
      toast.success('系统任务操作已提交')
      loadSchedulerJobs()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '系统任务操作失败，请确认管理员权限')
    }
  }

  const renderModelTab = () => (
    <div className="space-y-4">
      <Panel icon={Cpu} title="默认模型">
        {modelLoading ? (
          <div className="flex items-center gap-2 text-white/40">
            <Loader2 className="w-4 h-4 animate-spin" />
            加载模型配置...
          </div>
        ) : (
          <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-white/60 mb-2">快速分析模型</label>
              <select
                value={modelDefaults.quick}
                onChange={e => setModelDefaults(prev => ({ ...prev, quick: e.target.value }))}
                className={inputClass('w-full')}
              >
                <option value="">请选择模型</option>
                {enabledModels.map(model => (
                  <option key={`${model.provider}:${model.model_name}`} value={model.model_name}>
                    {model.model_display_name || model.model_name} · {model.provider}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-white/60 mb-2">深度分析模型</label>
              <select
                value={modelDefaults.deep}
                onChange={e => setModelDefaults(prev => ({ ...prev, deep: e.target.value }))}
                className={inputClass('w-full')}
              >
                <option value="">请选择模型</option>
                {enabledModels.map(model => (
                  <option key={`${model.provider}:${model.model_name}`} value={model.model_name}>
                    {model.model_display_name || model.model_name} · {model.provider}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="mt-5 flex justify-end">
            <button
              onClick={handleSaveModelDefaults}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-sm font-medium hover:opacity-90"
            >
              <Save className="w-4 h-4" />
              保存默认模型
            </button>
          </div>
          </>
        )}
      </Panel>

      <Panel icon={Key} title="模型厂家">
        {/* 添加厂家按钮 */}
        <div className="mb-4">
          <button
            onClick={() => setShowAddProvider(prev => !prev)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-500/20 text-blue-300 border border-blue-500/30 text-sm hover:bg-blue-500/30 transition-all"
          >
            <Plus className="w-4 h-4" />
            {showAddProvider ? '收起' : '添加厂家'}
          </button>
        </div>

        {/* 添加厂家表单 */}
        {showAddProvider && (
          <div className="mb-6 p-4 rounded-xl border border-blue-500/20 bg-blue-500/5">
            <h4 className="text-white font-medium mb-4">添加新厂家</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-white/60 mb-1">快速选择</label>
                <select
                  value={selectedPreset}
                  onChange={e => handlePresetChange(e.target.value)}
                  className={inputClass('w-full')}
                >
                  <option value="">— 选择预设厂家或手动填写 —</option>
                  {PRESET_PROVIDERS.map(p => (
                    <option key={p.name} value={p.name}>{p.display_name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-1">厂家ID <span className="text-red-400">*</span></label>
                <input
                  value={addProviderForm.name}
                  onChange={e => setAddProviderForm(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="如: openai, deepseek"
                  className={inputClass('w-full')}
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-1">显示名称 <span className="text-red-400">*</span></label>
                <input
                  value={addProviderForm.display_name}
                  onChange={e => setAddProviderForm(prev => ({ ...prev, display_name: e.target.value }))}
                  placeholder="如: OpenAI, DeepSeek"
                  className={inputClass('w-full')}
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-1">默认API地址</label>
                <input
                  value={addProviderForm.default_base_url}
                  onChange={e => setAddProviderForm(prev => ({ ...prev, default_base_url: e.target.value }))}
                  placeholder="https://api.openai.com/v1"
                  className={inputClass('w-full')}
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-1">API Key</label>
                <input
                  type="password"
                  value={addProviderForm.api_key}
                  onChange={e => setAddProviderForm(prev => ({ ...prev, api_key: e.target.value }))}
                  placeholder="留空则使用环境变量"
                  className={inputClass('w-full')}
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm text-white/60 mb-1">支持功能 <span className="text-red-400">*</span></label>
                <div className="flex flex-wrap gap-2">
                  {['chat', 'completion', 'embedding', 'vision', 'function_calling', 'streaming'].map(feature => (
                    <label key={feature} className="flex items-center gap-1.5 text-sm text-white/70 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={addProviderForm.supported_features.includes(feature)}
                        onChange={e => {
                          setAddProviderForm(prev => ({
                            ...prev,
                            supported_features: e.target.checked
                              ? [...prev.supported_features, feature]
                              : prev.supported_features.filter(f => f !== feature)
                          }))
                        }}
                        className="rounded"
                      />
                      {feature}
                    </label>
                  ))}
                </div>
              </div>
              <div className="md:col-span-2">
                <label className="flex items-center gap-2 text-white/70 text-sm">
                  <input
                    type="checkbox"
                    checked={addProviderForm.is_active}
                    onChange={e => setAddProviderForm(prev => ({ ...prev, is_active: e.target.checked }))}
                    className="rounded"
                  />
                  启用该厂家
                </label>
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-3">
              <button
                onClick={() => { setShowAddProvider(false); setSelectedPreset(''); setAddProviderForm({ name: '', display_name: '', description: '', website: '', api_doc_url: '', default_base_url: '', api_key: '', supported_features: [], is_active: true }) }}
                className="px-4 py-2 rounded-lg bg-white/5 text-white/60 text-sm hover:bg-white/10"
              >
                取消
              </button>
              <button
                onClick={handleAddProvider}
                disabled={addProviderSaving}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-sm font-medium disabled:opacity-50"
              >
                {addProviderSaving && <Loader2 className="w-4 h-4 animate-spin" />}
                添加厂家
              </button>
            </div>
          </div>
        )}

        <div className="space-y-3">
          {providers.length === 0 && !showAddProvider ? (
            <p className="text-white/40 text-sm">暂无厂家配置，请点击上方"添加厂家"</p>
          ) : providers.map(provider => (
            <div key={provider.id} className="rounded-xl border border-white/5 bg-white/[0.03] p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-white font-medium">{provider.display_name || provider.name}</p>
                    <span className={clsx('px-2 py-0.5 rounded-full text-xs', provider.is_active ? 'bg-green-500/10 text-green-400' : 'bg-white/10 text-white/40')}>
                      {provider.is_active ? '启用' : '停用'}
                    </span>
                    <span className={clsx('px-2 py-0.5 rounded-full text-xs', provider.api_key ? 'bg-blue-500/10 text-blue-400' : 'bg-amber-500/10 text-amber-400')}>
                      {provider.api_key ? `Key: ${provider.api_key}` : '未配置 Key'}
                    </span>
                  </div>
                  <p className="text-white/35 text-xs mt-1">{provider.name}</p>
                  {provider.default_base_url && <p className="text-white/35 text-xs mt-1">{provider.default_base_url}</p>}
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="password"
                    value={providerKeys[provider.id] || ''}
                    onChange={e => setProviderKeys(prev => ({ ...prev, [provider.id]: e.target.value }))}
                    placeholder="输入新 API Key"
                    className={inputClass('w-56')}
                  />
                  <button
                    onClick={() => handleSaveProviderKey(provider)}
                    className="px-3 py-2 rounded-lg bg-blue-500/20 text-blue-300 border border-blue-500/30 text-sm hover:bg-blue-500/30"
                  >
                    保存 Key
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel icon={Cpu} title="模型清单">
        {/* 添加模型表单 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm text-white/60 mb-1">模型厂家</label>
            <select
              value={modelForm.provider}
              onChange={e => setModelForm(prev => ({ ...prev, provider: e.target.value }))}
              className={inputClass('w-full')}
            >
              <option value="">请选择厂家</option>
              {providers.map(provider => (
                <option key={provider.name} value={provider.name}>{provider.display_name || provider.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-1">模型名称</label>
            <input
              value={modelForm.model_name}
              onChange={e => setModelForm(prev => ({ ...prev, model_name: e.target.value }))}
              placeholder="例如 qwen-max / deepseek-chat"
              className={inputClass('w-full')}
            />
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-1">显示名称</label>
            <input
              value={modelForm.model_display_name || ''}
              onChange={e => setModelForm(prev => ({ ...prev, model_display_name: e.target.value }))}
              className={inputClass('w-full')}
            />
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-1">API Base（可选）</label>
            <input
              value={modelForm.api_base || ''}
              onChange={e => setModelForm(prev => ({ ...prev, api_base: e.target.value }))}
              placeholder="默认使用厂家 Base URL"
              className={inputClass('w-full')}
            />
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-1">Max Tokens</label>
            <input
              type="number"
              value={modelForm.max_tokens}
              onChange={e => setModelForm(prev => ({ ...prev, max_tokens: Number(e.target.value) }))}
              className={inputClass('w-full')}
            />
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-1">Temperature</label>
            <input
              type="number"
              min={0}
              max={2}
              step={0.1}
              value={modelForm.temperature}
              onChange={e => setModelForm(prev => ({ ...prev, temperature: Number(e.target.value) }))}
              className={inputClass('w-full')}
            />
          </div>
        </div>
        <div className="flex items-center justify-between mb-4">
          <label className="flex items-center gap-2 text-white/70 text-sm">
            <input
              type="checkbox"
              checked={modelForm.enabled}
              onChange={e => setModelForm(prev => ({ ...prev, enabled: e.target.checked }))}
              className="rounded"
            />
            启用模型
          </label>
          <button
            onClick={handleSaveModel}
            disabled={modelSaving}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-sm font-medium disabled:opacity-50"
          >
            {modelSaving && <Loader2 className="w-4 h-4 animate-spin" />}
            保存模型
          </button>
        </div>

        {/* 模型列表 */}
        <div className="space-y-3">
          {llmConfigs.length === 0 ? (
            <p className="text-white/40 text-sm">暂无模型配置，请在上方添加。</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-white/40 border-b border-white/5">
                    <th className="text-left py-2">厂家</th>
                    <th className="text-left py-2">模型名称</th>
                    <th className="text-left py-2">能力</th>
                    <th className="text-left py-2">Token</th>
                    <th className="text-left py-2">温度</th>
                    <th className="text-left py-2">状态</th>
                  </tr>
                </thead>
                <tbody>
                  {llmConfigs.map(model => (
                    <tr key={`${model.provider}:${model.model_name}`} className="border-b border-white/5 last:border-0">
                      <td className="py-3 text-white/70">{model.provider}</td>
                      <td className="py-3">
                        <button
                          onClick={() => setModelForm({ ...EMPTY_MODEL_FORM, ...model })}
                          className="text-blue-300 hover:text-blue-200"
                        >
                          {model.model_display_name || model.model_name}
                        </button>
                        <p className="text-white/30 text-xs">{model.model_name}</p>
                      </td>
                      <td className="py-3 text-white/70">L{model.capability_level || 2}</td>
                      <td className="py-3 text-white/70">{model.max_tokens}</td>
                      <td className="py-3 text-white/70">{model.temperature}</td>
                      <td className="py-3">
                        <span className={clsx('px-2 py-0.5 rounded-full text-xs', model.enabled ? 'bg-green-500/10 text-green-400' : 'bg-white/10 text-white/40')}>
                          {model.enabled ? '启用' : '停用'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Panel>

    </div>
  )

  const renderSystemTasksTab = () => (
    <Panel icon={CalendarClock} title="系统任务">
      {schedulerLoading ? (
        <div className="flex items-center gap-2 text-white/40">
          <Loader2 className="w-4 h-4 animate-spin" />
          加载系统任务...
        </div>
      ) : schedulerJobs.length === 0 ? (
        <p className="text-white/40 text-sm">暂无系统任务</p>
      ) : (
        <div className="divide-y divide-white/5">
          {schedulerJobs.map(job => {
            const jobId = getJobId(job)
            const isPaused = job.paused || job.status === 'paused' || job.enabled === false || !job.next_run_time
            return (
              <div key={jobId} className="flex flex-col gap-3 py-4 lg:flex-row lg:items-center lg:justify-between">
                <div className="min-w-0">
                  <div className="flex items-center gap-3">
                    <p className="text-white font-medium">{job.display_name || job.name || jobId}</p>
                    <span className={clsx('px-2 py-0.5 rounded-full border text-xs', isPaused ? 'bg-amber-500/10 text-amber-300 border-amber-500/20' : 'bg-green-500/10 text-green-300 border-green-500/20')}>
                      {isPaused ? '已暂停' : '运行中'}
                    </span>
                  </div>
                  <p className="text-white/40 text-sm mt-1">{job.description || job.trigger || '系统调度任务'}</p>
                  <p className="text-white/30 text-xs mt-1">下次执行：{job.next_run_time || '--'}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => handleSchedulerAction('trigger', jobId)} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white/70 text-sm hover:bg-white/10">
                    <Play className="w-4 h-4" />
                    运行
                  </button>
                  <button onClick={() => handleSchedulerAction(isPaused ? 'resume' : 'pause', jobId)} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white/70 text-sm hover:bg-white/10">
                    {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                    {isPaused ? '恢复' : '暂停'}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </Panel>
  )

  const renderTab = () => {
    if (activeTab === 'general') {
      return (
        <Panel icon={User} title="通用设置">
          <SettingRow title="用户名"><span className="text-white/40 text-sm">{user?.username || '—'}（不可更改）</span></SettingRow>
          <SettingRow title="邮箱" description="用于接收分析报告">
            <input value={settings.email} onChange={e => update('email', e.target.value)} className={inputClass('w-64 text-right')} />
          </SettingRow>
          <SettingRow title="语言">
            <select value={settings.language} onChange={e => update('language', e.target.value)} className={inputClass()}>
              <option value="zh-CN">简体中文</option>
              <option value="en-US">English</option>
            </select>
          </SettingRow>
          <SettingRow title="时区">
            <select value={settings.timezone} onChange={e => update('timezone', e.target.value)} className={inputClass()}>
              <option value="Asia/Shanghai">北京时间 (UTC+8)</option>
              <option value="America/New_York">纽约时间</option>
              <option value="Europe/London">伦敦时间</option>
            </select>
          </SettingRow>
        </Panel>
      )
    }

    if (activeTab === 'analysis') {
      return (
        <Panel icon={TrendingUp} title="分析偏好">
          <SettingRow title="默认市场">
            <select value={settings.defaultMarket} onChange={e => update('defaultMarket', e.target.value as AppSettings['defaultMarket'])} className={inputClass()}>
              <option value="A股">A股</option>
              <option value="美股">美股</option>
              <option value="港股">港股</option>
            </select>
          </SettingRow>
          <SettingRow title="默认分析深度">
            <select value={settings.defaultDepth} onChange={e => update('defaultDepth', Number(e.target.value) as AppSettings['defaultDepth'])} className={inputClass()}>
              <option value={1}>1级 - 快速分析</option>
              <option value={2}>2级 - 基础分析</option>
              <option value={3}>3级 - 标准分析</option>
              <option value={4}>4级 - 深度分析</option>
              <option value={5}>5级 - 全面分析</option>
            </select>
          </SettingRow>
          <SettingRow title="自动刷新"><Toggle checked={settings.autoRefresh} onChange={v => update('autoRefresh', v)} /></SettingRow>
          <SettingRow title="刷新间隔" description="单位：秒">
            <input type="number" min={10} max={300} disabled={!settings.autoRefresh} value={settings.refreshInterval} onChange={e => update('refreshInterval', Number(e.target.value))} className={inputClass('w-20 text-right disabled:opacity-40')} />
          </SettingRow>
        </Panel>
      )
    }

    if (activeTab === 'models') return renderModelTab()

    if (activeTab === 'systemTasks') return renderSystemTasksTab()

    if (activeTab === 'notifications') {
      return (
        <Panel icon={Bell} title="通知设置">
          <SettingRow title="桌面通知" description="浏览器桌面推送通知（需授权）">
            <Toggle checked={settings.notifyDesktop} onChange={v => update('notifyDesktop', v)} />
          </SettingRow>
          <SettingRow title="分析完成通知">
            <Toggle checked={settings.notifyAnalysisComplete} onChange={v => update('notifyAnalysisComplete', v)} />
          </SettingRow>
        </Panel>
      )
    }

    return (
      <Panel icon={Database} title="缓存管理">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white font-medium">分析缓存</p>
            <p className="text-white/40 text-sm mt-0.5">包含会话存储中的分析结果与任务状态</p>
          </div>
          <button onClick={handleClearCache} disabled={clearingCache} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm hover:bg-red-500/20 disabled:opacity-50">
            {clearingCache ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
            清除缓存
          </button>
        </div>
      </Panel>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">系统设置</h1>

        </div>
        <button
          onClick={activeTab === 'models' ? loadModelConfig : activeTab === 'systemTasks' ? loadSchedulerJobs : handleSaveLocalSettings}
          disabled={saving || modelLoading || schedulerLoading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white/70 hover:text-white hover:bg-white/10"
        >
          {activeTab === 'models' || activeTab === 'systemTasks'
            ? <RefreshCw className={clsx('w-4 h-4', (modelLoading || schedulerLoading) && 'animate-spin')} />
            : saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          {activeTab === 'models' || activeTab === 'systemTasks' ? '刷新配置' : '保存本地设置'}
        </button>
      </div>

      <div className="grid grid-cols-[220px_1fr] gap-6">
        <div className="space-y-1">
          {TABS.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={clsx(
                'w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all text-left',
                activeTab === tab.key
                  ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                  : 'text-white/55 hover:text-white hover:bg-white/5'
              )}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
        <div className="min-w-0">{renderTab()}</div>
      </div>
    </div>
  )
}
