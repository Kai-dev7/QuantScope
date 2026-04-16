# Token使用统计和成本跟踪指南 (v0.1.7)

本指南介绍如何配置和使用QuantScope的Token使用统计和成本跟踪功能，包括v0.1.7新增的DeepSeek成本追踪和智能成本控制。

## 功能概述

TradingAgents提供了完整的Token使用统计和成本跟踪功能，包括：

- **实时Token统计**: 自动记录每次LLM调用的输入和输出token数量
- **成本计算**: 根据不同供应商的定价自动计算使用成本
- **多存储支持**: 支持JSON文件存储和MongoDB数据库存储
- **统计分析**: 提供详细的使用统计和成本分析
- **成本警告**: 当使用成本超过阈值时自动提醒

## 支持的LLM供应商

目前支持以下LLM供应商的Token统计：

- ✅ **DeepSeek**: 完全支持，自动提取API响应中的token使用量 (v0.1.7新增)
- ✅ **DashScope (阿里百炼)**: 完全支持，自动提取API响应中的token使用量
- ✅ **Google AI**: 完全支持，Gemini系列模型token统计
- 🔄 **OpenAI**: 计划支持
- 🔄 **Anthropic**: 计划支持

## 配置方法

### 1. 基础配置

在项目根目录创建或编辑 `.env` 文件：

```bash
# 启用成本跟踪（默认启用）
ENABLE_COST_TRACKING=true

# 成本警告阈值（人民币）
COST_ALERT_THRESHOLD=100.0

# DashScope API密钥
DASHSCOPE_API_KEY=your_dashscope_api_key_here
```

### 2. 存储配置

#### 选项1: JSON文件存储（默认）

默认情况下，Token使用记录保存在 `config/usage.json` 文件中。

```bash
# 最大记录数量（默认10000）
MAX_USAGE_RECORDS=10000

# 自动保存使用记录（默认启用）
AUTO_SAVE_USAGE=true
```

#### 选项2: MongoDB存储（推荐用于生产环境）

对于大量数据和高性能需求，推荐使用MongoDB存储：

```bash
# 启用MongoDB存储
USE_MONGODB_STORAGE=true

# MongoDB连接字符串
# 本地MongoDB
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/

# 或云MongoDB（如MongoDB Atlas）
# MONGODB_CONNECTION_STRING=mongodb+srv://username:password@cluster.mongodb.net/

# 数据库名称
MONGODB_DATABASE_NAME=tradingagents
```

### 3. 安装MongoDB依赖（如果使用MongoDB存储）

```bash
pip install pymongo
```

## 使用方法

### 1. 自动Token统计

当使用DashScope适配器时，Token统计会自动进行：

```python
from tradingagents.llm_adapters.dashscope_adapter import ChatDashScope
from langchain_core.messages import HumanMessage

# 初始化LLM
llm = ChatDashScope(
    model="qwen-turbo",
    temperature=0.7
)

# 发送消息（自动记录token使用）
response = llm.invoke([
    HumanMessage(content="分析一下苹果公司的股票")
], session_id="my_session", analysis_type="stock_analysis")
```

### 2. 查看使用统计

```python
from tradingagents.config.config_manager import config_manager

# 获取最近30天的统计
stats = config_manager.get_usage_statistics(30)

print(f"总成本: ¥{stats['total_cost']:.4f}")
print(f"总请求数: {stats['total_requests']}")
print(f"输入tokens: {stats['total_input_tokens']}")
print(f"输出tokens: {stats['total_output_tokens']}")

# 按供应商查看统计
for provider, provider_stats in stats['provider_stats'].items():
    print(f"{provider}: ¥{provider_stats['cost']:.4f}")
```

### 3. 查看会话成本

```python
from tradingagents.config.config_manager import token_tracker

# 查看特定会话的成本
session_cost = token_tracker.get_session_cost("my_session")
print(f"会话成本: ¥{session_cost:.4f}")
```

### 4. 估算成本

```python
# 估算成本（用于预算规划）
estimated_cost = token_tracker.estimate_cost(
    provider="dashscope",
    model_name="qwen-turbo",
    estimated_input_tokens=1000,
    estimated_output_tokens=500
)
print(f"估算成本: ¥{estimated_cost:.4f}")
```

## 定价配置

系统内置了主要LLM供应商的定价信息，也可以自定义定价：

```python
from tradingagents.config.config_manager import config_manager, PricingConfig

# 添加自定义定价
custom_pricing = PricingConfig(
    provider="dashscope",
    model_name="qwen-max",
    input_price_per_1k=0.02,   # 每1000个输入token的价格（人民币）
    output_price_per_1k=0.06,  # 每1000个输出token的价格（人民币）
    currency="CNY"
)

pricing_list = config_manager.load_pricing()
pricing_list.append(custom_pricing)
config_manager.save_pricing(pricing_list)
```

## 内置定价表

### DashScope (阿里百炼)

| 模型 | 输入价格 (¥/1K tokens) | 输出价格 (¥/1K tokens) |
|------|----------------------|----------------------|
| qwen-turbo | 0.002 | 0.006 |
| qwen-plus-latest | 0.004 | 0.012 |
| qwen-max | 0.02 | 0.06 |

### OpenAI

| 模型 | 输入价格 ($/1K tokens) | 输出价格 ($/1K tokens) |
|------|----------------------|----------------------|
| gpt-3.5-turbo | 0.0015 | 0.002 |
| gpt-4 | 0.03 | 0.06 |
| gpt-4-turbo | 0.01 | 0.03 |

## 测试Token统计功能

运行测试脚本验证功能：

```bash
# 测试DashScope token统计
python tests/test_dashscope_token_tracking.py
```

## MongoDB存储优势

使用MongoDB存储相比JSON文件存储有以下优势：

1. **高性能**: 支持大量数据的高效查询和聚合
2. **可扩展性**: 支持分布式部署和水平扩展
3. **数据安全**: 支持备份、复制和故障恢复
4. **高级查询**: 支持复杂的聚合查询和统计分析
5. **并发支持**: 支持多用户并发访问

### MongoDB索引优化

系统会自动创建以下索引以提高查询性能：

- 复合索引：`(timestamp, provider, model_name)`
- 单字段索引：`session_id`, `analysis_type`

## 成本控制建议

1. **设置合理的成本警告阈值**
2. **定期查看使用统计，优化使用模式**
3. **根据需求选择合适的模型（平衡成本和性能）**
4. **使用会话ID跟踪特定分析的成本**
5. **定期清理旧的使用记录（MongoDB支持自动清理）**

## 故障排除

### 1. Token统计不工作

- 检查API密钥是否正确配置
- 确认 `ENABLE_COST_TRACKING=true`
- 查看控制台是否有错误信息

### 2. MongoDB连接失败

- 检查MongoDB服务是否运行
- 验证连接字符串格式
- 确认网络连接和防火墙设置
- 检查用户权限

### 3. 成本计算不准确

- 检查定价配置是否正确
- 确认模型名称匹配
- 验证token提取逻辑

## 最佳实践

1. **生产环境使用MongoDB存储**
2. **定期备份使用数据**
3. **监控成本趋势，及时调整策略**
4. **使用有意义的会话ID和分析类型**
5. **定期更新定价信息**

## 未来计划

- [ ] 支持更多LLM供应商的Token统计
- [ ] 添加可视化仪表板
- [ ] 支持成本预算和限制
- [ ] 添加使用报告导出功能
- [ ] 支持团队和用户级别的成本跟踪