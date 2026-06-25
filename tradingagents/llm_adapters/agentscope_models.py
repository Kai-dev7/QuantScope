"""
AgentScope 1.0.x 模型工厂（兼容 agentscope>=1.0.13）

根据 provider 创建 AgentScope 原生模型实例，并提供与原 langchain 适配器
相同的同步调用接口（invoke / invoke_with_tools）。

支持厂商：
  openai / siliconflow / openrouter / ollama / 自定义兼容 → OpenAIChatModel
  deepseek                                                 → OpenAIChatModel + DeepSeek base_url
  dashscope / alibaba / 阿里百炼                           → DashScopeChatModel
  anthropic                                                → AnthropicChatModel
  google / gemini                                          → GeminiChatModel
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import os
from typing import Any, Dict, List, Optional

from tradingagents.utils.logging_init import get_logger

logger = get_logger("llm_adapters.agentscope")


# ---------------------------------------------------------------------------
# 内部工具：同步运行异步协程（线程安全）
# ---------------------------------------------------------------------------

def _run_coro_sync(coro):
    """将 async 协程转为同步调用。

    - 若当前线程没有事件循环（大多数情况）→ asyncio.run()
    - 若已有运行中事件循环（Jupyter/嵌套场景） → 新线程中 asyncio.run()
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


# ---------------------------------------------------------------------------
# 统一结果包装（兼容 llm.invoke().content 调用约定）
# ---------------------------------------------------------------------------

class SyncChatResult:
    """统一的同步调用结果。

    兼容原 llm.invoke(prompt).content 调用约定，同时携带 tool_calls 列表。
    """

    def __init__(self, content: str, tool_calls: list, usage: Optional[Any] = None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.usage = usage

    def __str__(self) -> str:
        return self.content


# ---------------------------------------------------------------------------
# AgentScope 1.0 同步模型包装器
# ---------------------------------------------------------------------------

class AgentScopeModelWrapper:
    """
    同步包装 AgentScope 1.0 模型，暴露：
      - invoke(prompt)              → SyncChatResult  （纯文本调用）
      - invoke_with_tools(messages, tools_schemas) → SyncChatResult

    token 统计从 ChatResponse['usage'] 读取。
    """

    def __init__(self, model, provider_name: str, model_name: str):
        self._model = model
        self.provider_name = provider_name
        self.model_name = model_name

    # ------------------------------------------------------------------
    # 内部：async 调用 agentscope 1.0 模型
    # agentscope 1.0.x OpenAIChatModel.__call__ 接收 list[dict] (OpenAI 格式)
    # ------------------------------------------------------------------

    async def _async_call(
        self,
        messages: List[Dict],
        tools_schemas: Optional[List[Dict]] = None,
    ) -> SyncChatResult:
        """
        直接将 OpenAI 格式的 messages list[dict] 传给 agentscope 1.0 模型。
        模型返回 ChatResponse（dict-like），包含 content 字段（block 列表）。
        """
        import json as _json

        # agentscope 1.0.20: await model(messages: list[dict], tools=...) → ChatResponse
        response = await self._model(
            messages,
            tools=tools_schemas if tools_schemas else None,
        )

        # 解析 ChatResponse（dict-like subclass）
        content_blocks = response.get("content") if isinstance(response, dict) else getattr(response, "content", [])
        if content_blocks is None:
            content_blocks = []

        text_content = ""
        tool_calls: List[Dict] = []

        for block in content_blocks:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                text_content += getattr(block, "text", "")
            elif block_type in ("tool_use", "tool_call"):
                raw_input = getattr(block, "input", {})
                if isinstance(raw_input, str):
                    try:
                        raw_input = _json.loads(raw_input)
                    except Exception:
                        raw_input = {"_raw": raw_input}
                tool_calls.append(
                    {
                        "id": getattr(block, "id", ""),
                        "name": getattr(block, "name", ""),
                        "args": raw_input,
                    }
                )

        # token 统计
        usage = response.get("usage") if isinstance(response, dict) else getattr(response, "usage", None)
        self._track_tokens(usage)

        return SyncChatResult(content=text_content, tool_calls=tool_calls, usage=usage)

    def _track_tokens(self, usage: Any) -> None:
        if not usage:
            return
        # agentscope 1.0 usage 格式可能是 dict 或对象
        if isinstance(usage, dict):
            input_tokens = usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0) or 0
            output_tokens = usage.get("completion_tokens", 0) or usage.get("output_tokens", 0) or 0
        else:
            input_tokens = (
                getattr(usage, "prompt_tokens", 0)
                or getattr(usage, "input_tokens", 0)
                or 0
            )
            output_tokens = (
                getattr(usage, "completion_tokens", 0)
                or getattr(usage, "output_tokens", 0)
                or 0
            )
        if input_tokens == 0 and output_tokens == 0:
            return
        try:
            from tradingagents.config.config_manager import token_tracker
            token_tracker.track_usage(
                provider=self.provider_name,
                model_name=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 公共同步接口（与原 langchain 适配器兼容）
    # ------------------------------------------------------------------

    def invoke(self, prompt: Any) -> SyncChatResult:
        """兼容 llm.invoke(prompt) 调用约定，纯文本不带工具。

        prompt 可以是：
          - str        → 单条 user 消息
          - list[dict] → OpenAI 格式消息列表（直接透传）
          - ChatPromptValue / BaseMessage → 兼容 langchain
        """
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list):
            # 检查是否是 list[dict]（OpenAI 格式）或 list[BaseMessage]
            if prompt and isinstance(prompt[0], dict):
                messages = prompt
            else:
                messages = _convert_lc_messages(prompt)
        elif hasattr(prompt, "to_messages"):
            # langchain ChatPromptValue
            messages = _convert_lc_messages(prompt.to_messages())
        elif hasattr(prompt, "content"):
            # 单个 BaseMessage 或类似对象
            messages = [{"role": "user", "content": str(prompt.content)}]
        else:
            messages = [{"role": "user", "content": str(prompt)}]

        return _run_coro_sync(self._async_call(messages))

    def invoke_with_tools(
        self,
        messages: List[Dict],
        tools_schemas: List[Dict],
    ) -> SyncChatResult:
        """带工具 schema 的调用，返回 SyncChatResult（可能含 tool_calls）。"""
        return _run_coro_sync(self._async_call(messages, tools_schemas))

    # ------------------------------------------------------------------
    # LangChain LCEL 兼容层 - 允许 prompt | llm.bind_tools(tools) 写法
    # ------------------------------------------------------------------

    def bind_tools(self, tools: list):
        """
        返回 RunnableLambda，兼容 LangChain LCEL 管道。
        tools 为 langchain @tool 装饰的函数列表。
        """
        from langchain_core.runnables import RunnableLambda

        def _invoke(input_val):
            # input_val 可能是 ChatPromptValue 或 list[BaseMessage]
            if hasattr(input_val, "to_messages"):
                lc_messages = input_val.to_messages()
            elif isinstance(input_val, list):
                lc_messages = input_val
            else:
                lc_messages = []

            dict_messages = _convert_lc_messages(lc_messages)
            schemas = [_lc_tool_to_openai_schema(t) for t in tools]
            result = self.invoke_with_tools(dict_messages, schemas)
            return _AgentScopeInvokeResult(result.content, result.tool_calls)

        return RunnableLambda(_invoke)

    # ------------------------------------------------------------------
    # 供 ReActAgent 使用的工具方法
    # ------------------------------------------------------------------

    def _get_formatter(self):
        """根据 provider 返回合适的 agentscope formatter。"""
        provider = self.provider_name.lower()
        if provider == "dashscope":
            from agentscope.formatter import DashScopeChatFormatter
            return DashScopeChatFormatter()
        else:
            from agentscope.formatter import OpenAIChatFormatter
            return OpenAIChatFormatter()


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------

