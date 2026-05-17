# QuantScope Skill Schema Phase 1 Plan

> 本文档细化 `AGENT_RUNTIME_MODERNIZATION_PLAN.md` 中的第一阶段，实现目标是：在不重写主分析链路的前提下，把“分析 SOP”抽象为 Skill Schema，并以最小代价接入现有 `SimpleAnalysisService -> TradingAgentsGraph` 流程。

## 1. Phase 1 目标

第一阶段只解决一个问题：

**把当前硬编码在 service / graph 中的流程配置，抽象为可配置、可校验、可选择的 skill。**

第一阶段不做：

- 不做全量 MCP 接入
- 不做 session recovery 重构
- 不做 sandbox
- 不重写 `AgentScopeRunner`
- 不引入复杂 DSL

## 2. Phase 1 交付范围

### 2.1 新增模块

新增目录：

```text
tradingagents/skills/
  __init__.py
  models.py
  registry.py
  selector.py
  validator.py
  loader.py
  schemas/
    standard-a-share-analysis.yaml
    event-driven-news-analysis.yaml
    batch-low-cost-screening.yaml
```

### 2.2 新增能力

- Skill 数据模型
- Skill YAML 加载器
- Skill 注册中心
- 基于上下文的 skill 选择器
- Skill 校验器
- 将 skill 应用于 runtime config 的转换函数

## 3. Skill 数据模型设计

第一版不做图结构，只做结构化配置。

建议 Python 模型：

```python
@dataclass
class SkillSelectorRule:
    task_type: str
    market_scopes: list[str]
    research_depths: list[str]

@dataclass
class ToolPolicy:
    allowed_tools: list[str]
    max_tool_calls: dict[str, int]

@dataclass
class ExecutionPolicy:
    debate_rounds: int
    risk_rounds: int
    memory_enabled: bool
    llm_routing: str

@dataclass
class OutputContract:
    schema: str
    required_sections: list[str]

@dataclass
class SkillDefinition:
    name: str
    version: int
    description: str
    selectors: SkillSelectorRule
    analysts: list[str]
    tool_policy: ToolPolicy
    execution: ExecutionPolicy
    output: OutputContract
    quality_gates: list[str]
    fallback: dict[str, str]
```

## 4. YAML Schema 设计

### 4.1 统一字段

第一版 skill YAML 要求字段固定：

- `name`
- `version`
- `description`
- `selectors`
- `inputs`
- `analysts`
- `tool_policy`
- `execution`
- `output`
- `quality_gates`
- `fallback`

### 4.2 第一版约束

- `name` 必须唯一
- `version` 必须为正整数
- `analysts.enabled` 必须属于 `{market, fundamentals, news, social}`
- `execution.debate_rounds` 与 `risk_rounds` 必须为非负整数
- `tool_policy.max_tool_calls` 的 key 必须只引用已启用 analyst

## 5. 运行时接入点

### 5.1 现有主链路

当前主链路：

`submit_single_analysis`
-> `create_analysis_task`
-> `execute_analysis_background`
-> `_run_analysis_sync`
-> `create_analysis_config`
-> `TradingAgentsGraph`

### 5.2 Phase 1 接入策略

最小接入方式：

1. 在 `_run_analysis_sync()` 中构造 `skill_context`
2. 调 `SkillSelector.select_for_context(...)`
3. 取到 `SkillDefinition`
4. 将 skill 应用到 `create_analysis_config(...)`
5. 将 skill 元信息注入 `config`

不改动：

- `TradingAgentsGraph.propagate()`
- `AgentScopeRunner.run()` 主流程
- `toolkit` 实现

### 5.3 Skill 注入 config 的映射

Skill 映射到现有 config 的关键字段：

- `analysts.enabled` -> `selected_analysts`
- `execution.debate_rounds` -> `max_debate_rounds`
- `execution.risk_rounds` -> `max_risk_discuss_rounds`
- `execution.memory_enabled` -> `memory_enabled`
- `tool_policy` -> `skill_tool_policy`
- `output` -> `skill_output_contract`
- `quality_gates` -> `skill_quality_gates`
- `fallback` -> `skill_fallback`
- `name/version` -> `skill_name` / `skill_version`

## 6. 哪些现有函数要改

### 6.1 `app/services/simple_analysis_service.py`

需要改：

- `create_analysis_config(...)`
- `_run_analysis_sync(...)`

改法：

- 支持可选 `skill_definition`
- skill 存在时，用 skill 覆盖一部分运行配置
- 保留原有 research depth 配置作为 fallback

### 6.2 `tradingagents/graph/trading_graph.py`

第一阶段只做轻改：

- 允许读取 `config["skill_name"]`
- 允许读取 `config["skill_tool_policy"]`
- 不改变主流程逻辑

### 6.3 `tradingagents/graph/conditional_logic.py`

第一阶段不改逻辑，只预留读取：

- `state.get("skill_tool_policy")`
- `state.get("skill_name")`

等第二阶段再让工具调用上限真正从 skill 驱动。

## 7. 第一批 3 个 Skill 定义

### 7.1 `standard-a-share-analysis`

适用场景：

- 单股分析
- A 股
- 标准 / 深度研究

特点：

- analyst: market + fundamentals + news
- 平衡质量与速度
- 适合作为默认 skill

### 7.2 `event-driven-news-analysis`

适用场景：

- 新闻驱动分析
- 事件/舆情快速研判

特点：

- analyst: news + market + social
- 降低基本面比重
- 更强调事件摘要与风险提示

### 7.3 `batch-low-cost-screening`

适用场景：

- 批量分析
- 成本敏感
- 快速预筛查

特点：

- analyst: market + fundamentals
- memory 默认关闭
- 辩论轮次更少

## 8. Phase 1 测试策略

### 8.1 单元测试

- skill YAML 加载成功
- skill 校验规则生效
- 选择器能按上下文选对 skill
- 非法 YAML 给出明确错误

### 8.2 集成测试

- 单股分析请求能自动选中 `standard-a-share-analysis`
- `config` 中能看到 `skill_name`
- 批量分析请求能选中 `batch-low-cost-screening`

## 9. 风险与回退

### 风险

- 选择器误选 skill
- skill 配置与现有 graph 逻辑不一致
- 新增配置字段过多导致调试复杂

### 回退策略

- 没选中 skill 时，保持原有逻辑
- skill 加载失败时，记录 warning 并回退到原有 `create_analysis_config`
- 第一阶段 skill 只做“增强配置”，不做硬依赖

## 10. 第一阶段完成标准

满足以下条件即认为 Phase 1 完成：

- 有独立 `tradingagents/skills/` 模块
- 有 3 个示例 skill YAML
- skill 能被加载、校验、选择
- 单股分析主链路可注入 skill 元信息
- 现有分析功能不被破坏

## 11. 对外可描述成果

可用于简历或项目介绍：

- Designed a structured skill schema to externalize hard-coded financial research SOPs from the multi-agent runtime.
- Implemented a skill registry, selector, and validator layer to support configurable analyst routing and execution policies.
- Introduced a low-risk configuration overlay architecture that augments the existing trading analysis pipeline without rewriting the core execution engine.
