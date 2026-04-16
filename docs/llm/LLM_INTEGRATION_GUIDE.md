# QuantScope 大模型接入指导手册

## 📋 概述

本手册旨在帮助开发者为 QuantScope 项目添加新的大模型支持。通过遵循本指南，您可以快速集成新的大模型提供商，并提交高质量的 Pull Request。

## 🎯 适用场景

- 添加新的大模型提供商（如智谱、腾讯、百度等）
- 为现有提供商添加新模型
- 修复或优化现有 LLM 适配器
- 添加新的 API 兼容方式

## 🏗️ 系统架构概览

TradingAgents 的 LLM 集成基于以下架构：

```
tradingagents/
├── llm_adapters/              # LLM 适配器实现
│   ├── __init__.py           # 导出所有适配器
│   ├── openai_compatible_base.py  # OpenAI 兼容基类 (核心)
│   ├── dashscope_adapter.py       # 阿里百炼适配器
│   ├── dashscope_openai_adapter.py # 阿里百炼 OpenAI 兼容适配器  
│   ├── deepseek_adapter.py        # DeepSeek 原生适配器
│   ├── deepseek_direct_adapter.py # DeepSeek 直接适配器
│   └── google_openai_adapter.py   # Google AI 适配器
└── web/
    ├── components/sidebar.py  # 前端模型选择界面
    └── utils/analysis_runner.py  # 运行时配置与流程编排
```

### 核心组件

1. 适配器基类: <mcsymbol name="OpenAICompatibleBase" filename="openai_compatible_base.py" path="tradingagents/llm_adapters/openai_compatible_base.py" startline="32" type="class"></mcsymbol> —— 为所有 OpenAI 兼容的 LLM 提供统一实现，是新增提供商最重要的扩展点 <mcfile name="openai_compatible_base.py" path="tradingagents/llm_adapters/openai_compatible_base.py"></mcfile>
2. 工厂方法: <mcsymbol name="create_openai_compatible_llm" filename="openai_compatible_base.py" path="tradingagents/llm_adapters/openai_compatible_base.py" startline="329" type="function"></mcsymbol> —— 运行时根据提供商与模型创建对应的适配器实例（建议优先使用）
3. 提供商注册: 在 <mcfile name="openai_compatible_base.py" path="tradingagents/llm_adapters/openai_compatible_base.py"></mcfile> 中的 `OPENAI_COMPATIBLE_PROVIDERS` 字典 —— 统一管理 base_url、API Key 环境变量名、受支持模型等（单一信息源）
4. 前端集成: <mcfile name="sidebar.py" path="web/components/sidebar.py"></mcfile> —— 模型选择界面负责把用户选择的 llm_provider 和 llm_model 传递到后端
5. 运行时入口: <mcfile name="trading_graph.py" path="tradingagents/graph/trading_graph.py"></mcfile> 中统一使用工厂方法创建 LLM；<mcfile name="analysis_runner.py" path="web/utils/analysis_runner.py"></mcfile> 仅作为参数传递与流程编排，通常无需为新增提供商做修改

## 🚀 快速开始

### 第一步：环境准备

1. **Fork 并克隆仓库**

   ```bash
   git clone https://github.com/your-username/TradingAgentsCN.git
   cd TradingAgentsCN
   ```
2. **安装依赖**

   ```bash
   pip install -e .
   # 或使用 uv
   uv pip install -e .
   ```
3. **创建开发分支**

   ```bash
   git checkout develop
   git checkout -b feature/add-{provider_name}-llm
   ```

### 第二步：选择集成方式

根据目标大模型的 API 类型，选择适合的集成方式：

#### 方式一：OpenAI 兼容 API（推荐）

适用于：支持 OpenAI API 格式的模型（如智谱、MiniMax、月之暗面等）

**优势**：

- 开发工作量最小
- 复用现有的工具调用逻辑
- 统一的错误处理和日志记录

> 备注：百度千帆（Qianfan）已通过 OpenAI 兼容方式集成，provider 名称为 `qianfan`，只需配置 `QIANFAN_API_KEY`。相关细节见专项文档 QIANFAN_INTEGRATION_GUIDE.md；pricing.json 已包含 ERNIE 系列占位价格，支持在 Web 配置页调整。

#### 方式二：原生 API 适配器

适用于：非 OpenAI 兼容格式的模型

**需要更多工作**：

- 需要自定义消息格式转换
- 需要实现工具调用逻辑
- 需要处理特定的错误格式

