import time
from typing import Any, Callable, Dict, List, Optional

from langchain_core.messages import RemoveMessage, ToolMessage

from tradingagents.agents import (
    create_bear_researcher,
    create_bull_researcher,
    create_fundamentals_analyst,
    create_market_analyst,
    create_msg_delete,
    create_news_analyst,
    create_neutral_debator,
    create_risk_manager,
    create_risky_debator,
    create_research_manager,
    create_safe_debator,
    create_social_media_analyst,
    create_trader,
)
from app.services.capabilities import capability_executor
from app.services.sessions import session_event_store, session_runtime_service
from .llm_judge import JUDGE_TARGETS, LLMJudge
from tradingagents.skills import filter_allowed_tools
try:
    from agentscope.agent import AgentBase  # noqa: F401
except Exception as exc:  # pragma: no cover - handled at runtime
    _AGENTSCOPE_IMPORT_ERROR = exc
else:
    _AGENTSCOPE_IMPORT_ERROR = None


class _StateReducer:
    @staticmethod
    def merge_messages(
        current: List[Any],
        updates: List[Any],
    ) -> List[Any]:
        if not updates:
            return current

        new_messages = list(current)
        for msg in updates:
            if isinstance(msg, RemoveMessage):
                msg_id = getattr(msg, "id", None)
                if msg_id:
                    new_messages = [
                        existing
                        for existing in new_messages
                        if getattr(existing, "id", None) != msg_id
                    ]
                continue
            new_messages.append(msg)
        return new_messages

    @staticmethod
    def apply(state: Dict[str, Any], update: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not update:
            return state

        next_state = dict(state)
        for key, value in update.items():
            if key == "messages":
                updates = value if isinstance(value, list) else [value]
                next_state["messages"] = _StateReducer.merge_messages(
                    state.get("messages", []), updates
                )
            else:
                next_state[key] = value
        return next_state


class AgentScopeStateAgent:
    def __init__(self, name: str, node_func: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.name = name
        self.node_func = node_func

    def reply(self, state):
        update = self.node_func(state)
        return _StateReducer.apply(state, update)


class AgentScopeRunner:
    def __init__(
        self,
        quick_llm,
        deep_llm,
        toolkit,
        bull_memory,
        bear_memory,
        trader_memory,
        invest_judge_memory,
        risk_manager_memory,
        conditional_logic,
        tool_map: Dict[str, List[Any]],
    ):
        if _AGENTSCOPE_IMPORT_ERROR:
            raise ImportError(
                "AgentScope is required for the AgentScope runner."
            ) from _AGENTSCOPE_IMPORT_ERROR

        self.quick_llm = quick_llm
        self.deep_llm = deep_llm
        self.toolkit = toolkit
        self.bull_memory = bull_memory
        self.bear_memory = bear_memory
        self.trader_memory = trader_memory
        self.invest_judge_memory = invest_judge_memory
        self.risk_manager_memory = risk_manager_memory
        self.conditional_logic = conditional_logic
        self.tool_map = tool_map

        self.delete_node = create_msg_delete()

        self.analyst_nodes = {
            "market": create_market_analyst(self.quick_llm, self.toolkit),
            "social": create_social_media_analyst(self.quick_llm, self.toolkit),
            "news": create_news_analyst(self.quick_llm, self.toolkit),
            "fundamentals": create_fundamentals_analyst(self.quick_llm, self.toolkit),
        }

        self.bull_researcher = create_bull_researcher(self.quick_llm, self.bull_memory)
        self.bear_researcher = create_bear_researcher(self.quick_llm, self.bear_memory)
        self.research_manager = create_research_manager(
            self.deep_llm, self.invest_judge_memory
        )
        self.trader = create_trader(self.quick_llm, self.trader_memory)

        self.risky_analyst = create_risky_debator(self.quick_llm)
        self.safe_analyst = create_safe_debator(self.quick_llm)
        self.neutral_analyst = create_neutral_debator(self.quick_llm)
        self.risk_manager = create_risk_manager(self.deep_llm, self.risk_manager_memory)
        self.judge = None
        if toolkit.config.get("llm_judge_enabled", True):
            self.judge = LLMJudge(
                self.deep_llm,
                min_score=int(toolkit.config.get("llm_judge_min_score", 7)),
            )

    def _apply_judge_feedback(self, state: Dict[str, Any], node_name: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        target = JUDGE_TARGETS.get(node_name)
        if not target:
            return state

        feedback_map = dict(state.get("judge_feedback", {}) or {})
        score_map = dict(state.get("judge_scores", {}) or {})
        feedback_map[target["feedback_key"]] = feedback.get("feedback", "")
        score_map[node_name] = {
            "score": feedback.get("score", 0),
            "passed": feedback.get("passed", False),
            "missing_items": feedback.get("missing_items", []),
        }

        next_state = dict(state)
        next_state["judge_feedback"] = feedback_map
        next_state["judge_scores"] = score_map
        return next_state

    def _sanitize_message_history(self, messages: List[Any]) -> List[Any]:
        """
        清理非法消息序列，避免出现孤立 ToolMessage 导致厂商 400。
        规则：ToolMessage 只能紧跟在带 tool_calls 的 AIMessage 之后。
        """
        if not messages:
            return messages

        sanitized: List[Any] = []
        pending_tool_call_ids: set[str] = set()
        expecting_tool_messages = False
        enforce_tool_call_ids = False
        removed_count = 0

        for msg in messages:
            # ToolMessage 只能在待处理 tool_calls 阶段出现
            if isinstance(msg, ToolMessage):
                tool_call_id = getattr(msg, "tool_call_id", None)
                if not expecting_tool_messages:
                    removed_count += 1
                    continue
                if enforce_tool_call_ids and tool_call_id not in pending_tool_call_ids:
                    removed_count += 1
                    continue

                sanitized.append(msg)
                if tool_call_id in pending_tool_call_ids:
                    pending_tool_call_ids.remove(tool_call_id)
                continue

            # 非 ToolMessage 到来，结束 tool_calls 响应窗口
            expecting_tool_messages = False
            enforce_tool_call_ids = False
            pending_tool_call_ids.clear()
            sanitized.append(msg)

            # 如果是带 tool_calls 的 AIMessage，开启响应窗口
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                expecting_tool_messages = True
                enforce_tool_call_ids = False
                for tc in tool_calls:
                    tc_id = tc.get("id") if isinstance(tc, dict) else None
                    if tc_id:
                        pending_tool_call_ids.add(tc_id)
                        enforce_tool_call_ids = True

        if removed_count > 0:
            from tradingagents.utils.logging_init import get_logger

            logger = get_logger("agents")
            logger.warning(
                f"🧹 [消息清理] 移除 {removed_count} 条非法 ToolMessage，避免模型请求失败"
            )

        return sanitized

    def _execute_tool_calls(
        self, state: Dict[str, Any], tools: List[Any]
    ) -> Dict[str, Any]:
        messages = state.get("messages", [])
        if not messages:
            return {}

        last_message = messages[-1]
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return {}

        allowed_tools = ((state.get("skill_tool_policy") or {}).get("allowed_tools") or [])
        filtered_tools = filter_allowed_tools(tools, allowed_tools)
        session_id = str(state.get("session_id", "") or "")

        tool_messages = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id")

            tool_result = None
            for tool in filtered_tools:
                current_tool_name = getattr(tool, "name", None) or getattr(
                    tool, "__name__", None
                )
                if current_tool_name == tool_name:
                    capability_result = capability_executor.execute_local(
                        tool,
                        tool_args,
                        session_id=session_id,
                    )
                    tool_result = (
                        capability_result.result
                        if capability_result.success
                        else f"工具执行失败: {capability_result.error}"
                    )
                    break

            if tool_result is None:
                if allowed_tools:
                    tool_result = f"工具未被当前 skill 允许或未找到: {tool_name}"
                    if session_id:
                        session_event_store.append_event_sync(
                            session_id,
                            "tool_call_blocked",
                            {
                                "capability_name": tool_name,
                                "reason": "not_allowed_or_not_found",
                            },
                            source="runtime",
                        )
                else:
                    tool_result = f"未找到工具: {tool_name}"
                    if session_id:
                        session_event_store.append_event_sync(
                            session_id,
                            "tool_call_blocked",
                            {
                                "capability_name": tool_name,
                                "reason": "not_found",
                            },
                            source="runtime",
                        )

            tool_messages.append(
                ToolMessage(content=str(tool_result), tool_call_id=tool_id)
            )

        return {"messages": tool_messages}

    def run(
        self,
        init_state: Dict[str, Any],
        selected_analysts: List[str],
        progress_sender: Optional[Callable[[str], None]] = None,
    ) -> tuple[Dict[str, Any], Dict[str, float]]:
        state = init_state
        node_timings: Dict[str, float] = {}

        def run_agent(node_name: str, node_func, send_progress: bool = True):
            nonlocal state
            if send_progress and progress_sender:
                progress_sender(node_name)
            start = time.time()
            max_attempts = 1 + int(self.toolkit.config.get("llm_judge_max_retries", 1))
            session_id = str(state.get("session_id", "") or "")
            if session_id:
                session_event_store.append_event_sync(
                    session_id,
                    "node_started",
                    {"node_name": node_name, "attempts": max_attempts},
                    node_name=node_name,
                    source="runtime",
                )

            for attempt in range(max_attempts):
                # 防御性清理：避免历史中残留非法 ToolMessage 影响下一次 LLM 调用
                if "messages" in state:
                    state["messages"] = self._sanitize_message_history(state.get("messages", []))
                agent = AgentScopeStateAgent(node_name, node_func)
                updated_state = agent.reply(state)

                if not self.judge or not self.judge.should_judge(node_name):
                    state = updated_state
                    break

                judge_result = self.judge.evaluate(node_name, state, updated_state)
                updated_state = self._apply_judge_feedback(updated_state, node_name, judge_result or {})
                if session_id:
                    session_event_store.append_event_sync(
                        session_id,
                        "judge_evaluated",
                        {
                            "node_name": node_name,
                            "attempt": attempt + 1,
                            "score": (judge_result or {}).get("score", 0),
                            "passed": (judge_result or {}).get("passed", True),
                            "feedback": (judge_result or {}).get("feedback", ""),
                        },
                        node_name=node_name,
                        source="judge",
                    )

                if judge_result and not judge_result.get("passed", True) and attempt < max_attempts - 1:
                    from tradingagents.utils.logging_init import get_logger
                    logger = get_logger("agents")
                    logger.warning(
                        f"⚠️ [LLM Judge] {node_name} 评分 {judge_result.get('score', 0)}/10，"
                        f"触发重生成: {judge_result.get('feedback', '')}"
                    )
                    state = updated_state
                    continue

                state = updated_state
                break

            node_timings[node_name] = time.time() - start
            if session_id:
                node_completed_event = session_event_store.append_event_sync(
                    session_id,
                    "node_completed",
                    {
                        "node_name": node_name,
                        "duration_ms": int(node_timings[node_name] * 1000),
                    },
                    node_name=node_name,
                    source="runtime",
                )
                try:
                    session_runtime_service.checkpoint_sync(
                        session_id,
                        state_summary={
                            "node_name": node_name,
                            "last_event_seq": int(node_completed_event.get("seq", 0)),
                        },
                        recoverable_state={
                            "messages_count": len(state.get("messages", [])),
                            "judge_feedback": dict(state.get("judge_feedback", {}) or {}),
                            "judge_scores": dict(state.get("judge_scores", {}) or {}),
                        },
                        checkpoint_id=f"{node_name.lower().replace(' ', '_')}_{int(time.time() * 1000)}",
                        created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                    )
                except Exception:
                    pass

        def run_tool_node(node_name: str, tools: List[Any]):
            nonlocal state
            start = time.time()
            update = self._execute_tool_calls(state, tools)
            state = _StateReducer.apply(state, update)
            node_timings[node_name] = time.time() - start

        def run_msg_clear(node_name: str):
            nonlocal state
            start = time.time()
            update = self.delete_node(state)
            state = _StateReducer.apply(state, update)
            node_timings[node_name] = time.time() - start

        # Analysts
        for analyst_key in selected_analysts:
            analyst_node = self.analyst_nodes[analyst_key]
            analyst_name = f"{analyst_key.capitalize()} Analyst"
            run_agent(analyst_name, analyst_node)

            while True:
                next_step = getattr(
                    self.conditional_logic, f"should_continue_{analyst_key}"
                )(state)
                if next_step.startswith("tools_"):
                    run_tool_node(next_step, self.tool_map.get(analyst_key, []))
                    run_agent(analyst_name, analyst_node)
                    continue
                if next_step.startswith("Msg Clear"):
                    run_msg_clear(next_step)
                break

        # Research debate
        next_node = "Bull Researcher"
        while True:
            if next_node == "Bull Researcher":
                run_agent(next_node, self.bull_researcher)
            elif next_node == "Bear Researcher":
                run_agent(next_node, self.bear_researcher)
            elif next_node == "Research Manager":
                run_agent(next_node, self.research_manager)
                break

            next_node = self.conditional_logic.should_continue_debate(state)
            if next_node == "Research Manager":
                run_agent(next_node, self.research_manager)
                break

        # Trader
        run_agent("Trader", self.trader)

        # Risk management
        next_node = "Risky Analyst"
        while True:
            if next_node == "Risk Judge":
                run_agent(next_node, self.risk_manager)
                break

            if next_node == "Risky Analyst":
                run_agent(next_node, self.risky_analyst)
            elif next_node == "Safe Analyst":
                run_agent(next_node, self.safe_analyst)
            elif next_node == "Neutral Analyst":
                run_agent(next_node, self.neutral_analyst)

            next_node = self.conditional_logic.should_continue_risk_analysis(state)
            if next_node == "Risk Judge":
                run_agent(next_node, self.risk_manager)
                break

        if progress_sender:
            progress_sender("__end__")

        return state, node_timings
