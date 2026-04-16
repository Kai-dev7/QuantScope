# 学习中心文档

本目录包含QuantScope学习中心的所有教学内容。

## 📁 目录结构

```
docs/learning/
├── 01-ai-basics/              # AI基础知识
│   ├── what-is-ai.md          # 什么是人工智能
│   ├── what-is-llm.md         # 什么是大语言模型
│   ├── transformer.md         # Transformer架构
│   ├── training-process.md    # 模型训练过程
│   └── llm-capabilities.md    # 大模型的能力边界
│
├── 02-prompt-engineering/     # 提示词工程
│   ├── prompt-basics.md       # 提示词基础
│   ├── prompt-patterns.md     # 常用提示词模式
│   ├── best-practices.md      # 最佳实践
│   ├── few-shot-learning.md   # Few-shot学习
│   ├── chain-of-thought.md    # 思维链提示
│   └── prompt-optimization.md # 提示词优化技巧
│
├── 03-model-selection/        # 模型选择指南
│   ├── model-comparison.md    # 模型对比
│   ├── openai-models.md       # OpenAI模型系列
│   ├── chinese-models.md      # 国产模型介绍
│   └── cost-analysis.md       # 成本分析
│
├── 04-analysis-principles/    # AI分析股票原理
│   ├── multi-agent-system.md  # 多智能体系统
│   ├── debate-mechanism.md    # 辩论机制
│   ├── analysis-workflow.md   # 分析流程
│   ├── data-processing.md     # 数据处理
│   ├── technical-analysis.md  # 技术分析
│   ├── fundamental-analysis.md # 基本面分析
│   └── sentiment-analysis.md  # 情感分析
│
├── 05-risks-limitations/      # 风险与局限性
│   ├── hallucination.md       # 幻觉问题
│   ├── data-timeliness.md     # 数据时效性
│   ├── market-volatility.md   # 市场波动性
│   ├── risk-warnings.md       # 风险警示
│   └── proper-usage.md        # 正确使用方式
│
├── 06-resources/              # 源项目与论文
│   ├── tradingagents-intro.md # TradingAgents项目介绍
│   ├── paper-chinese.md       # 论文中文版
│   ├── paper-english.md       # 论文英文版
│   └── related-resources.md   # 相关资源
│
├── 07-tutorials/              # 实战教程
│   ├── quick-start.md         # 快速开始
│   ├── single-analysis.md     # 单股分析教程
│   ├── batch-analysis.md      # 批量分析教程
│   ├── screening-tutorial.md  # 筛选功能教程
│   ├── paper-trading.md       # 模拟交易教程
│   ├── custom-prompts.md      # 自定义提示词
│   ├── llm-configuration.md   # LLM配置教程
│   └── advanced-features.md   # 高级功能
│
└── 08-faq/                    # 常见问题
    ├── installation.md        # 安装问题
    ├── configuration.md       # 配置问题
    ├── data-sync.md           # 数据同步问题
    ├── analysis-issues.md     # 分析问题
    ├── llm-issues.md          # LLM相关问题
    └── troubleshooting.md     # 故障排除
```

## 📝 内容规范

### 文档格式

每篇文档应包含以下部分：

1. **标题和元信息**
   ```markdown
   # 文章标题
   
   **分类**: AI基础知识  
   **难度**: 入门/进阶/高级  
   **阅读时间**: X分钟  
   **更新日期**: YYYY-MM-DD
   ```

2. **引言**：简要介绍文章内容和学习目标

3. **正文**：详细的教学内容，使用清晰的标题层级

4. **示例代码**：如果适用，提供代码示例

5. **总结**：总结要点

6. **延伸阅读**：相关文章链接

### 写作风格

- 使用简洁明了的语言
- 避免过于专业的术语，或在使用时提供解释
- 使用实际案例和示例
- 添加图表和可视化内容
- 提供交互式演示（如果可能）

## 🎯 学习路径

### 初学者路径

1. AI基础知识 → 什么是人工智能
2. AI基础知识 → 什么是大语言模型
3. 实战教程 → 快速开始
4. 实战教程 → 单股分析教程
5. 风险与局限性 → 风险警示

### 进阶路径

1. 提示词工程 → 提示词基础
2. 提示词工程 → 最佳实践
3. AI分析股票原理 → 多智能体系统
4. AI分析股票原理 → 辩论机制
5. 实战教程 → 自定义提示词

### 高级路径

1. AI基础知识 → Transformer架构
2. 模型选择指南 → 模型对比
3. AI分析股票原理 → 分析流程详解
4. 实战教程 → 高级功能
5. 源项目与论文 → 学术论文研读

## 🤝 贡献指南

欢迎贡献学习内容！请遵循以下步骤：

1. Fork本项目
2. 在 `docs/learning/` 目录下创建或编辑Markdown文件
3. 确保内容符合上述规范
4. 提交Pull Request

## 📧 反馈

如果您发现内容错误或有改进建议，请：

1. 提交Issue
2. 发送邮件至项目维护者
3. 在社区讨论区反馈

---

## ✅ 已完成文档

### AI基础知识
- ✅ [什么是大语言模型（LLM）](./01-ai-basics/what-is-llm.md)

### 提示词工程
- ✅ [提示词基础概念](./02-prompt-engineering/prompt-basics.md)
- ✅ [提示词最佳实践](./02-prompt-engineering/best-practices.md)

### 模型选择指南
- ✅ [主流大模型对比](./03-model-selection/model-comparison.md)

### AI分析股票原理
- ✅ [多智能体系统详解](./04-analysis-principles/multi-agent-system.md)

### 风险与局限性
- ✅ [风险警示和免责声明](./05-risks-limitations/risk-warnings.md)

### 源项目与论文
- ✅ [TradingAgents项目介绍](./06-resources/tradingagents-intro.md)

### 实战教程
- ✅ [快速入门教程](./07-tutorials/getting-started.md)

### 常见问题
- ✅ [常见问题解答](./08-faq/general-questions.md)

**进度统计**：已完成 8 篇核心文档，涵盖从入门到进阶的主要内容。

