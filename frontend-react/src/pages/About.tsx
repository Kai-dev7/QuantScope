import { Card, CardContent } from '@/components/ui/card'
import { Zap, Github, Mail, Globe } from 'lucide-react'

export default function About() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="text-center">
        <div className="relative inline-block mb-6">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/30">
            <Zap className="w-10 h-10 text-white" />
          </div>
          <div className="absolute -inset-3 bg-gradient-to-r from-blue-500 to-cyan-400 rounded-3xl blur opacity-30" />
        </div>
        <h1 className="text-3xl font-bold text-white">QuantScope</h1>
        <p className="text-white/60 mt-2">AI 智能投研平台</p>
        <p className="text-white/40 text-sm mt-1">版本 1.0.0</p>
      </div>

      <Card className="gradient-card border-white/5">
        <CardContent className="p-6 space-y-6">
          <div>
            <h2 className="text-white font-semibold mb-3">平台介绍</h2>
            <p className="text-white/60 text-sm leading-relaxed">
              QuantScope 是一个基于多智能体协作的 A 股深度分析系统，模拟顶级投研机构的决策闭环，
              通过多个专业 AI Agent 的并行分析与综合裁决，为投资者提供结构化的交易建议。
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-white/5">
              <p className="text-white/40 text-sm">分析师数量</p>
              <p className="text-2xl font-bold text-white mt-1">4</p>
            </div>
            <div className="p-4 rounded-xl bg-white/5">
              <p className="text-white/40 text-sm">支持市场</p>
              <p className="text-2xl font-bold text-white mt-1">CN/HK/US</p>
            </div>
          </div>

          <div>
            <h2 className="text-white font-semibold mb-3">核心功能</h2>
            <ul className="space-y-2 text-sm text-white/60">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                多维度并行分析：财务、估值、风险、行业
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
                实时任务追踪与断点续跑
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                结构化研报与决策卡片
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                实时市场数据与新闻整合
              </li>
            </ul>
          </div>

          <div>
            <h2 className="text-white font-semibold mb-3">技术栈</h2>
            <div className="flex flex-wrap gap-2">
              {['Python', 'FastAPI', 'Vue 3', 'TypeScript', 'MongoDB', 'WebSocket', 'LLM'].map(
                (tech) => (
                  <span
                    key={tech}
                    className="px-3 py-1 rounded-full bg-white/5 text-white/60 text-sm border border-white/10"
                  >
                    {tech}
                  </span>
                )
              )}
            </div>
          </div>

          <div className="flex items-center gap-4 pt-4 border-t border-white/5">
            <a
              href="#"
              className="flex items-center gap-2 text-white/40 hover:text-white text-sm transition-colors"
            >
              <Github className="w-4 h-4" />
              GitHub
            </a>
            <a
              href="#"
              className="flex items-center gap-2 text-white/40 hover:text-white text-sm transition-colors"
            >
              <Mail className="w-4 h-4" />
              联系我们
            </a>
            <a
              href="#"
              className="flex items-center gap-2 text-white/40 hover:text-white text-sm transition-colors"
            >
              <Globe className="w-4 h-4" />
              文档
            </a>
          </div>
        </CardContent>
      </Card>

      <p className="text-center text-white/20 text-xs">
        仅供学习研究，不构成投资建议。证券市场有风险，投资需谨慎。
      </p>
    </div>
  )
}
