# QuantScope Agent Runtime Modernization Plan

> 目标：在不破坏当前分析主链路稳定性的前提下，引入更现代的 Agent Engineering 思路，把 QuantScope 从“可运行的多智能体分析系统”升级为“可恢复、可配置、可扩展、可对外集成”的研究平台。

## 1. 背景与目标

当前 QuantScope 已经具备完整的分析链路：

- FastAPI 后端负责任务、配置、状态、通知、数据同步
- `tradingagents/` 负责多角色分析流程与工具调用
- Vue 3 前端负责工作台、任务中心、配置中心、报告展示

但当前实现存在几个明显瓶颈：

1. 流程知识高度硬编码
2. 运行态状态以内存和 Redis 临时状态为主
3. orchestration 与 tool execution 强耦合
4. 外部能力接入没有统一协议边界
5. “研究 SOP” 没有抽象成可复用资产

本次改造不追求“为了新技术而重写”，而追求：

- 保留现有分析热路径性能
- 提升流程配置能力
- 提升任务恢复与审计能力
- 为 MCP / skills / sandbox / external agent integration 铺路
- 形成可写入简历和作品集的工程亮点

## 2. 当前架构问题诊断

### 2.1 状态层问题

当前状态主要分散在：

- `app/services/memory_state_manager.py`
- `app/services/redis_progress_tracker.py`
- `app/services/session_event_service.py`
- MongoDB `analysis_tasks` / `analysis_reports`

问题：

- `memory_state_manager` 仍然是进程内真相源之一
- `session_event_service` 只是轻量事件流，还不能完整恢复任务
- progress、report、tool-call、judge-feedback 没有统一事件模型

### 2.2 编排层问题

当前编排核心在：

- `tradingagents/graph/trading_graph.py`
- `tradingagents/graph/agentscope_runner.py`
- `tradingagents/graph/conditional_logic.py`

问题：

- orchestration、retry、judge、tool dispatch、message sanitize 在同一运行时类中
- 不同 analyst 的条件判断是硬编码分支
- skill / SOP / fallback policy 都散落在 service 和 graph 代码里

### 2.3 工具层问题

当前工具调用模式是：

- LLM 产生 `tool_calls`
- `AgentScopeRunner._execute_tool_calls()` 直接匹配 tool 并 `invoke`

问题：

- 缺少 capability boundary
- 工具执行默认与主 orchestrator 进程耦合
- 不利于未来接 MCP、sandbox、远端执行器

## 3. 改造目标架构

采用 `Session / Harness / Hands` 三层架构。

### 3.1 Session

Session 是任务的 durable source of truth。

职责：

- 保存 append-only event stream
- 保存 checkpoint / snapshot
- 支持 `session_id` 级恢复
- 审计 tool call、judge retry、报告生成、失败与补偿

建议存储：

- 热路径：Redis stream / Redis list
- 持久层：MongoDB `analysis_sessions`、`analysis_session_events`

第一版必须明确的数据对象：

- `analysis_sessions`
  - `session_id`
  - `task_id`
  - `user_id`
  - `status`
  - `skill_name`
  - `skill_version`
  - `analysis_context`
  - `last_event_seq`
  - `latest_checkpoint_id`
  - `started_at`
  - `updated_at`
  - `completed_at`
- `analysis_session_events`
  - `session_id`
  - `seq`
  - `event_type`
  - `node_name`
  - `timestamp`
  - `payload`
  - `source`
- `analysis_session_checkpoints`
  - `session_id`
  - `checkpoint_id`
  - `created_at`
  - `state_summary`
  - `recoverable_state`

第一版统一事件类型建议固定为：

- `session_started`
- `skill_selected`
- `progress_updated`
- `node_started`
- `node_completed`
- `tool_call_requested`
- `tool_call_completed`
- `tool_call_blocked`
- `judge_evaluated`
- `quality_gate_evaluated`
- `session_checkpointed`
- `session_completed`
- `session_failed`

这里的约束必须明确：

- MongoDB 是 durable truth
- Redis 只承担热缓存和快速读取
- Resume 以 checkpoint + 后续 event replay 为准
- 运行日志不是恢复依据，只是辅助审计

