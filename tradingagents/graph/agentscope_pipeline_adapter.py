from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, List

from agentscope.agent import AgentBase
from agentscope.message import Msg
from agentscope.pipeline import FanoutPipeline, MsgHub


class StateFunctionAgent(AgentBase):
    """Adapter from QuantScope state functions to AgentScope AgentBase."""

    def __init__(self, name: str, handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        super().__init__()
        self.name = name
        self._handler = handler
        self.observed_messages: List[Msg] = []
        self.last_result: Dict[str, Any] | None = None
        self.last_duration_ms = 0

    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        if msg is None:
            return
        if isinstance(msg, list):
            self.observed_messages.extend(msg)
        else:
            self.observed_messages.append(msg)

    async def reply(self, msg: Msg | list[Msg] | None = None, **kwargs: Any) -> Msg:
        state = dict(kwargs.get("state") or {})
        start = time.time()
        self.last_result = await asyncio.to_thread(self._handler, state)
        self.last_duration_ms = int((time.time() - start) * 1000)
        return Msg(
            name=self.name,
            role="assistant",
            content=f"{self.name} completed",
            metadata={
                "duration_ms": self.last_duration_ms,
                "has_result": self.last_result is not None,
            },
        )


async def run_agentscope_fanout(
    *,
    name: str,
    agents: List[StateFunctionAgent],
    state: Dict[str, Any],
) -> list[Msg]:
    announcement = Msg(
        name=name,
        role="system",
        content=f"{name} started",
        metadata={"agent_names": [agent.name for agent in agents]},
    )
    async with MsgHub(
        participants=agents,
        announcement=announcement,
        enable_auto_broadcast=True,
        name=name,
    ):
        pipeline = FanoutPipeline(agents=agents, enable_gather=True)
        return await pipeline(
            Msg(name=name, role="user", content=f"run {name}"),
            state=state,
        )