## 📝 实现指南

### OpenAI 兼容适配器开发

#### 1. 创建适配器文件

在 `tradingagents/llm_adapters/` 下创建新文件：

```python
# tradingagents/llm_adapters/your_provider_adapter.py

from .openai_compatible_base import OpenAICompatibleBase
import os
from tradingagents.utils.tool_logging import log_llm_call
import logging

logger = logging.getLogger(__name__)

class ChatYourProvider(OpenAICompatibleBase):
    """你的提供商 OpenAI 兼容适配器"""
  
    def __init__(
        self,
        model: str = "your-default-model",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> None:
        super().__init__(
            provider_name="your_provider",
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key_env_var="YOUR_PROVIDER_API_KEY",
            base_url="https://api.yourprovider.com/v1",
            **kwargs
        )
```

#### 2. 在基类中注册提供商

编辑 `tradingagents/llm_adapters/openai_compatible_base.py`：

```python
# 在 OPENAI_COMPATIBLE_PROVIDERS 字典中添加配置
OPENAI_COMPATIBLE_PROVIDERS = {
    # ... 现有配置 ...
  
    "your_provider": {
        "adapter_class": ChatYourProvider,
        "base_url": "https://api.yourprovider.com/v1",
        "api_key_env": "YOUR_PROVIDER_API_KEY",
        "models": {
            "your-model-1": {"context_length": 8192, "supports_function_calling": True},
            "your-model-2": {"context_length": 32768, "supports_function_calling": True},
        }
    },
}
```

#### 3. 更新导入文件

编辑 `tradingagents/llm_adapters/__init__.py`：

```python
from .your_provider_adapter import ChatYourProvider

__all__ = ["ChatDashScope", "ChatDashScopeOpenAI", "ChatGoogleOpenAI", "ChatYourProvider"]
```

#### 4. 前端集成

编辑 `web/components/sidebar.py`，在模型选择部分添加：

```python
# 在 llm_provider 选择中添加选项
options=["dashscope", "deepseek", "google", "openai", "openrouter", "custom_openai", "your_provider"],

# 在格式化映射中添加
format_mapping={
    # ... 现有映射 ...
    "your_provider": "🚀 您的提供商",
}

# 添加模型选择逻辑
elif llm_provider == "your_provider":
    your_provider_options = ["your-model-1", "your-model-2"]
  
    current_index = 0
    if st.session_state.llm_model in your_provider_options:
        current_index = your_provider_options.index(st.session_state.llm_model)
  
    llm_model = st.selectbox(
        "选择模型",
        options=your_provider_options,
        index=current_index,
        format_func=lambda x: {
            "your-model-1": "Model 1 - 快速",
            "your-model-2": "Model 2 - 强大",
        }.get(x, x),
        help="选择用于分析的模型",
        key="your_provider_model_select"
    )
```

#### 5. 运行时配置

在绝大多数情况下，新增一个 OpenAI 兼容提供商时，无需修改 <mcfile name="analysis_runner.py" path="web/utils/analysis_runner.py"></mcfile>。原因：

- 侧边栏 <mcfile name="sidebar.py" path="web/components/sidebar.py"></mcfile> 收集 `llm_provider` 与 `llm_model`
- 这些参数会被传入 <mcfile name="trading_graph.py" path="tradingagents/graph/trading_graph.py"></mcfile>，由 <mcsymbol name="create_openai_compatible_llm" filename="openai_compatible_base.py" path="tradingagents/llm_adapters/openai_compatible_base.py" startline="329" type="function"></mcsymbol> 基于 `OPENAI_COMPATIBLE_PROVIDERS` 自动实例化正确的适配器
- 因此，真正的“运行时配置”主要体现在 <mcfile name="openai_compatible_base.py" path="tradingagents/llm_adapters/openai_compatible_base.py"></mcfile> 的注册表和工厂方法，而非 analysis_runner 本身

推荐做法：

- 在 <mcfile name="openai_compatible_base.py" path="tradingagents/llm_adapters/openai_compatible_base.py"></mcfile> 中完善 `OPENAI_COMPATIBLE_PROVIDERS`（base_url、api_key 环境变量、模型清单等）
- 在 <mcfile name="sidebar.py" path="web/components/sidebar.py"></mcfile> 中新增该 `llm_provider` 的下拉选项与模型列表
- 保持 <mcfile name="analysis_runner.py" path="web/utils/analysis_runner.py"></mcfile> 无需改动

