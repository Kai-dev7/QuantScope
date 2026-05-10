import time
from typing import Any, Callable

import httpx
from openai import APIConnectionError, APITimeoutError, RateLimitError

from tradingagents.utils.logging_init import get_logger

logger = get_logger("default")

RETRYABLE_LLM_ERRORS = (
    httpx.RemoteProtocolError,
    httpx.ConnectError,
    httpx.ReadTimeout,
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
)


def log_prompt_stats(node_name: str, prompt: str) -> None:
    prompt_length = len(prompt)
    estimated_tokens = int(prompt_length / 1.8)
    logger.info(
        "📊 [%s] Prompt统计: %s 字符, 估算~%s tokens",
        node_name,
        f"{prompt_length:,}",
        f"{estimated_tokens:,}",
    )


def invoke_llm_with_fallback(
    *,
    node_name: str,
    llm: Any,
    prompt: Any,
    fallback_content: str,
    on_retryable_error: Callable[[Exception], None] | None = None,
) -> str:
    start_time = time.time()
    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        logger.info(
            "⏱️ [%s] LLM调用完成，耗时: %.2f秒，输出长度: %s 字符",
            node_name,
            time.time() - start_time,
            f"{len(content):,}",
        )
        return content
    except RETRYABLE_LLM_ERRORS as e:
        logger.error(
            "⚠️ [%s] LLM连接失败，使用降级输出继续流程: %s",
            node_name,
            e,
        )
        if on_retryable_error:
            on_retryable_error(e)
        return fallback_content