### 3.2 Harness

Harness 是无状态 orchestrator。

职责：

- 选择 skill
- 整理上下文
- 触发 analyst / researcher / trader / risk manager
- 管理 retry / judge / fallback
- 管理 progress mapping

建议落点：

- 由 `AgentScopeRunner` 演进而来
- 把 tool dispatch 抽到独立 capability executor
- 把条件逻辑从硬编码转成 skill policy 解释执行

Harness 第一版必须暴露的稳定接口：

- `start_session(context) -> session_id`
- `load_session(session_id) -> session context + latest checkpoint`
- `run(session_id, init_state, selected_analysts, progress_sender) -> final_state`
- `resume(session_id) -> resume_result`

Harness 第一版恢复边界需要明确：

- 不追求“任意 token 级别恢复”
- 以 analyst / tool / judge / trader / risk 阶段作为 checkpoint 边界
- 如果进程在节点内部崩溃，允许从最近 checkpoint 重放该节点之后的 event
- tool call 结果必须事件化，否则 resume 无法判断是否需要补执行

### 3.3 Hands

Hands 是执行环境和能力层。

职责：

- 本地 toolkit tools
- MCP tools
- sandboxed executors
- 外部 provider / search / docs / report tools

建议分层：

- `LocalHands`: 本地低延迟热路径工具
- `MCPHands`: 标准协议工具
- `SandboxHands`: 批处理、调度、重型任务

Hands 第一版需要统一 capability contract：

```python
execute(
    capability_name: str,
    arguments: dict,
    session_context: dict,
) -> CapabilityResult
```

其中 `CapabilityResult` 至少包含：

- `success`
- `capability_name`
- `result`
- `error`
- `latency_ms`
- `metadata`

这样 orchestrator 不直接关心它来自：

- 本地 Python tool
- MCP server
- 远端 sandbox executor

## 4. Skill Schema 设计

### 4.1 为什么要引入 Skill Schema

当前项目已经有很多“隐式 SOP”，只是写成了代码分支：

- 哪些 analyst 参与
- 研究深度如何映射辩论轮次
- 哪些工具允许调用
- 哪些回退逻辑适用
- 哪些结果检查必须通过

Skill Schema 的目标是：

- 把“流程知识”从代码里抽出来
- 让分析流程成为一等资产
- 支持版本化、测试、对比和复用

### 4.2 Skill 的定位

Skill 不是单个 tool。

Skill 是一个结构化研究 SOP，描述：

- 什么时候使用
- 需要哪些输入
- 可以调用哪些 analyst / tools
- 输出必须满足什么要求
- 失败时怎么回退

### 4.3 第一版 Skill Schema

建议使用 `YAML`，例如：

```yaml
name: standard-a-share-analysis
version: 1
description: 标准 A 股单股分析流程

selectors:
  task_type: single_stock_analysis
  market_scope: [A股]
  research_depth: [标准, 深度]

inputs:
  required:
    - stock_code
    - analysis_date
  optional:
    - user_goal
    - risk_preference

analysts:
  enabled:
    - market
    - fundamentals
    - news
  optional:
    - social

tool_policy:
  allowed_tools:
    - get_stock_market_data_unified
    - get_stock_fundamentals_unified
    - get_stock_news_unified
  max_tool_calls:
    market: 3
    fundamentals: 1
    news: 3

execution:
  debate_rounds: 1
  risk_rounds: 2
  memory_enabled: true
  llm_routing: cost_balanced

output:
  schema: stock_analysis_v1
  required_sections:
    - summary
    - risks
    - valuation
    - action

quality_gates:
  - report_completeness_check
  - risk_disclosure_check
  - target_price_sanity_check

fallback:
  on_missing_fundamentals: switch_to_market_news_mode
  on_tool_timeout: retry_with_backup_provider
```

### 4.4 Skill Runtime 需要的组件

需要新增：

- `SkillRegistry`
- `SkillSelector`
- `SkillValidator`
- `SkillRuntimeBinder`
- `QualityGateRegistry`

职责：