何时需要少量修改 analysis_runner：

- 该提供商要求在分析阶段动态切换不同模型（例如“快速/深度”分开）
- 需要在任务执行流水线中注入特定的 header、代理或文件型鉴权
- 需要为该提供商设置额外的日志或成本估算逻辑

即便如此，也请：

- 不在 analysis_runner 硬编码模型清单或 API 细节，统一放在 `OPENAI_COMPATIBLE_PROVIDERS`
- 仍然使用 <mcsymbol name="create_openai_compatible_llm" filename="openai_compatible_base.py" path="tradingagents/llm_adapters/openai_compatible_base.py" startline="329" type="function"></mcsymbol> 创建实例，避免重复初始化逻辑

编辑 `web/utils/analysis_runner.py`，在模型配置部分添加：

```python
elif llm_provider == "your_provider":
    config["backend_url"] = "https://api.yourprovider.com/v1"
    logger.info(f"🚀 [您的提供商] 使用模型: {llm_model}")
    logger.info(f"🚀 [您的提供商] API端点: https://api.yourprovider.com/v1")
```

### 📋 必需的环境变量

在项目根目录的 `.env.example` 文件中添加：

```bash
# 您的提供商 API 配置
YOUR_PROVIDER_API_KEY=your_api_key_here
```

## 🧪 测试指南

### 1. 基础连接测试

创建测试文件 `test_your_provider.py`：

```python
import os
from tradingagents.llm_adapters.your_provider_adapter import ChatYourProvider

def test_basic_connection():
    """测试基础连接"""
    # 设置测试环境变量
    os.environ["YOUR_PROVIDER_API_KEY"] = "your_test_key"
  
    try:
        llm = ChatYourProvider(model="your-model-1")
        response = llm.invoke("Hello, world!")
        print(f"✅ 连接成功: {response.content}")
        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

if __name__ == "__main__":
    test_basic_connection()
```

### 2. 工具调用测试

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """获取城市天气信息"""
    return f"{city}今天晴天，温度25°C"

def test_function_calling():
    """测试工具调用"""
    llm = ChatYourProvider(model="your-model-1")
    llm_with_tools = llm.bind_tools([get_weather])
  
    response = llm_with_tools.invoke("北京天气如何？")
    print(f"工具调用测试: {response}")
