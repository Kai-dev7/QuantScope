# Managed Agent Lightweight Upgrade

这次改造聚焦于三个能显著提升稳定性、且适合二次开发展示的点：

## 1. Worker 租约续期

- 问题：分析任务执行时间长于 Redis 可见性超时时，任务会被重新入队，导致重复执行。
- 改造：为任务增加 lease renewal 机制，Worker 在执行期间周期性续期可见性超时。
- 价值：避免同一 `task_id` 被多个 Worker 重复消费，降低重复调用 LLM 与外部数据源的成本。

## 2. 每任务独立 Harness

- 问题：`TradingAgentsGraph` 实例内部持有 `curr_state`、`ticker` 等可变状态，复用实例会造成跨任务污染。
- 改造：移除 graph 实例缓存，每个任务创建独立的 graph/harness。
- 价值：将 orchestrator 从“共享可变对象”收敛到“任务级独立执行单元”，更接近 managed-agent-architecture 的无状态 harness。

## 3. 轻量级 Session Event Stream

- 问题：原实现只有日志和粗粒度任务状态，缺少可审计的 agent 运行事件。
- 改造：基于 Redis 增加 append-only session event store，记录 `task_submitted`、`task_started`、`graph_progress`、`task_completed`、`task_failed` 等事件。
- 价值：具备基本的事件追踪与运行审计能力，为后续 checkpoint / resume 打基础。

## 对应简历表达

可表述为：

> 对开源多智能体量化分析系统进行二次架构改造，引入任务租约续期、任务级独立 orchestrator 与 Redis 会话事件流，解决长任务重复消费、共享状态串扰与运行不可审计问题，提升 AI 分析任务的稳定性与可观测性。