- Registry：注册与发现 skill
- Selector：根据任务上下文选择 skill
- Validator：检查 skill 配置合法性
- Binder：把 skill 注入运行链路
- QualityGateRegistry：注册结果质检器

除此之外，需要补一个 `SkillPolicyProjector`，专门负责：

- 将 skill policy 映射为 runtime config
- 将 skill policy 映射为 capability allowlist
- 将 skill policy 映射为 conditional override
- 避免 service / graph / router 多处各自投影同一套规则

### 4.5 第一批建议 Skill

- `standard-a-share-analysis`
- `deep-hk-stock-analysis`
- `event-driven-news-analysis`
- `earnings-risk-review`
- `batch-low-cost-screening`
- `provider-fallback-recovery`

## 5. MCP 接入边界

### 5.1 为什么不建议全量 MCP 化

当前核心分析链路大量依赖：

- 本地 state
- 高频 tool loop
- 低延迟同步 `tool.invoke`
- 复杂的 analyst-specific 条件判断

如果全量改成 MCP：

- latency 上升
- 运行复杂度明显增加
- 故障面变大
- 热路径调试难度提升

因此不建议把核心热路径重写为纯 MCP。

### 5.2 建议采用 Hybrid MCP

策略：

- 热路径工具保留本地调用
- 外围能力通过 MCP 暴露

### 5.3 适合 MCP 化的能力

优先 MCP 化这些能力：

- 报告查询 / 导出
- 历史会话查询
- 文档检索
- 配置查询
- scheduler / job inspect
- usage statistics
- knowledge base / architecture docs
- GitHub / issue / changelog 辅助能力

### 5.4 暂不 MCP 化的能力

- 实时行情热路径
- 基本面主聚合工具
- 高频新闻主链工具
- graph 内部循环节点

### 5.5 MCP 接入形式

建议新增：

- `mcp_servers/`
- `app/services/capabilities/`
- `tradingagents/toolkit_mcp_adapter.py`

执行方式：

- Local tool 和 MCP tool 在 orchestrator 看起来都实现同一 capability interface
- runner 不直接知道它是本地调用还是 MCP 调用

## 6. 目录改造方案

建议新增以下目录：

```text
app/
  services/
    capabilities/
      models.py
      executor.py
      registry.py
      local_hands.py
      mcp_hands.py
      sandbox_hands.py
    sessions/
      models.py
      event_store.py
      checkpoint_store.py
      recovery.py
      runtime.py

tradingagents/
  skills/
    registry.py
    selector.py
    validator.py
    binder.py
    projector.py
    schemas/
      standard-a-share-analysis.yaml
      event-driven-news-analysis.yaml
  quality_gates/
    report_completeness.py
    risk_disclosure.py
    target_price_sanity.py

mcp_servers/
  reports_server/
  sessions_server/
  docs_server/
  config_server/
```

### 6.1 现有文件的改造方向

#### `app/services/simple_analysis_service.py`

改造方向：

- 不再直接决定完整流程策略
- 改为：
  1. 构造 analysis context
  2. 选择 skill
  3. 初始化 session
  4. 调用 harness

#### `tradingagents/graph/agentscope_runner.py`

改造方向：

- 保留 runner 主体
- 把 `_execute_tool_calls()` 抽到 capability executor
- 把部分硬编码条件迁移到 skill policy 解释器

#### `tradingagents/graph/conditional_logic.py`

改造方向：

- 从 analyst-specific hardcoded logic
- 演进为：
  - default policy
  - skill override policy

#### `app/services/session_event_service.py`

改造方向：

- 从轻量事件流
- 升级为可恢复 session event store

需要补充的实现约束：

- append event 时同时写 Redis 和 Mongo
- event sequence 由 store 统一分配，不能由调用方决定
- 支持 `get_events_after(session_id, seq)`
- 支持 `get_latest_summary(session_id)`
- 支持 `list_sessions(task_id/user_id/status)`
- 支持 checkpoint 与 session summary 解耦

## 7. 分阶段里程碑

### Milestone 1：Skill Layer MVP

目标：

- skill schema 落地
- skill registry / selector / validator 初版
- 将现有“标准单股分析”迁移为一个 skill