```

### 3. Web 界面测试

启动 Web 应用进行集成测试：

```bash
cd web
streamlit run app.py
```

验证：

- [ ]  在侧边栏能正确选择新提供商
- [ ]  模型选择下拉菜单工作正常
- [ ]  API 密钥检查显示正确状态
- [ ]  能成功进行股票分析

## 📊 验证清单

提交 PR 前，请确保以下项目都已完成：

### 代码实现

- [ ]  创建了适配器类并继承正确的基类
- [ ]  在 `OPENAI_COMPATIBLE_PROVIDERS` 中正确注册
- [ ]  更新了 `__init__.py` 导入
- [ ]  前端集成完整（模型选择、配置界面）
- [ ]  运行时配置正确

### 环境配置

- [ ]  添加了环境变量示例到 `.env.example`
- [ ]  API 密钥验证逻辑正确
- [ ]  错误处理完善

### 测试验证

- [ ]  基础连接测试通过
- [ ]  工具调用测试通过（如果支持）
- [ ]  Web 界面集成测试通过
- [ ]  至少完成一次完整的股票分析

### 文档更新

- [ ]  更新了相关 README 文档
- [ ]  添加了模型特性说明
- [ ]  提供了使用示例

## 💡 实际接入案例：百度千帆模型

### 案例背景

百度千帆模型是一个典型的国产大模型接入案例，在实际接入过程中遇到了一些特殊问题，以下是完整的解决方案。

### 接入步骤详解

#### 1. 使用 OpenAI 兼容基座注册千帆提供商

```python
# 在 tradingagents/llm_adapters/openai_compatible_base.py 内部注册
OPENAI_COMPATIBLE_PROVIDERS["qianfan"] = {
    "base_url": "https://qianfan.baidubce.com/v2",
    "api_key_env": "QIANFAN_API_KEY",
    "models": {
        "ernie-3.5-8k": {"context_length": 8192, "supports_function_calling": True},
        "ernie-4.0-turbo-8k": {"context_length": 8192, "supports_function_calling": True},
        "ERNIE-Speed-8K": {"context_length": 8192, "supports_function_calling": True},
        "ERNIE-Lite-8K": {"context_length": 8192, "supports_function_calling": False},
    }
}
```

> 提示：无需单独的 qianfan_adapter.py 文件，统一由 openai_compatible_base 进行适配。

#### 2. 注册千帆提供商

```python
# 在 openai_compatible_base.py 中添加
OPENAI_COMPATIBLE_PROVIDERS = {
    # ... 现有配置 ...
  
    "qianfan": {
        "base_url": "https://qianfan.baidubce.com/v2",
        "api_key_env": "QIANFAN_API_KEY",
        "models": {
            "ernie-3.5-8k": {"context_length": 8192, "supports_function_calling": True},
            "ernie-4.0-turbo-8k": {"context_length": 8192, "supports_function_calling": True},
            "ERNIE-Lite-8K": {"context_length": 8192, "supports_function_calling": False},
            "ERNIE-Speed-8K": {"context_length": 8192, "supports_function_calling": True},
        }
    },
}
```

#### 3. 配置环境变量

在 `.env` 文件中添加千帆API配置：

```bash
# 千帆API配置
QIANFAN_ACCESS_KEY=your_access_key_here
QIANFAN_SECRET_KEY=your_secret_key_here
```

#### 4. 添加模型价格配置

在 `config/pricing.json` 文件中添加千帆模型的价格信息：

```json
{
  "provider": "qianfan",
  "model_name": "ernie-3.5-8k",
  "input_price_per_1k": 0.0025,
  "output_price_per_1k": 0.005,
  "currency": "CNY"
},
{
  "provider": "qianfan",
  "model_name": "ernie-4.0-turbo-8k",
  "input_price_per_1k": 0.03,
  "output_price_per_1k": 0.09,
  "currency": "CNY"
},
{
  "provider": "qianfan",
  "model_name": "ERNIE-Speed-8K",
  "input_price_per_1k": 0.0004,
  "output_price_per_1k": 0.0008,
  "currency": "CNY"
},
{
  "provider": "qianfan",
  "model_name": "ERNIE-Lite-8K",
  "input_price_per_1k": 0.0008,
  "output_price_per_1k": 0.002,
  "currency": "CNY"
}
```

**价格说明**：
- 价格单位为每1000个token的费用
- 货币单位为人民币（CNY）
- 价格基于百度千帆官方定价，可能会有调整

#### 5. 前端界面集成

```python
# 在 sidebar.py 中添加千帆选项
elif llm_provider == "qianfan":
    qianfan_options = [
        "ernie-3.5-8k",
        "ernie-4.0-turbo-8k",
        "ERNIE-Speed-8K",
        "ERNIE-Lite-8K"
    ]

    current_index = 0
    if st.session_state.llm_model in qianfan_options:
        current_index = qianfan_options.index(st.session_state.llm_model)

    llm_model = st.selectbox(
        "选择文心一言模型",
        options=qianfan_options,
        index=current_index,
        format_func=lambda x: {
            "ernie-3.5-8k": "ERNIE 3.5 8K - ⚡ 快速高效",
            "ernie-4.0-turbo-8k": "ERNIE 4.0 Turbo 8K - 🚀 强大推理",
            "ERNIE-Speed-8K": "ERNIE Speed 8K - 🏃 极速响应",
            "ERNIE-Lite-8K": "ERNIE Lite 8K - 💡 轻量经济"
        }[x],
        help="选择用于分析的文心一言（千帆）模型",
        key="qianfan_model_select"
    )

    if st.session_state.llm_model != llm_model:
        logger.debug(f"🔄 [Persistence] Qianfan模型变更: {st.session_state.llm_model} → {llm_model}")
    st.session_state.llm_model = llm_model
    logger.debug(f"💾 [Persistence] Qianfan模型已保存: {llm_model}")
