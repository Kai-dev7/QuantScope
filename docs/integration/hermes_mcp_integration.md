# Hermes MCP 集成说明

本文档说明如何将 QuantScope 的单股分析能力以 MCP tool 方式接入 Hermes。

当前采用的交互模式是：

- `submit_single_analysis`
- `get_final_report`

不要求 Hermes 高频轮询任务状态，也不依赖长连接等待 10 分钟以上的分析过程完成。

## 1. 设计原则

单股分析是长任务，完整执行通常需要数分钟到十几分钟。

因此不推荐：

- 单次 tool 调用阻塞等待最终结果
- 高频调用 `get_analysis_task_status`

当前更合适的方式是：

1. Hermes 发起分析任务
2. QuantScope 后台异步执行
3. Hermes 在合适时机查询最终报告

这符合 QuantScope 当前的任务模型，也更适合 agent 编排。

## 2. MCP Endpoint

当前 analysis MCP server 地址：

```text
http://<host>:8000/mcp/analysis/mcp
```

本地 Docker 默认地址：

```text
http://localhost:8000/mcp/analysis/mcp
```

注意：

- 当前项目里的 MCP client 应使用 `/mcp/<server>/mcp`
- 不要使用 `/mcp/analysis`

## 3. 可用 Tool

### 3.1 `submit_single_analysis`

作用：

- 提交一个单股分析任务
- 立即返回 `task_id`
- 后台开始运行真实分析流程

输入参数：

```json
{
  "symbol": "AAPL",
  "market_type": "美股",
  "research_depth": "标准",
  "selected_analysts": ["market", "fundamentals", "news"],
  "custom_prompt": "重点关注近期财报与基本面变化",
  "planner_enabled": true,
  "include_sentiment": true,
  "include_risk": true,
  "language": "zh-CN",
  "quick_analysis_model": "qwen-turbo",
  "deep_analysis_model": "qwen-max"
}
```

返回示例：

```json
{
  "success": true,
  "task_id": "0a4ebde3-02ea-4d78-9ba4-7f9cf08adfc2",
  "status": "pending",
  "message": "任务已创建，等待执行",
  "planner_plan": {
    "analysts": ["market", "fundamentals"],
    "depth": "快速",
    "focus_hint": "用户关注点：测试MCP提交单股分析；重点结合近期价格趋势、成交量和市场反应验证基本面/事件影响",
    "reasoning": [
      "根据用户分析目标提取重点",
      "纳入市场分析，要求交叉验证价格反应"
    ],
    "user_goal": "测试MCP提交单股分析"
  },
  "query_hint": "Use get_final_report with task_id after the analysis completes."
}
```

### 3.2 `get_final_report`

作用：

- 按 `task_id`
- 或按 `analysis_id`
- 或按 `stock_symbol` 获取最终报告

建议优先使用：

- `task_id`

输入示例 1：

```json
{
  "task_id": "0a4ebde3-02ea-4d78-9ba4-7f9cf08adfc2"
}
```

输入示例 2：

```json
{
  "stock_symbol": "AAPL"
}
```

未完成时返回：

```json
{
  "success": false,
  "found": false,
  "message": "Final report is not ready or does not exist."
}
```

已完成时返回：

```json
{
  "success": true,
  "found": true,
  "report": {
    "analysis_id": "AAPL_20260428_125413",
    "task_id": "d1aab55e-c064-46e9-bace-2904bed4ba2d",
    "stock_symbol": "AAPL",
    "stock_name": "苹果公司",
    "market_type": "美股",
    "analysis_date": "2026-04-28",
    "summary": "...",
    "recommendation": "...",
    "confidence_score": 0.7,
    "risk_level": "中等",
    "key_points": [],
    "execution_time": 1233.45,
    "tokens_used": 0,
    "analysts": ["market", "fundamentals", "news"],
    "research_depth": "标准",
    "reports": {},
    "decision": {},
    "planner_plan": {},
    "focus_hint": "...",
    "status": "completed",
    "model_info": "ChatCustomOpenAI:MiniMax-M2.7",
    "created_at": "2026-04-28 12:54:13.989000",
    "updated_at": "2026-04-28 12:54:13.989000"
  }
}
```