def _is_valid_api_key(key: Optional[str]) -> bool:
    if not key or not key.strip():
        return False
    k = key.strip().lower()
    if k.startswith("your-") or k.startswith("your_"):
        return False
    if k in {"sk-xxxxxxxx", "sk-your-api-key"}:
        return False
    return len(key) > 10


# ---------------------------------------------------------------------------
# 模型工厂（agentscope 1.0.x API）
# ---------------------------------------------------------------------------

def create_agentscope_model(
    provider: str,
    model_name: str,
    api_key: Optional[str],
    base_url: Optional[str],
    temperature: float = 0.7,
    max_tokens: int = 4000,
    timeout: int = 180,
) -> AgentScopeModelWrapper:
    """
    根据 provider 创建 AgentScopeModelWrapper（同步包装）。
    适配 agentscope >= 1.0.13。

    厂商路由：
      dashscope / alibaba / 阿里百炼 → DashScopeChatModel
      deepseek                        → OpenAIChatModel + DeepSeek base_url
      其余（openai/siliconflow/openrouter/ollama/自定义）→ OpenAIChatModel
    """
    provider_lower = provider.lower()

    try:
        if provider_lower in ("dashscope", "alibaba") or "dashscope" in provider_lower or "阿里百炼" in provider:
            model = _create_dashscope(model_name, api_key, base_url, temperature, max_tokens)
            canonical_provider = "dashscope"
        elif provider_lower == "deepseek" or "deepseek" in provider_lower:
            ds_url = base_url or "https://api.deepseek.com"
            model = _create_openai_compatible("deepseek", model_name, api_key, ds_url, temperature, max_tokens)
            canonical_provider = "deepseek"
        else:
            model = _create_openai_compatible(provider, model_name, api_key, base_url, temperature, max_tokens)
            canonical_provider = provider_lower

        logger.info(f"✅ [AgentScope] 创建模型成功 provider={canonical_provider} model={model_name}")
        return AgentScopeModelWrapper(model, canonical_provider, model_name)

    except Exception as exc:
        logger.error(f"❌ [AgentScope] 创建模型失败 provider={provider} model={model_name}: {exc}")
        raise