交付物：

- `tradingagents/skills/`
- 3 个内置 skill
- 单元测试

### Milestone 2：Session Recovery Layer

目标：

- 统一 session event model
- 持久化 tool call、judge、progress、report 事件
- 支持 `session_id` 恢复

交付物：

- `app/services/sessions/`
- `analysis_sessions` 持久化模型
- resume API

完成标准：

- 单次分析开始时自动创建 durable session
- analyst / tool / judge / quality gate 关键事件落库
- 至少支持读取 session 时间线
- 至少支持从最新 checkpoint 恢复运行前状态

### Milestone 3：Capability Executor

目标：

- tool execution 与 orchestrator 解耦
- 引入 local / sandbox / mcp capability interface

交付物：

- capability registry
- local hands
- sandbox hands stub

完成标准：

- runner 不再直接 `tool.invoke`
- 所有 tool call 经过 capability executor
- capability executor 统一记录 requested / completed / blocked 事件
- local tool 和未来 MCP tool 共享同一调用返回结构

### Milestone 4：Hybrid MCP

目标：

- 报告、文档、配置、session 查询能力 MCP 化

交付物：

- 至少 2-4 个 MCP server
- 本地 tool / MCP tool 共存运行

### Milestone 5：Quality Gate + LLM Judge Upgrade

目标：

- 将 LLM judge 升级为正式质量门控层
- 支持结果重生成、降级、告警

交付物：

- quality gates registry
- judge score persistence
- 审计可视化基础接口

## 8. 风险与取舍

### 8.1 不建议做的事

- 不要为了简历把核心热路径全量改成 MCP
- 不要一上来引入超复杂 DSL
- 不要让 skill 可执行任意 Python
- 不要把高权限 host tools 暴露给主分析链路

### 8.2 必须控制的复杂度

- skill schema 第一版只做流程描述，不做图形编辑器
- MCP 第一版只做外围能力
- session 第一版优先保证 auditability 和 resume，不追求完美 replay

## 9. 预期收益

### 9.1 工程收益

- 流程配置与执行引擎解耦
- 更容易扩展分析场景
- 更容易做 A/B test 和质量评估
- 更容易接入外部 agent 生态
- 更容易做任务恢复和审计

### 9.2 产品收益

- 支持内置研究 SOP
- 支持不同研究模式的版本化管理
- 支持组织级分析模板
- 支持结果质控和可解释流程

### 9.3 简历亮点收益

可以对外描述为：

- 设计并实现了 skill-driven AI financial research workflow system
- 将硬编码多智能体流程重构为可配置的 skill schema + runtime binder
- 构建了 Session / Harness / Hands 三层可恢复 agent runtime
- 设计并落地 hybrid MCP integration，用于标准化外围研究能力接入
- 构建 LLM judge + quality gates 结果质量门控体系

## 10. 推荐实施顺序

建议按以下顺序实施：

1. Skill Schema MVP
2. Session Event Store Upgrade
3. Capability Executor 抽象
4. Hybrid MCP
5. Quality Gates 与审计完善

这个顺序的原因：

- 对现有系统侵入最小
- 每一步都能独立交付
- 每一步都能形成清晰的项目亮点

## 12. 当前方案仍需补充的关键实现细节

如果按“是否已经足够指导编码实现”来判断，当前文档在补完本节前并不算完全完善。最关键缺口是：

1. 缺少统一 event schema
2. 缺少 checkpoint 粒度与恢复边界说明
3. 缺少 capability executor 的稳定输入输出契约
4. 缺少 session / task / report 三者之间的关联字段约束
5. 缺少对“第一版只做可恢复，不做完美重放”的明确范围控制

补完这些之后，文档才足够指导渐进式实现。

## 11. 最终建议

最终建议不是“把 function calling 改成 MCP”，而是：

- 核心分析热路径继续保留本地 function/tool calling
- 流程知识抽象为 skill schema
- 运行时升级为 Session / Harness / Hands
- 外围能力采用 Hybrid MCP
- 质量控制升级为 judge + quality gates

这套组合对 QuantScope 最现实、最稳定、也最适合写进简历。
