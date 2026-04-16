# 使用统计与定价配置功能

## 📋 功能概述

本文档介绍 QuantScope 的使用统计和定价配置功能，包括：

1. **模型定价配置** - 为每个大模型配置输入/输出 token 价格
2. **使用统计** - 查看模型使用情况和成本统计
3. **计费分析** - 按供应商、模型、日期分析成本

## 🎯 功能特性

### 1. 模型定价配置

#### 在大模型配置中设置定价

在"配置管理 > 大模型配置"中，每个模型卡片会显示定价信息：

```
┌─────────────────────────────────────┐
│ 🖥️ qwen-max                  ✅ 启用 │
├─────────────────────────────────────┤
│ Token: 4000                         │
│ 温度: 0.7                           │
│ 超时: 60s                           │
├─────────────────────────────────────┤
│ 💰 定价:                            │
│   输入: 0.0200 CNY/1K               │
│   输出: 0.0600 CNY/1K               │
└─────────────────────────────────────┘
```

#### 编辑定价

点击"编辑"按钮，在对话框中可以配置：

- **输入价格** (input_price_per_1k): 每 1000 个输入 token 的价格
- **输出价格** (output_price_per_1k): 每 1000 个输出 token 的价格
- **货币单位** (currency): CNY(人民币) / USD(美元) / EUR(欧元)

### 2. 使用统计界面

访问"设置 > 使用统计"查看详细的使用和计费信息。

#### 统计概览

显示关键指标：
- 总请求数
- 总输入 Token
- 总输出 Token
- 总成本

#### 图表分析

1. **按供应商统计** (饼图)
   - 显示各供应商的成本占比
   - 快速识别主要成本来源

2. **按模型统计** (柱状图)
   - 显示前 10 个模型的成本
   - 对比不同模型的使用成本

3. **每日成本趋势** (折线图)
   - 显示每日成本变化
   - 分析成本趋势

#### 使用记录表格

详细记录每次 API 调用：
- 时间
- 供应商
- 模型
- 输入/输出 Token
- 成本
- 分析类型
- 会话 ID

## 🔧 技术实现

### 后端 API

#### 使用统计服务

```python
# app/services/usage_statistics_service.py
class UsageStatisticsService:
    async def add_usage_record(record: UsageRecord) -> bool
    async def get_usage_records(...) -> List[UsageRecord]
    async def get_usage_statistics(...) -> UsageStatistics
    async def get_cost_by_provider(days: int) -> Dict[str, float]
    async def get_cost_by_model(days: int) -> Dict[str, float]
    async def get_daily_cost(days: int) -> Dict[str, float]
```

#### API 端点

```
GET  /api/usage/records          # 获取使用记录
GET  /api/usage/statistics       # 获取使用统计
GET  /api/usage/cost/by-provider # 按供应商统计成本
GET  /api/usage/cost/by-model    # 按模型统计成本
GET  /api/usage/cost/daily       # 每日成本统计
DELETE /api/usage/records/old    # 删除旧记录
```

### 前端组件

#### 使用统计页面

```
frontend/src/views/Settings/UsageStatistics.vue
```

功能：
- 统计概览卡片
- ECharts 图表展示
- 使用记录表格
- 时间范围筛选

#### 配置管理增强

```
frontend/src/views/Settings/ConfigManagement.vue
frontend/src/views/Settings/components/LLMConfigDialog.vue
```

新增：
- 模型卡片显示定价信息
- 编辑对话框添加定价配置字段

### 数据模型

#### LLMConfig 扩展

```python
class LLMConfig(BaseModel):
    # ... 原有字段 ...
    
    # 定价配置
    input_price_per_1k: Optional[float] = None
    output_price_per_1k: Optional[float] = None
    currency: str = "CNY"
```

#### UsageRecord

```python
class UsageRecord(BaseModel):
    timestamp: str
    provider: str
    model_name: str
    input_tokens: int
    output_tokens: int
    cost: float
    session_id: str
    analysis_type: str
```

#### UsageStatistics

```python
class UsageStatistics(BaseModel):
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    by_provider: Dict[str, Any]
    by_model: Dict[str, Any]
    by_date: Dict[str, Any]
```

## 📊 使用示例

### 1. 配置模型定价

```python
# 通过 API 更新模型配置
llm_config = {
    "provider": "dashscope",
    "model_name": "qwen-max",
    "input_price_per_1k": 0.02,    # 2分/1K tokens
    "output_price_per_1k": 0.06,   # 6分/1K tokens
    "currency": "CNY"
}

await config_service.update_llm_config(llm_config)
```

### 2. 查询使用统计

```python
# 获取最近 7 天的统计
stats = await usage_statistics_service.get_usage_statistics(days=7)

print(f"总请求数: {stats.total_requests}")
print(f"总成本: ¥{stats.total_cost:.4f}")

# 按供应商统计
for provider, data in stats.by_provider.items():
    print(f"{provider}: ¥{data['cost']:.4f}")
```

### 3. 前端调用

```typescript
// 获取使用统计
import { getUsageStatistics } from '@/api/usage'

const stats = await getUsageStatistics({ days: 7 })
console.log('总成本:', stats.data.data.total_cost)
```

## 🎨 界面截图

### 模型定价配置

在大模型配置卡片中显示定价信息，点击"编辑"可以修改。

### 使用统计仪表板

- 顶部显示关键指标卡片
- 中间显示三个图表（供应商、模型、每日趋势）
- 底部显示详细使用记录表格

## 💡 最佳实践

### 1. 定价配置建议

- **及时更新**: 供应商调整价格后及时更新配置
- **统一货币**: 建议统一使用人民币(CNY)便于统计
- **精确配置**: 价格精确到小数点后 4 位

### 2. 成本控制

- **定期查看**: 每周查看使用统计，了解成本趋势
- **识别高成本**: 通过图表快速识别高成本模型
- **优化选择**: 根据成本和效果选择合适的模型

### 3. 数据管理

- **定期清理**: 定期删除 90 天前的旧记录
- **导出备份**: 重要数据可以导出备份
- **监控异常**: 关注成本异常增长

## 🔒 安全说明

- 使用记录存储在 MongoDB 中
- 只有登录用户可以查看统计数据
- 定价信息与模型配置一起存储
- 支持按用户权限控制访问

## 📝 注意事项

1. **自动记录**: TradingAgents 核心库会自动记录每次 API 调用
2. **成本计算**: 成本 = (输入 tokens / 1000) × 输入价格 + (输出 tokens / 1000) × 输出价格
3. **货币转换**: 系统不自动转换货币，请手动配置统一货币
4. **数据延迟**: 统计数据可能有几秒钟延迟

## 🚀 未来计划

- [ ] 成本预警功能
- [ ] 成本预算管理
- [ ] 更多图表类型
- [ ] 导出统计报表
- [ ] 成本优化建议
- [ ] 多用户成本分摊

## 📚 相关文档

- [配置管理文档](./CONFIG_MANAGEMENT.md)
- [API 文档](./API_DOCUMENTATION.md)
- [数据库设计](./DATABASE_SCHEMA.md)