```


## 🚨 常见问题与解决方案

### 1. API 密钥验证失败

**问题**: 环境变量设置正确但仍提示 API 密钥错误

**解决方案**:

- 检查 API 密钥格式是否符合提供商要求
- 确认环境变量名称拼写正确
- 检查 `.env` 文件是否在正确位置
- **千帆特殊情况**: 需要同时设置 `QIANFAN_API_KEY`

### 2. 工具调用不工作

**问题**: 模型不能正确调用工具

**解决方案**:

- 确认模型本身支持 Function Calling
- 检查 API 格式是否完全兼容 OpenAI 标准
- 查看是否需要特殊的工具调用格式
- **千帆特殊情况**: 需要转换工具定义格式，参考上述案例

### 3. 前端界面不显示新模型

**问题**: 侧边栏看不到新添加的提供商

**解决方案**:

- 清除浏览器缓存
- 检查 `sidebar.py` 中的选项列表
- 确认 Streamlit 重新加载了代码
- **调试技巧**: 在浏览器开发者工具中查看控制台错误

### 4. 请求超时或连接错误

**问题**: API 请求经常超时

**解决方案**:

- 调整 `timeout` 参数
- 检查网络连接和 API 端点状态
- 考虑添加重试机制
- **国产模型特殊情况**: 某些国产模型服务器在海外访问较慢，建议增加超时时间

### 5. 中文编码问题

**问题**: 中文输入或输出出现乱码

**解决方案**:

```python
# 确保请求和响应都使用 UTF-8 编码
import json

def safe_json_dumps(data):
    return json.dumps(data, ensure_ascii=False, indent=2)

def safe_json_loads(text):
    return json.loads(text.encode('utf-8').decode('utf-8'))
```
### 6. 成本控制问题

**问题**: 某些模型调用成本过高

**解决方案**:

- 在配置中设置合理的 `max_tokens` 限制
- 使用成本较低的模型进行初步分析
- 实现智能模型路由，根据任务复杂度选择模型

```python
# 智能模型选择示例
def select_model_by_task(task_complexity: str) -> str:
    if task_complexity == "simple":
        return "ERNIE-Lite-8K"  # 成本低
    elif task_complexity == "medium":
        return "ERNIE-3.5-8K"  # 平衡
    else:
        return "ERNIE-4.0-8K"  # 性能强
```
## 📝 PR 提交规范

### 提交信息格式

```
feat(llm): add {ProviderName} LLM integration

- Add {ProviderName} OpenAI-compatible adapter
- Update frontend model selection UI
- Add configuration and environment variables
- Include basic tests and documentation

Closes #{issue_number}
```
### PR 描述模板

```markdown
## 🚀 新增大模型支持：{ProviderName}

### 📋 变更概述
- 添加了 {ProviderName} 的 OpenAI 兼容适配器
- 更新了前端模型选择界面
- 完善了配置和环境变量
- 包含了基础测试

### 🧪 测试情况
- [x] 基础连接测试通过
- [x] 工具调用测试通过（如适用）
- [x] Web 界面集成测试通过
- [x] 完整的股票分析测试通过

### 📚 支持的模型
- `model-1`: 快速模型，适合简单任务
- `model-2`: 强大模型，适合复杂分析

### 🔧 配置要求
需要设置环境变量：`YOUR_PROVIDER_API_KEY`

### 📸 截图
（添加前端界面截图）

### ✅ 检查清单
- [x] 代码遵循项目规范
- [x] 添加了必要的测试
- [x] 更新了相关文档
- [x] 通过了所有现有测试
```
## 🎯 最佳实践

### 1. 错误处理

- 提供清晰的错误消息
- 区分不同类型的错误（API 密钥、网络、模型等）
- 添加重试机制处理临时故障

### 2. 日志记录

- 使用统一的日志格式
- 记录关键操作和错误
- 避免记录敏感信息（API 密钥等）

### 3. 性能优化

- 合理设置超时时间
- 考虑并发限制
- 优化大模型调用的 token 使用

### 4. 用户体验

- 提供清晰的模型选择说明
- 添加合适的帮助文本
- 确保错误消息用户友好

## 📞 获取帮助

如果在开发过程中遇到问题：

1. **查看现有实现**: 参考 `deepseek_adapter.py` 或 `dashscope_adapter.py`
2. **阅读基类文档**: 查看 `openai_compatible_base.py` 的注释
3. **提交 Issue**: 在 GitHub 上创建问题描述
4. **加入讨论**: 参与项目的 Discussion 板块

## 🔄 版本控制建议

1. **分支命名**: `feature/add-{provider}-llm`
2. **提交频率**: 小步骤频繁提交
3. **提交信息**: 使用清晰的描述性信息
4. **代码审查**: 提交前自我审查代码质量

---

**感谢您为 TradingAgentsCN 项目贡献新的大模型支持！** 🎉

通过遵循本指南，您的贡献将更容易被审查和合并，同时也为其他开发者提供了良好的参考示例。