## 4. Hermes 推荐调用模式

推荐工作流：

1. Hermes 判断用户意图是单股研究
2. 调 `submit_single_analysis`
3. 保存 `task_id`
4. 不做高频状态轮询
5. 在下一轮或延迟一段时间后调 `get_final_report(task_id=...)`
6. 若 `found=false`，延后重试
7. 若 `found=true`，读取 `summary / recommendation / reports / decision`

## 5. 为什么不用状态轮询作为主模式

原因有三点：

- 单股分析经常超过 10 分钟，轮询价值低
- Hermes 更关心最终可消费结果，而不是中间节点进度
- QuantScope 当前已经把最终报告稳定沉淀到 `analysis_reports`

因此：

- 对 Web 端，进度展示仍有意义
- 对 Hermes，这里更适合“提交 + 取结果”

## 6. 推荐的 Hermes 端封装方式

建议在 Hermes 侧把 QuantScope 封装成两个能力：

- `start_stock_analysis`
- `read_stock_analysis_report`

映射关系：

- `start_stock_analysis` -> `submit_single_analysis`
- `read_stock_analysis_report` -> `get_final_report`

这样 Hermes 内部不需要理解 QuantScope 的完整后端结构，只消费稳定能力边界。

## 6.1 模型如何知道这些 tool 的用途和参数

Hermes 并不是“猜”这些 tool 怎么用，而是通过 MCP 的 tool metadata 获取信息。

当 Hermes 连接 MCP server 后，会先做：

1. `initialize`
2. `list_tools`

随后 MCP server 会把每个 tool 的元数据暴露给 Hermes，包括：

- tool 名称
- tool 描述
- 输入参数名称
- 参数类型
- 必填参数
- 某些参数的枚举约束

对于 QuantScope 的 analysis MCP server，Hermes 会拿到类似这样的结构化信息：

- `submit_single_analysis`
  - 这是一个长耗时分析任务提交 tool
  - 它会立即返回 `task_id`
  - 不会同步返回最终报告
  - 推荐下一步使用 `get_final_report`

- `get_final_report`
  - 用于获取已完成任务的最终报告
  - 优先用 `task_id`
  - 如果只给 `stock_symbol`，拿到的是最近一份报告，而不是某次特定任务的唯一结果

当前我们已经在 tool 定义里补充了较详细的 docstring 和参数约束，Hermes 在读取 tool schema 时会更容易理解：

- 这个 tool 是做什么的
- 什么时候应该调用
- 参数应该怎么传
- 两个 tool 的先后顺序是什么

### 为什么这一步重要

如果 tool 只有名字，没有明确描述：

- 模型通常只能大概猜用途
- 对长任务尤其容易误用
- 可能会错误地期待 `submit_single_analysis` 直接返回最终分析结论

补强描述后，模型会更容易形成正确调用习惯：

1. 先 `submit`
2. 保存 `task_id`
3. 再 `get_final_report`

### 当前已经补上的约束

在 `submit_single_analysis` 中，我们已经显式约束了：

- `market_type`:
  - `A股`
  - `港股`
  - `美股`

- `research_depth`:
  - `快速`
  - `基础`
  - `标准`
  - `深度`
  - `全面`

- `selected_analysts`:
  - `market`
  - `fundamentals`
  - `news`
  - `social`

这会比只用自由字符串更适合 Hermes 做自动参数构造。

## 7. 已完成验证

已完成真实 MCP 调用验证：

- `http://127.0.0.1:8000/mcp/analysis/mcp` 可初始化
- tool 列表可返回：
  - `submit_single_analysis`
  - `get_final_report`
- `get_final_report(stock_symbol='AAPL')` 返回历史最终报告成功
- `submit_single_analysis(...)` 返回 `task_id` 成功
- 后台分析任务已确认真正启动

## 8. 后续可选增强

如果后续要继续增强，可以考虑：

- 增加 `get_report_by_task_id` 的强约束版本
- 增加 `list_recent_reports`
- 增加 `get_session_recovery`
- 在报告返回中增加更适合 agent 消费的摘要字段
- 给 Hermes 增加 webhook 或外部通知，而不是 MCP 主动 push
