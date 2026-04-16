# 🏗️ QuantScope 项目深度架构讲解

> 本文档详细介绍 QuantScope 项目的整体架构、核心模块、数据流和设计理念。

## 📊 一、项目整体架构

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           QuantScope 系统架构                                │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                          🖥️ 前端层 (frontend/)                               │  │
│  │   Vue 3 + TypeScript + Element Plus                                         │  │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │  │
│  │   │ 股票分析 │ │ 任务中心 │ │ 配置管理 │ │ 历史记录 │ │ 用户管理 │         │  │
│  │   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘         │  │
│  └────────┼────────────┼────────────┼────────────┼────────────┼────────────────┘  │
│           │            │            │            │            │                   │
│           └────────────┴────────────┴────────────┴────────────┘                   │
│                                    ↓ HTTP/WebSocket                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                          🌐 API层 (app/routers/)                             │  │
│  │   FastAPI + JWT认证 + 中间件                                                 │  │
│  │   /api/analysis/* | /api/config/* | /api/stocks/* | /api/auth/*             │  │
│  └────────────────────────────────────────────┬────────────────────────────────┘  │
│                                               ↓                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                         ⚙️ 服务层 (app/services/)                            │  │
│  │   ┌────────────────┐ ┌────────────────┐ ┌────────────────┐                  │  │
│  │   │ SimpleAnalysis │ │ ConfigService  │ │  QueueService  │                  │  │
│  │   │    Service     │ │                │ │                │                  │  │
│  │   └───────┬────────┘ └────────────────┘ └────────────────┘                  │  │
│  └───────────┼─────────────────────────────────────────────────────────────────┘  │
│              ↓                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                    🤖 核心引擎层 (tradingagents/)                             │  │
│  │                                                                              │  │
│  │   ┌──────────────────────────────────────────────────────────────────────┐   │  │
│  │   │                    🔗 LangGraph 工作流引擎                             │   │  │
│  │   │   TradingAgentsGraph → GraphSetup → Propagator                       │   │  │
│  │   └──────────────────────────────────────────────────────────────────────┘   │  │
│  │                                    ↓                                         │  │
│  │   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │  │
│  │   │  Analysts  │ │ Researchers│ │   Trader   │ │Risk Managers│              │  │
│  │   │  分析师团队 │ │  研究员团队│ │   交易员   │ │ 风险管理团队│              │  │
│  │   └────────────┘ └────────────┘ └────────────┘ └────────────┘              │  │
│  │                                    ↓                                         │  │
│  │   ┌──────────────────────────────────────────────────────────────────────┐   │  │
│  │   │                    📊 数据流层 (dataflows/)                           │   │  │
│  │   │   DataSourceManager | Cache | Providers (US/CN/HK)                   │   │  │
│  │   └──────────────────────────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                               ↓                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                         💾 数据存储层                                        │  │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │  │
│  │   │ MongoDB  │  │  Redis   │  │ 文件系统  │  │ 外部API  │                   │  │
│  │   │ 持久存储  │  │ 缓存/队列│  │  结果存储 │  │ 数据源    │                   │  │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘                   │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 二、目录结构详解

### 1. 核心引擎 - `tradingagents/`

这是项目的**智能分析核心**，基于 LangGraph 构建的多智能体协作系统：

```
tradingagents/
├── agents/                    # 🤖 智能体定义
│   ├── analysts/              # 分析师智能体
│   │   ├── market_analyst.py      # 市场分析师（K线、技术指标）
│   │   ├── fundamentals_analyst.py # 基本面分析师（财务数据）
│   │   ├── news_analyst.py         # 新闻分析师
│   │   └── social_media_analyst.py # 社交媒体分析师
│   ├── researchers/           # 研究员智能体
│   │   ├── bull_researcher.py     # 看涨研究员（构建买入论据）
│   │   └── bear_researcher.py     # 看跌研究员（构建卖出论据）
│   ├── managers/              # 管理者智能体
│   │   ├── research_manager.py    # 研究经理（综合多空意见）
│   │   └── risk_manager.py        # 风险经理（最终决策）
│   ├── risk_mgmt/             # 风险评估智能体
│   │   ├── aggresive_debator.py   # 激进风险分析师
│   │   ├── conservative_debator.py # 保守风险分析师
│   │   └── neutral_debator.py     # 中性风险分析师
│   ├── trader/                # 交易员智能体
│   │   └── trader.py              # 制定交易策略
│   └── utils/
│       ├── agent_states.py        # ⭐ 智能体状态定义
│       ├── agent_utils.py         # 智能体工具函数
│       └── memory.py              # 记忆系统
│
├── graph/                     # 🔗 LangGraph 工作流
│   ├── trading_graph.py           # ⭐ 主图类（入口点）
│   ├── setup.py                   # 图结构设置
│   ├── propagation.py             # 状态传播
│   ├── conditional_logic.py       # 条件边逻辑
│   └── signal_processing.py       # 信号处理
│
├── dataflows/                 # 📊 数据获取层
│   ├── interface.py               # ⭐ 统一数据接口
│   ├── data_source_manager.py     # 数据源管理器
│   ├── providers/                 # 数据提供者
│   │   ├── china/                 # A股数据源
│   │   │   ├── akshare.py
│   │   │   ├── tushare.py
│   │   │   └── baostock.py
│   │   ├── us/                    # 美股数据源
│   │   │   ├── finnhub.py
│   │   │   └── yfinance.py
│   │   └── hk/                    # 港股数据源
│   │       └── improved_hk.py
│   ├── cache/                     # 缓存系统
│   │   ├── integrated.py          # 集成缓存
│   │   └── mongodb_cache_adapter.py
│   └── news/                      # 新闻数据
│       ├── google_news.py
│       └── chinese_finance.py
│
├── llm_adapters/              # 🧠 LLM适配器
│   ├── openai_compatible_base.py  # OpenAI兼容基类
│   ├── dashscope_openai_adapter.py # 阿里百炼适配器
│   ├── deepseek_adapter.py        # DeepSeek适配器
│   └── google_openai_adapter.py   # Google AI适配器
│
└── default_config.py          # 默认配置
```

### 2. Web API层 - `app/`

这是**后端服务层**，基于 FastAPI 构建：

```
app/
├── main.py                    # ⭐ FastAPI 应用入口
├── core/                      # 核心基础设施
│   ├── config.py                  # 环境配置（从.env读取）
│   ├── database.py                # MongoDB连接管理
│   ├── redis_client.py            # Redis连接管理
│   ├── unified_config.py          # 统一配置管理
│   └── config_bridge.py           # 配置桥接（DB→ENV）
│
├── models/                    # 数据模型（Pydantic）
│   ├── analysis.py                # 分析任务模型
│   ├── config.py                  # 配置模型
│   ├── user.py                    # 用户模型
│   └── notification.py            # 通知模型
│
├── routers/                   # API路由（37个模块）
│   ├── analysis.py                # ⭐ 股票分析API
│   ├── config.py                  # ⭐ 配置管理API
│   ├── auth_db.py                 # 认证API
│   ├── stocks.py                  # 股票数据API
│   ├── queue.py                   # 任务队列API
│   ├── sse.py                     # Server-Sent Events
│   └── ...
│
├── services/                  # 业务服务层（62个模块）
│   ├── simple_analysis_service.py # ⭐ 核心分析服务
│   ├── config_service.py          # 配置服务
│   ├── config_provider.py         # 配置提供者
│   ├── queue_service.py           # 队列服务
│   ├── memory_state_manager.py    # 内存状态管理
│   ├── redis_progress_tracker.py  # 进度跟踪
│   └── model_capability_service.py # 模型能力服务
│
├── middleware/                # 中间件
│   ├── error_handler.py           # 全局错误处理
│   ├── rate_limit.py              # 速率限制
│   └── operation_log_middleware.py # 操作日志
│
└── worker/                    # 后台任务Worker
    ├── analysis_worker.py         # 分析任务Worker
    └── *_sync_service.py          # 各种数据同步服务
```

### 3. 前端层 - `frontend/`

基于 **Vue 3 + TypeScript + Element Plus** 构建：

```
frontend/src/
├── api/                       # API封装
│   ├── analysis.ts                # 分析API
│   ├── config.ts                  # 配置API
│   └── request.ts                 # HTTP请求封装
│
├── views/                     # 页面视图
│   ├── Analysis/
│   │   ├── SingleAnalysis.vue     # ⭐ 单股分析页面
│   │   ├── BatchAnalysis.vue      # 批量分析页面
│   │   └── AnalysisHistory.vue    # 历史记录
│   ├── Settings/
│   │   └── ConfigManagement.vue   # 配置管理页面
│   ├── Dashboard/
│   └── ...
│
├── components/                # 公共组件
│   ├── ModelConfig.vue            # 模型配置组件
│   └── DeepModelSelector.vue      # 模型选择器
│
└── stores/                    # Pinia状态管理
    └── auth.ts                    # 认证状态
```

---

## 🤖 三、多智能体协作机制详解

### 1. 智能体状态定义 (AgentState)

文件: `tradingagents/agents/utils/agent_states.py`

```python
class AgentState(MessagesState):
    """主状态类 - 贯穿整个分析流程"""
    
    # 基础信息
    company_of_interest: str    # 分析的股票代码
    trade_date: str             # 分析日期
    sender: str                 # 当前消息发送者
    
    # 📊 分析师报告
    market_report: str          # 市场分析师报告
    sentiment_report: str       # 社媒分析师报告
    news_report: str            # 新闻分析师报告
    fundamentals_report: str    # 基本面分析师报告
    
    # 🐂🐻 研究团队辩论状态
    investment_debate_state: InvestDebateState
    investment_plan: str        # 研究团队投资计划
    
    # 💼 交易员决策
    trader_investment_plan: str # 交易员投资计划
    
    # ⚠️ 风险管理团队辩论状态
    risk_debate_state: RiskDebateState
    final_trade_decision: str   # 最终交易决策
```

### 2. 研究团队辩论状态 (InvestDebateState)

```python
class InvestDebateState(TypedDict):
    """多头/空头研究员辩论状态"""
    bull_history: str         # 看涨研究员的论据历史
    bear_history: str         # 看跌研究员的论据历史
    history: str              # 完整对话历史
    current_response: str     # 最新回复
    judge_decision: str       # 研究经理的最终裁决
    count: int                # 当前辩论轮次
```

### 3. 风险管理辩论状态 (RiskDebateState)

```python
class RiskDebateState(TypedDict):
    """风险管理团队辩论状态"""
    risky_history: str          # 激进分析师历史
    safe_history: str           # 保守分析师历史
    neutral_history: str        # 中性分析师历史
    current_risky_response: str # 激进分析师当前回复
    current_safe_response: str  # 保守分析师当前回复
    current_neutral_response: str # 中性分析师当前回复
    judge_decision: str         # 风险经理最终决策
    count: int                  # 辩论轮次
```

### 4. 多智能体工作流图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         分析工作流程图                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  START ──► 市场分析师 ──► 基本面分析师 ──► 新闻分析师 ──►          │
│                                                                     │
│            ┌──────────────────────────────────────────┐             │
│            │        研究团队辩论阶段                   │             │
│            │   ┌──────────┐      ┌──────────┐        │             │
│            │   │ 看涨研究员│◄────►│ 看跌研究员│        │             │
│            │   └────┬─────┘      └─────┬────┘        │             │
│            │        │                  │              │             │
│            │        └────────┬─────────┘              │             │
│            │                 ▼                        │             │
│            │           研究经理                       │             │
│            └──────────────────────────────────────────┘             │
│                              │                                      │
│                              ▼                                      │
│                           交易员                                    │
│                              │                                      │
│            ┌─────────────────┴─────────────────┐                   │
│            │        风险管理团队辩论            │                   │
│            │  ┌────────┐┌────────┐┌────────┐  │                   │
│            │  │激进分析│││保守分析│││中性分析│  │                   │
│            │  └────┬───┘└────┬───┘└────┬───┘  │                   │
│            │       └─────────┼─────────┘       │                   │
│            │                 ▼                 │                   │
│            │             风险经理              │                   │
│            └───────────────────────────────────┘                   │
│                              │                                      │
│                              ▼                                      │
│                            END                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**各节点功能说明：**

| 节点 | 功能 | 输出 |
|------|------|------|
| **市场分析师** | 分析K线、技术指标、成交量 | `market_report` |
| **基本面分析师** | 分析财务数据、估值指标 | `fundamentals_report` |
| **新闻分析师** | 分析相关新闻、公告 | `news_report` |
| **社媒分析师** | 分析社交媒体情绪（仅美股） | `sentiment_report` |
| **看涨研究员** | 构建看多论据 | `bull_history` |
| **看跌研究员** | 构建看空论据 | `bear_history` |
| **研究经理** | 综合多空意见形成共识 | `research_team_decision` |
| **交易员** | 制定交易策略 | `trader_investment_plan` |
| **激进分析师** | 评估激进风险 | `risky_history` |
| **保守分析师** | 评估保守风险 | `safe_history` |
| **中性分析师** | 平衡风险评估 | `neutral_history` |
| **风险经理** | 最终风险决策 | `final_trade_decision` |

---

## 🔗 四、LangGraph 工作流详解

### 1. 核心类 - TradingAgentsGraph

文件: `tradingagents/graph/trading_graph.py`

```python
class TradingAgentsGraph:
    """主图类 - 编排整个多智能体协作流程"""
    
    def __init__(self, selected_analysts, debug, config):
        # 1. 初始化LLM实例
        self.quick_thinking_llm = create_llm(...)  # 快速模型
        self.deep_thinking_llm = create_llm(...)   # 深度模型
        
        # 2. 初始化工具包（数据获取工具）
        self.toolkit = Toolkit(...)
        
        # 3. 初始化记忆系统
        self.memories = create_memories(...)
        
        # 4. 构建LangGraph工作流
        self.graph = GraphSetup(...).setup_graph(selected_analysts)
    
    def propagate(self, company_name, trade_date):
        """执行分析流程"""
        # 创建初始状态
        init_state = self.propagator.create_initial_state(company_name, trade_date)
        
        # 运行图
        for step in self.graph.stream(init_state):
            # 处理每个节点的输出
            ...
        
        return final_state, decision
```

### 2. 图结构设置 - GraphSetup

文件: `tradingagents/graph/setup.py`

```python
def setup_graph(self, selected_analysts):
    """构建LangGraph状态图"""
    
    workflow = StateGraph(AgentState)
    
    # 1️⃣ 添加分析师节点
    for analyst in selected_analysts:
        workflow.add_node(f"{analyst} Analyst", create_analyst_node())
        workflow.add_node(f"tools_{analyst}", ToolNode())
    
    # 2️⃣ 添加研究团队节点
    workflow.add_node("Bull Researcher", bull_researcher_node)
    workflow.add_node("Bear Researcher", bear_researcher_node)
    workflow.add_node("Research Manager", research_manager_node)
    
    # 3️⃣ 添加交易员节点
    workflow.add_node("Trader", trader_node)
    
    # 4️⃣ 添加风险管理节点
    workflow.add_node("Risky Analyst", risky_analyst_node)
    workflow.add_node("Safe Analyst", safe_analyst_node)
    workflow.add_node("Neutral Analyst", neutral_analyst_node)
    workflow.add_node("Risk Manager", risk_manager_node)
    
    # 5️⃣ 连接边 - 定义执行顺序
    workflow.add_edge(START, first_analyst)
    # ... 连接所有节点
    
    return workflow.compile()
```

---

## ⚙️ 五、配置系统架构

系统采用**多层配置架构**，支持灵活的配置管理：

```
┌─────────────────────────────────────────────────────────────────┐
│                        配置来源优先级                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1️⃣ 环境变量 (.env)           ← 最高优先级（敏感信息）         │
│      ↓                                                          │
│   2️⃣ MongoDB (system_configs)  ← 数据库配置（可通过Web管理）    │
│      ↓                                                          │
│   3️⃣ JSON文件 (config/*.json)  ← 文件配置（兼容旧版本）         │
│      ↓                                                          │
│   4️⃣ 代码默认值                ← 最低优先级                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 关键配置服务

#### 1. ConfigService - 配置服务

文件: `app/services/config_service.py`

```python
class ConfigService:
    """配置管理服务 - 负责配置的CRUD操作"""
    
    async def get_system_config(self) -> SystemConfig:
        """获取系统配置（从MongoDB）"""
        
    async def save_system_config(self, config: SystemConfig) -> bool:
        """保存系统配置（到MongoDB）"""
        
    async def update_system_settings(self, settings: Dict) -> bool:
        """更新系统设置"""
```

#### 2. ConfigProvider - 配置提供者

文件: `app/services/config_provider.py`

```python
class ConfigProvider:
    """配置提供者 - 合并多来源配置"""
    
    async def get_effective_system_settings(self) -> Dict:
        """获取有效的系统设置
        
        优先级: 环境变量 > 数据库配置 > 默认值
        """
        # 1. 从数据库读取
        db_settings = await config_service.get_system_settings()
        
        # 2. 环境变量覆盖
        for key in KNOWN_ENV_KEYS:
            env_value = os.getenv(key)
            if env_value:
                db_settings[key] = env_value
        
        return db_settings
```

---

## 💾 六、数据存储架构

### 1. MongoDB 集合设计

```
MongoDB Database: tradingagents
├── users                    # 用户信息
├── analysis_tasks           # 分析任务（进行中）
├── analysis_reports         # 分析报告（已完成）
├── system_configs           # 系统配置
├── llm_providers            # LLM厂家配置
├── model_catalogs           # 模型目录
├── favorites                # 用户收藏
├── operation_logs           # 操作日志
└── notifications            # 通知消息
```

### 2. Redis 用途

```
Redis Keys:
├── analysis:task:{task_id}         # 任务状态缓存
├── analysis:progress:{task_id}     # 任务进度
├── queue:analysis:pending          # 待处理队列
├── queue:analysis:processing       # 处理中队列
├── cache:stock:{symbol}            # 股票数据缓存
└── session:{user_id}               # 用户会话
```

---

## 🔄 七、数据流详解

### 1. 股票数据获取流程

```
┌──────────────────────────────────────────────────────────────────────┐
│                       数据获取流程                                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   分析师调用                     数据源管理器                         │
│   ┌─────────┐                   ┌─────────────────┐                 │
│   │ Market  │ ──get_price()──►  │ DataSourceManager│                │
│   │ Analyst │                   │                  │                │
│   └─────────┘                   │  1. 检查缓存     │                │
│                                 │  2. 优先级轮询   │                │
│                                 │  3. 降级策略     │                │
│                                 └────────┬────────┘                 │
│                                          ↓                          │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │                      数据提供者层                             │  │
│   │                                                              │  │
│   │   A股数据源                港股数据源              美股数据源   │  │
│   │   ┌─────────┐             ┌─────────┐           ┌─────────┐  │  │
│   │   │ AKShare │             │ AKShare │           │ Finnhub │  │  │
│   │   │ Tushare │             │ YFinance│           │ YFinance│  │  │
│   │   │ Baostock│             └─────────┘           │AlphaVant│  │  │
│   │   └─────────┘                                   └─────────┘  │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                                          ↓                          │
│                                   ┌─────────────┐                   │
│                                   │    缓存层   │                   │
│                                   │ MongoDB/File│                   │
│                                   └─────────────┘                   │
└──────────────────────────────────────────────────────────────────────┘
```

### 2. 分析结果数据流

```
分析完成后的数据流向：

TradingAgentsGraph.propagate()
        ↓
    返回 (state, decision)
        ↓
SimpleAnalysisService._run_analysis_sync()
        ↓
    提取报告内容 (reports)
    格式化决策 (decision)
        ↓
    ┌─────────────────────────────────────┐
    │           结果保存                   │
    │                                      │
    │  1. 内存状态 (MemoryStateManager)   │
    │  2. MongoDB (analysis_reports)      │
    │  3. 文件系统 (results/{symbol}/)    │
    └─────────────────────────────────────┘
        ↓
    前端轮询获取结果
```

---

## 🧠 八、LLM 集成架构

### 1. LLM适配器设计

系统通过适配器模式支持多种LLM提供商：

```
┌─────────────────────────────────────────────────────────────────┐
│                      LLM 适配器架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   统一接口: create_llm_by_provider()                            │
│                      ↓                                          │
│   ┌────────────────────────────────────────────────────────┐    │
│   │              OpenAICompatibleBase                       │    │
│   │              (OpenAI 兼容基类)                          │    │
│   └────────────────────────────────────────────────────────┘    │
│           ↑              ↑              ↑              ↑        │
│   ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│   │  OpenAI   │  │ DashScope │  │  DeepSeek │  │  Google   │   │
│   │  Adapter  │  │  Adapter  │  │  Adapter  │  │  Adapter  │   │
│   └───────────┘  └───────────┘  └───────────┘  └───────────┘   │
│                                                                 │
│   支持的厂商：                                                   │
│   - OpenAI (gpt-4, gpt-4o, gpt-3.5-turbo)                      │
│   - 阿里百炼 (qwen-turbo, qwen-plus, qwen-max)                  │
│   - DeepSeek (deepseek-chat, deepseek-coder)                   │
│   - Google (gemini-pro, gemini-2.0-flash)                      │
│   - 智谱AI (glm-4)                                              │
│   - 硅基流动 (siliconflow)                                      │
│   - 302.AI (聚合渠道)                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 双模型架构

系统使用**双模型架构**优化成本和性能：

| 模型类型 | 用途 | 特点 |
|---------|------|------|
| **快速分析模型** | 分析师数据收集、初步分析 | 速度快、成本低 |
| **深度决策模型** | 研究经理决策、风险评估 | 推理能力强 |

```python
# trading_graph.py 中的双模型初始化
self.quick_thinking_llm = create_llm(
    provider=config["quick_provider"],
    model=config["quick_think_llm"],  # 如 qwen-turbo
    ...
)

self.deep_thinking_llm = create_llm(
    provider=config["deep_provider"],
    model=config["deep_think_llm"],   # 如 qwen-max
    ...
)
```

---

## 📊 九、关键数据模型

### 1. 分析任务模型

文件: `app/models/analysis.py`

```python
class AnalysisTask(BaseModel):
    """分析任务"""
    task_id: str                    # 任务ID
    user_id: PyObjectId             # 用户ID
    symbol: str                     # 股票代码
    status: AnalysisStatus          # 状态 (pending/processing/completed/failed)
    progress: int                   # 进度 0-100
    parameters: AnalysisParameters  # 分析参数
    result: Optional[AnalysisResult] # 分析结果
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

class AnalysisParameters(BaseModel):
    """分析参数"""
    market_type: str = "A股"
    research_depth: str = "标准"     # 快速/基础/标准/深度/全面
    selected_analysts: List[str]     # 选中的分析师
    quick_analysis_model: str        # 快速分析模型
    deep_analysis_model: str         # 深度决策模型
    include_sentiment: bool = True
    include_risk: bool = True
```

### 2. 系统配置模型

文件: `app/models/config.py`

```python
class SystemConfig(BaseModel):
    """系统配置"""
    config_name: str
    config_type: str
    llm_configs: List[LLMConfig]          # LLM模型配置
    default_llm: Optional[str]
    data_source_configs: List[DataSourceConfig]  # 数据源配置
    database_configs: List[DatabaseConfig]       # 数据库配置
    system_settings: Dict[str, Any]              # 系统设置
    version: int
    is_active: bool

class LLMConfig(BaseModel):
    """LLM配置"""
    provider: str                    # 厂商
    model_name: str                  # 模型名称
    model_display_name: Optional[str] # 显示名称
    api_key: Optional[str]           # API密钥
    api_base: Optional[str]          # API地址
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 180
    enabled: bool = True
    capability_level: Optional[int]   # 能力等级 1-5
    suitable_roles: Optional[List[str]] # 适用角色
```

---

## 🔐 十、安全与认证

### 1. JWT认证流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        认证流程                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. 登录请求                                                   │
│      POST /api/auth/login                                       │
│      Body: { username, password }                               │
│                       ↓                                         │
│   2. 验证密码 (bcrypt)                                          │
│                       ↓                                         │
│   3. 生成JWT Token                                              │
│      { user_id, username, exp }                                 │
│                       ↓                                         │
│   4. 返回Token给前端                                            │
│      { access_token, token_type: "bearer" }                     │
│                       ↓                                         │
│   5. 前端存储Token (localStorage)                               │
│                       ↓                                         │
│   6. 后续请求携带Token                                          │
│      Header: Authorization: Bearer {token}                      │
│                       ↓                                         │
│   7. 后端验证Token                                              │
│      get_current_user() 依赖注入                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. API密钥安全

```python
# 敏感信息处理策略

1. 存储：
   - API密钥存储在 MongoDB llm_providers 集合
   - 支持环境变量覆盖
   
2. 传输：
   - API响应中脱敏显示（只显示前4位和后4位）
   - 前端请求不传递完整密钥
   
3. 使用：
   - 运行时从数据库或环境变量读取
   - 优先级：模型配置 > 厂家配置 > 环境变量
```

---

## 📈 十一、性能优化设计

### 1. 缓存策略

```
┌─────────────────────────────────────────────────────────────────┐
│                        缓存架构                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   L1 缓存：内存缓存                                              │
│   - 任务状态 (MemoryStateManager)                               │
│   - 配置缓存 (TTL=60s)                                          │
│                                                                 │
│   L2 缓存：Redis缓存                                             │
│   - 任务进度                                                    │
│   - 会话数据                                                    │
│   - 频繁访问数据                                                │
│                                                                 │
│   L3 缓存：MongoDB缓存                                           │
│   - 股票数据                                                    │
│   - 新闻数据                                                    │
│   - 历史分析结果                                                │
│                                                                 │
│   L4 缓存：文件系统                                              │
│   - 大型数据文件                                                │
│   - 分析报告                                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 并发处理

```python
# SimpleAnalysisService 中的并发设计

class SimpleAnalysisService:
    def __init__(self):
        # 共享线程池，支持最多3个任务并发执行
        self._thread_pool = ThreadPoolExecutor(max_workers=3)
    
    async def _execute_analysis_sync(self, task_id, ...):
        # 在线程池中执行同步的分析任务
        result = await loop.run_in_executor(
            self._thread_pool,
            self._run_analysis_sync,
            ...
        )
```

---

## 🚀 十二、股票分析完整流程

### 从前端到后端的完整数据流

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│  前端UI  │      │ API路由  │      │ 分析服务 │      │ Trading  │      │ MongoDB  │
│          │      │          │      │          │      │ Agents   │      │          │
└────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                 │                 │                 │
     │ 1. 点击分析     │                 │                 │                 │
     │────────────────►│                 │                 │                 │
     │                 │                 │                 │                 │
     │ 2. POST /api/analysis/single      │                 │                 │
     │                 │────────────────►│                 │                 │
     │                 │                 │                 │                 │
     │                 │                 │ 3. 创建任务      │                 │
     │                 │                 │────────────────────────────────────►│
     │                 │                 │                 │                 │
     │                 │                 │ 4. 返回task_id  │                 │
     │ 5. 返回task_id  │◄────────────────│                 │                 │
     │◄────────────────│                 │                 │                 │
     │                 │                 │                 │                 │
     │                 │                 │ 6. 后台执行分析 │                 │
     │                 │                 │────────────────►│                 │
     │                 │                 │                 │                 │
     │ 7. 轮询状态     │                 │                 │ 7.1 分析师执行  │
     │────────────────►│────────────────►│                 │ (LangGraph)     │
     │                 │                 │                 │                 │
     │ 8. 返回进度     │                 │                 │                 │
     │◄────────────────│◄────────────────│                 │                 │
     │                 │                 │                 │                 │
     │    (重复7-8)    │                 │                 │ 7.2 研究辩论   │
     │                 │                 │                 │                 │
     │                 │                 │                 │ 7.3 交易决策   │
     │                 │                 │                 │                 │
     │                 │                 │                 │ 7.4 风险评估   │
     │                 │                 │                 │                 │
     │                 │                 │ 9. 分析完成     │                 │
     │                 │                 │◄────────────────│                 │
     │                 │                 │                 │                 │
     │                 │                 │ 10. 保存结果    │                 │
     │                 │                 │────────────────────────────────────►│
     │                 │                 │                 │                 │
     │ 11. 获取结果    │                 │                 │                 │
     │────────────────►│────────────────►│                 │                 │
     │                 │                 │────────────────────────────────────►│
     │ 12. 返回结果    │                 │                 │                 │
     │◄────────────────│◄────────────────│◄────────────────────────────────────│
     │                 │                 │                 │                 │
     │ 13. 展示结果    │                 │                 │                 │
     │                 │                 │                 │                 │
```

---

## 🎯 十三、总结

### 核心设计理念

1. **多智能体协作** - 模拟投资团队的决策流程
2. **可扩展架构** - 支持多种LLM提供商和数据源
3. **配置驱动** - 通过配置而非代码控制系统行为
4. **异步优先** - 使用异步处理提高并发能力
5. **分层设计** - 清晰的分层便于维护和扩展

### 关键技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Element Plus + Pinia |
| API | FastAPI + Pydantic + JWT |
| 核心引擎 | LangGraph + LangChain |
| 数据存储 | MongoDB + Redis |
| LLM | OpenAI兼容接口（支持多厂商） |
| 部署 | Docker + Nginx |

### 关键文件索引

| 功能 | 文件路径 |
|------|----------|
| **前端视图** | `frontend/src/views/Analysis/SingleAnalysis.vue` |
| **前端API** | `frontend/src/api/analysis.ts` |
| **后端路由** | `app/routers/analysis.py` |
| **数据模型** | `app/models/analysis.py` |
| **分析服务** | `app/services/simple_analysis_service.py` |
| **核心引擎** | `tradingagents/graph/trading_graph.py` |
| **图配置** | `tradingagents/graph/setup.py` |
| **状态定义** | `tradingagents/agents/utils/agent_states.py` |
| **配置服务** | `app/services/config_service.py` |

---

## 📚 相关文档

- [快速开始指南](../QUICK_START.md)
- [API文档](../api/)
- [部署指南](../deployment/)
- [配置说明](../configuration/)

---

*文档更新日期: 2025-11-26*