def _create_openai_compatible(
    provider: str,
    model_name: str,
    api_key: Optional[str],
    base_url: Optional[str],
    temperature: float,
    max_tokens: int,
) -> Any:
    from agentscope.model import OpenAIChatModel

    if not _is_valid_api_key(api_key):
        env_map = {
            "openai": "OPENAI_API_KEY",
            "siliconflow": "SILICONFLOW_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "google": "GOOGLE_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }
        env_key = env_map.get(provider.lower(), f"{provider.upper()}_API_KEY")
        api_key = os.getenv(env_key) or os.getenv("OPENAI_API_KEY") or os.getenv("CUSTOM_OPENAI_API_KEY")

    client_kwargs: Dict[str, Any] = {}
    if base_url:
        client_kwargs["base_url"] = base_url.rstrip("/")

    return OpenAIChatModel(
        model_name=model_name,
        api_key=api_key or "dummy",
        client_kwargs=client_kwargs or None,
        generate_kwargs={"temperature": temperature, "max_tokens": max_tokens},
        stream=False,
    )


def _create_dashscope(
    model_name: str,
    api_key: Optional[str],
    base_url: Optional[str],
    temperature: float,
    max_tokens: int,
) -> Any:
    from agentscope.model import DashScopeChatModel

    if not _is_valid_api_key(api_key):
        api_key = os.getenv("DASHSCOPE_API_KEY")
    if not _is_valid_api_key(api_key):
        raise ValueError("DashScope API key 未找到，请设置 DASHSCOPE_API_KEY 或在数据库中配置")

    kwargs: Dict[str, Any] = {
        "model_name": model_name,
        "api_key": api_key,
        "generate_kwargs": {"temperature": temperature, "max_tokens": max_tokens},
        "stream": False,
    }
    if base_url:
        kwargs["base_http_api_url"] = base_url.rstrip("/")

    return DashScopeChatModel(**kwargs)


# ---------------------------------------------------------------------------
# LangChain 兼容辅助（仅供 bind_tools 使用）
# ---------------------------------------------------------------------------

class _AgentScopeInvokeResult:
    """模拟 langchain AIMessage，供分析师检查 .tool_calls 和 .content。"""

    def __init__(self, content: str, tool_calls: list):
        self.content = content
        self.tool_calls = tool_calls or []
        self.type = "ai"
        self.additional_kwargs = {}

    def __repr__(self) -> str:
        return f"_AgentScopeInvokeResult(content={self.content!r:.60}, tool_calls={self.tool_calls})"


def _convert_lc_messages(lc_messages: list) -> List[Dict]:
    """将 langchain BaseMessage 列表转为 OpenAI dict 格式。"""
    result = []
    for msg in lc_messages:
        # 处理我们自己的 _AgentScopeInvokeResult
        if isinstance(msg, _AgentScopeInvokeResult):
            if msg.tool_calls:
                result.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": msg.tool_calls,
                })
            else:
                result.append({"role": "assistant", "content": msg.content})
            continue

        # 处理 langchain 消息对象
        msg_type = getattr(msg, "type", None)
        content = getattr(msg, "content", "")
        if isinstance(content, list):
            # 某些 langchain message 的 content 是 blocks
            content = " ".join(
                b.get("text", "") if isinstance(b, dict) else str(b)
                for b in content
            )

        if msg_type in ("human", "user"):
            result.append({"role": "user", "content": content})
        elif msg_type in ("ai", "assistant"):
            tool_calls = getattr(msg, "tool_calls", []) or []
            if tool_calls:
                result.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": [
                        {
                            "id": tc.get("id", ""),
                            "name": tc.get("name", ""),
                            "args": tc.get("args", {}),
                        }
                        for tc in tool_calls
                    ],
                })
            else:
                result.append({"role": "assistant", "content": content})
        elif msg_type == "system":
            result.append({"role": "system", "content": content})
        elif msg_type == "tool":
            result.append({
                "role": "tool",
                "content": content,
                "tool_call_id": getattr(msg, "tool_call_id", ""),
            })
        else:
            result.append({"role": "user", "content": str(content)})
    return result


def _lc_tool_to_openai_schema(tool) -> Dict:
    """将 langchain @tool 对象转为 OpenAI function-calling 格式的 schema。"""
    name = getattr(tool, "name", None) or getattr(tool, "__name__", "unknown")
    description = getattr(tool, "description", "") or ""

    schema: Dict[str, Any] = {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": {}},
        },
    }

    args_schema = getattr(tool, "args_schema", None)
    if args_schema is not None:
        try:
            params = args_schema.schema()
            schema["function"]["parameters"] = params
        except Exception:
            pass

    return schema
