# TradingAgents/graph/trading_graph.py

import os
from pathlib import Path
import json
from datetime import date
from typing import Dict, Any, Tuple, List, Optional
import time

from tradingagents.llm_adapters.agentscope_models import create_agentscope_model, AgentScopeModelWrapper

from tradingagents.agents import *
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.memory import FinancialSituationMemory

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from tradingagents.dataflows.interface import set_config

from .conditional_logic import ConditionalLogic
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import SignalProcessor
from .agentscope_runner import AgentScopeRunner


def _is_valid_api_key(api_key: Optional[str]) -> bool:
    """过滤占位符 API Key，避免把模板值传给模型厂商接口。"""
    if not api_key or not api_key.strip():
        return False
    key = api_key.strip()
    lowered = key.lower()
    placeholder_values = {
        "your-api-key",
        "your_qwen_api_key_here",
        "your-qwen-api-key",
        "your-custom-openai-api-key",
        "sk-xxxxxxxx",
        "sk-your-api-key",
    }
    if lowered in placeholder_values:
        return False
    if lowered.startswith("your-") or lowered.startswith("your_"):
        return False
    return True


def _normalize_dashscope_base_url(base_url: Optional[str]) -> str:
    """统一 DashScope 为 OpenAI 兼容端点，避免 /api/v1 产生 404。"""
    default_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    if not base_url:
        return default_url

    normalized = base_url.strip().rstrip("/")
    if normalized.endswith("/api/v1"):
        normalized = normalized[: -len("/api/v1")] + "/compatible-mode/v1"
    return normalized


def create_llm_by_provider(
    provider: str,
    model: str,
    backend_url: str,
    temperature: float,
    max_tokens: int,
    timeout: int,
    api_key: str = None,
) -> AgentScopeModelWrapper:
    """
    根据 provider 创建 AgentScope 2.0 模型实例（同步包装器）。

    Args:
        provider: 供应商名称 (openai / deepseek / dashscope / siliconflow / ...)
        model: 模型名称
        backend_url: API 地址
        temperature: 温度参数
        max_tokens: 最大 token 数
        timeout: 超时时间（保留接口，agentscope 模型内部有重试机制）
        api_key: API Key（可选，未提供时从环境变量读取）

    Returns:
        AgentScopeModelWrapper 实例
    """
    logger.info(f"🔧 [AgentScope 2.0] 创建模型 provider={provider}, model={model}")
    logger.info(f"🔑 [API Key] 来源: {'数据库配置' if _is_valid_api_key(api_key) else '环境变量'}")

    # DashScope 特殊 URL 归一化
    provider_lower = provider.lower()
    if (
        provider_lower in ("dashscope", "alibaba", "阿里百炼")
        or "dashscope" in provider_lower
        or "阿里百炼" in provider
    ):
        backend_url = _normalize_dashscope_base_url(backend_url)
        provider = "dashscope"

    return create_agentscope_model(
        provider=provider,
        model_name=model,
        api_key=api_key,
        base_url=backend_url or None,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )


class TradingAgentsGraph:
    """Main class that orchestrates the trading agents framework."""

    def __init__(
        self,
        selected_analysts=["market", "social", "news", "fundamentals"],
        debug=False,
        config: Dict[str, Any] = None,
    ):
        """Initialize the trading agents graph and components.

        Args:
            selected_analysts: List of analyst types to include
            debug: Whether to run in debug mode
            config: Configuration dictionary. If None, uses default config
        """
        self.debug = debug
        self.selected_analysts = selected_analysts
        self.config = config or DEFAULT_CONFIG
        self.agent_framework = "agentscope"

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # Initialize LLMs using AgentScope 2.0 factory
        quick_config = self.config.get("quick_model_config", {})
        deep_config = self.config.get("deep_model_config", {})

        quick_provider = (
            self.config.get("quick_provider") or self.config.get("llm_provider", "openai")
        )
        deep_provider = (
            self.config.get("deep_provider") or self.config.get("llm_provider", "openai")
        )
        quick_backend_url = self.config.get("quick_backend_url") or self.config.get("backend_url", "")
        deep_backend_url = self.config.get("deep_backend_url") or self.config.get("backend_url", "")

        self.quick_thinking_llm = create_llm_by_provider(
            provider=quick_provider,
            model=self.config["quick_think_llm"],
            backend_url=quick_backend_url,
            temperature=quick_config.get("temperature", 0.7),
            max_tokens=quick_config.get("max_tokens", 4000),
            timeout=quick_config.get("timeout", 180),
            api_key=self.config.get("quick_api_key"),
        )
        self.deep_thinking_llm = create_llm_by_provider(
            provider=deep_provider,
            model=self.config["deep_think_llm"],
            backend_url=deep_backend_url,
            temperature=deep_config.get("temperature", 0.7),
            max_tokens=deep_config.get("max_tokens", 4000),
            timeout=deep_config.get("timeout", 180),
            api_key=self.config.get("deep_api_key"),
        )
        logger.info("✅ [AgentScope 2.0] LLM 实例创建成功")
        logger.info(f"   快速模型: {self.config['quick_think_llm']} ({quick_provider})")
        logger.info(f"   深度模型: {self.config['deep_think_llm']} ({deep_provider})")


        self.toolkit = Toolkit(config=self.config)

        # Initialize memories (如果启用)
        memory_enabled = self.config.get("memory_enabled", True)
        if memory_enabled:
            # 使用单例ChromaDB管理器，避免并发创建冲突
            self.bull_memory = FinancialSituationMemory("bull_memory", self.config)
            self.bear_memory = FinancialSituationMemory("bear_memory", self.config)
            self.trader_memory = FinancialSituationMemory("trader_memory", self.config)
            self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config)
            self.risk_manager_memory = FinancialSituationMemory("risk_manager_memory", self.config)
        else:
            # 创建空的内存对象
            self.bull_memory = None
            self.bear_memory = None
            self.trader_memory = None
            self.invest_judge_memory = None
            self.risk_manager_memory = None

        # Initialize components
        # 🔥 [修复] 从配置中读取辩论轮次参数
        self.conditional_logic = ConditionalLogic(
            max_debate_rounds=self.config.get("max_debate_rounds", 1),
            max_risk_discuss_rounds=self.config.get("max_risk_discuss_rounds", 1),
        )
        logger.info(f"🔧 [ConditionalLogic] 初始化完成:")
        logger.info(f"   - max_debate_rounds: {self.conditional_logic.max_debate_rounds}")
        logger.info(f"   - max_risk_discuss_rounds: {self.conditional_logic.max_risk_discuss_rounds}")

        self.tool_map = self._create_tool_map()
        self.agentscope_runner = AgentScopeRunner(
            quick_llm=self.quick_thinking_llm,
            deep_llm=self.deep_thinking_llm,
            toolkit=self.toolkit,
            bull_memory=self.bull_memory,
            bear_memory=self.bear_memory,
            trader_memory=self.trader_memory,
            invest_judge_memory=self.invest_judge_memory,
            risk_manager_memory=self.risk_manager_memory,
            conditional_logic=self.conditional_logic,
            tool_map=self.tool_map,
        )

        self.propagator = Propagator()
        self.reflector = Reflector(self.quick_thinking_llm)
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # State tracking
        self.curr_state = None
        self.ticker = None
        self.log_states_dict = {}  # date to full state dict

        # AgentScope runner does not require a compiled graph.

    def _create_tool_map(self) -> Dict[str, List[Any]]:
        """Create tool list map for AgentScope runner."""
        return {
            "market": [
                self.toolkit.get_stock_market_data_unified,
                self.toolkit.get_YFin_data_online,
                self.toolkit.get_stockstats_indicators_report_online,
                self.toolkit.get_YFin_data,
                self.toolkit.get_stockstats_indicators_report,
            ],
            "social": [
                self.toolkit.get_stock_sentiment_unified,
                self.toolkit.get_stock_news_openai,
                self.toolkit.get_reddit_stock_info,
            ],
            "news": [
                self.toolkit.get_stock_news_unified,
                self.toolkit.get_global_news_openai,
                self.toolkit.get_google_news,
                self.toolkit.get_finnhub_news,
                self.toolkit.get_reddit_news,
            ],
            "fundamentals": [
                self.toolkit.get_stock_fundamentals_unified,
                self.toolkit.get_finnhub_company_insider_sentiment,
                self.toolkit.get_finnhub_company_insider_transactions,
                self.toolkit.get_simfin_balance_sheet,
                self.toolkit.get_simfin_cashflow,
                self.toolkit.get_simfin_income_stmt,
                self.toolkit.get_china_stock_data,
                self.toolkit.get_china_fundamentals,
            ],
        }

    def propagate(
        self,
        company_name,
        trade_date,
        progress_callback=None,
        task_id=None,
        planner_plan=None,
        focus_hint=None,
        resume_state=None,
        resume_from_node=None,
    ):
        """Run the trading agents graph for a company on a specific date.

        Args:
            company_name: Company name or stock symbol
            trade_date: Date for analysis
            progress_callback: Optional callback function for progress updates
            task_id: Optional task ID for tracking performance data
        """
        return self._propagate_agentscope(
            company_name,
            trade_date,
            progress_callback=progress_callback,
            task_id=task_id,
            planner_plan=planner_plan,
            focus_hint=focus_hint,
            resume_state=resume_state,
            resume_from_node=resume_from_node,
        )

    def _propagate_agentscope(
        self,
        company_name,
        trade_date,
        progress_callback=None,
        task_id=None,
        planner_plan=None,
        focus_hint=None,
        resume_state=None,
        resume_from_node=None,
    ):
        """Run the trading agents flow using AgentScope."""
        logger.debug(f"🔍 [AGENTSCOPE] ===== TradingAgentsGraph._propagate_agentscope 接收参数 =====")
        logger.debug(f"🔍 [AGENTSCOPE] company_name: '{company_name}' (类型: {type(company_name)})")
        logger.debug(f"🔍 [AGENTSCOPE] trade_date: '{trade_date}' (类型: {type(trade_date)})")
        logger.debug(f"🔍 [AGENTSCOPE] task_id: '{task_id}'")

        self.ticker = company_name

        if resume_state:
            init_agent_state = dict(resume_state)
            init_agent_state["session_id"] = task_id or init_agent_state.get("session_id", "")
            init_agent_state["company_of_interest"] = company_name
            init_agent_state["trade_date"] = str(trade_date)
            init_agent_state["planner_plan"] = planner_plan or init_agent_state.get("planner_plan", {})
            init_agent_state["focus_hint"] = focus_hint or init_agent_state.get("focus_hint", "")
            init_agent_state["skill_name"] = self.config.get("skill_name") or init_agent_state.get("skill_name", "")
            init_agent_state["skill_tool_policy"] = self.config.get("skill_tool_policy") or init_agent_state.get("skill_tool_policy", {})
            logger.info(f"🔁 [AGENTSCOPE] 从 checkpoint 恢复执行，resume_from_node={resume_from_node}")
        else:
            init_agent_state = self.propagator.create_initial_state(
                company_name,
                trade_date,
                session_id=task_id,
                planner_plan=planner_plan,
                focus_hint=focus_hint,
                skill_name=self.config.get("skill_name"),
                skill_tool_policy=self.config.get("skill_tool_policy"),
            )

        node_timings = {}
        total_start_time = time.time()

        self._current_task_id = task_id

        def progress_sender(node_name: str):
            if not progress_callback:
                return
            if node_name == "__end__":
                self._send_progress_update({"__end__": True}, progress_callback)
            else:
                self._send_progress_update({node_name: {}}, progress_callback)

        final_state, node_timings = self.agentscope_runner.run(
            init_agent_state,
            selected_analysts=self.selected_analysts,
            progress_sender=progress_sender,
            resume_from_node=resume_from_node,
        )

        total_elapsed = time.time() - total_start_time

        logger.info(f"🔍 [AGENTSCOPE TIMING] 节点计时数量: {len(node_timings)}")
        logger.info(f"🔍 [AGENTSCOPE TIMING] 总耗时: {total_elapsed:.2f}秒")
        logger.info(f"🔍 [AGENTSCOPE TIMING] 节点列表: {list(node_timings.keys())}")

        self._print_timing_summary(node_timings, total_elapsed)
        performance_data = self._build_performance_data(node_timings, total_elapsed)
        final_state["performance_metrics"] = performance_data

        self.curr_state = final_state
        self._log_state(trade_date, final_state)

        model_info = ""
        try:
            if hasattr(self.deep_thinking_llm, "model_name"):
                model_info = f"{self.deep_thinking_llm.__class__.__name__}:{self.deep_thinking_llm.model_name}"
            else:
                model_info = self.deep_thinking_llm.__class__.__name__
        except Exception:
            model_info = "Unknown"

        decision = self.process_signal(final_state["final_trade_decision"], company_name)
        decision["model_info"] = model_info

        return final_state, decision

    def _send_progress_update(self, chunk, progress_callback):
        """发送进度更新到回调函数"""
        try:
            # 从chunk中提取当前执行的节点信息
            if not isinstance(chunk, dict):
                return

            # 获取第一个非特殊键作为节点名
            node_name = None
            for key in chunk.keys():
                if not key.startswith('__'):
                    node_name = key
                    break

            if not node_name:
                return

            logger.info(f"🔍 [Progress] 节点名称: {node_name}")

            # 检查是否为结束节点
            if '__end__' in chunk:
                logger.info(f"📊 [Progress] 检测到__end__节点")
                progress_callback("📊 生成报告")
                return

            # 节点名称映射表
            node_mapping = {
                # 分析师节点
                'Market Analyst': "📊 市场分析师",
                'Fundamentals Analyst': "💼 基本面分析师",
                'News Analyst': "📰 新闻分析师",
                'Social Analyst': "💬 社交媒体分析师",
                # 工具节点（不发送进度更新，避免重复）
                'tools_market': None,
                'tools_fundamentals': None,
                'tools_news': None,
                'tools_social': None,
                # 消息清理节点（不发送进度更新）
                'Msg Clear Market': None,
                'Msg Clear Fundamentals': None,
                'Msg Clear News': None,
                'Msg Clear Social': None,
                # 研究员节点
                'Bull Researcher': "🐂 看涨研究员",
                'Bear Researcher': "🐻 看跌研究员",
                'Research Manager': "👔 研究经理",
                # 交易员节点
                'Trader': "💼 交易员决策",
                # 风险评估节点
                'Risky Analyst': "🔥 激进风险评估",
                'Safe Analyst': "🛡️ 保守风险评估",
                'Neutral Analyst': "⚖️ 中性风险评估",
                'Risk Judge': "🎯 风险经理",
            }

            # 查找映射的消息
            message = node_mapping.get(node_name)

            if message is None:
                # None 表示跳过（工具节点、消息清理节点）
                logger.debug(f"⏭️ [Progress] 跳过节点: {node_name}")
                return

            if message:
                # 发送进度更新
                logger.info(f"📤 [Progress] 发送进度更新: {message}")
                progress_callback(message)
            else:
                # 未知节点，使用节点名称
                logger.warning(f"⚠️ [Progress] 未知节点: {node_name}")
                progress_callback(f"🔍 {node_name}")

        except Exception as e:
            logger.error(f"❌ 进度更新失败: {e}", exc_info=True)

    def _build_performance_data(self, node_timings: Dict[str, float], total_elapsed: float) -> Dict[str, Any]:
        """构建性能数据结构

        Args:
            node_timings: 每个节点的执行时间字典
            total_elapsed: 总执行时间

        Returns:
            性能数据字典
        """
        # 节点分类（注意：风险管理节点要先于分析师节点判断，因为它们也包含'Analyst'）
        analyst_nodes = {}
        tool_nodes = {}
        msg_clear_nodes = {}
        research_nodes = {}
        trader_nodes = {}
        risk_nodes = {}
        other_nodes = {}

        for node_name, elapsed in node_timings.items():
            # 优先匹配风险管理团队（因为它们也包含'Analyst'）
            if 'Risky' in node_name or 'Safe' in node_name or 'Neutral' in node_name or 'Risk Judge' in node_name:
                risk_nodes[node_name] = elapsed
            # 然后匹配分析师团队
            elif 'Analyst' in node_name:
                analyst_nodes[node_name] = elapsed
            # 工具节点
            elif node_name.startswith('tools_'):
                tool_nodes[node_name] = elapsed
            # 消息清理节点
            elif node_name.startswith('Msg Clear'):
                msg_clear_nodes[node_name] = elapsed
            # 研究团队
            elif 'Researcher' in node_name or 'Research Manager' in node_name:
                research_nodes[node_name] = elapsed
            # 交易团队
            elif 'Trader' in node_name:
                trader_nodes[node_name] = elapsed
            # 其他节点
            else:
                other_nodes[node_name] = elapsed

        # 计算统计数据
        slowest_node = max(node_timings.items(), key=lambda x: x[1]) if node_timings else (None, 0)
        fastest_node = min(node_timings.items(), key=lambda x: x[1]) if node_timings else (None, 0)
        avg_time = sum(node_timings.values()) / len(node_timings) if node_timings else 0

        return {
            "total_time": round(total_elapsed, 2),
            "total_time_minutes": round(total_elapsed / 60, 2),
            "node_count": len(node_timings),
            "average_node_time": round(avg_time, 2),
            "slowest_node": {
                "name": slowest_node[0],
                "time": round(slowest_node[1], 2)
            } if slowest_node[0] else None,
            "fastest_node": {
                "name": fastest_node[0],
                "time": round(fastest_node[1], 2)
            } if fastest_node[0] else None,
            "node_timings": {k: round(v, 2) for k, v in node_timings.items()},
            "category_timings": {
                "analyst_team": {
                    "nodes": {k: round(v, 2) for k, v in analyst_nodes.items()},
                    "total": round(sum(analyst_nodes.values()), 2),
                    "percentage": round(sum(analyst_nodes.values()) / total_elapsed * 100, 1) if total_elapsed > 0 else 0
                },
                "tool_calls": {
                    "nodes": {k: round(v, 2) for k, v in tool_nodes.items()},
                    "total": round(sum(tool_nodes.values()), 2),
                    "percentage": round(sum(tool_nodes.values()) / total_elapsed * 100, 1) if total_elapsed > 0 else 0
                },
                "message_clearing": {
                    "nodes": {k: round(v, 2) for k, v in msg_clear_nodes.items()},
                    "total": round(sum(msg_clear_nodes.values()), 2),
                    "percentage": round(sum(msg_clear_nodes.values()) / total_elapsed * 100, 1) if total_elapsed > 0 else 0
                },
                "research_team": {
                    "nodes": {k: round(v, 2) for k, v in research_nodes.items()},
                    "total": round(sum(research_nodes.values()), 2),
                    "percentage": round(sum(research_nodes.values()) / total_elapsed * 100, 1) if total_elapsed > 0 else 0
                },
                "trader_team": {
                    "nodes": {k: round(v, 2) for k, v in trader_nodes.items()},
                    "total": round(sum(trader_nodes.values()), 2),
                    "percentage": round(sum(trader_nodes.values()) / total_elapsed * 100, 1) if total_elapsed > 0 else 0
                },
                "risk_management_team": {
                    "nodes": {k: round(v, 2) for k, v in risk_nodes.items()},
                    "total": round(sum(risk_nodes.values()), 2),
                    "percentage": round(sum(risk_nodes.values()) / total_elapsed * 100, 1) if total_elapsed > 0 else 0
                },
                "other": {
                    "nodes": {k: round(v, 2) for k, v in other_nodes.items()},
                    "total": round(sum(other_nodes.values()), 2),
                    "percentage": round(sum(other_nodes.values()) / total_elapsed * 100, 1) if total_elapsed > 0 else 0
                }
            },
            "llm_config": {
                "provider": self.config.get('llm_provider', 'unknown'),
                "deep_think_model": self.config.get('deep_think_llm', 'unknown'),
                "quick_think_model": self.config.get('quick_think_llm', 'unknown')
            }
        }

    def _print_timing_summary(self, node_timings: Dict[str, float], total_elapsed: float):
        """打印详细的时间统计报告

        Args:
            node_timings: 每个节点的执行时间字典
            total_elapsed: 总执行时间
        """
        logger.info("🔍 [_print_timing_summary] 方法被调用")
        logger.info("🔍 [_print_timing_summary] node_timings 数量: " + str(len(node_timings)))
        logger.info("🔍 [_print_timing_summary] total_elapsed: " + str(total_elapsed))

        logger.info("=" * 80)
        logger.info("⏱️  分析性能统计报告")
        logger.info("=" * 80)

        # 节点分类（注意：风险管理节点要先于分析师节点判断，因为它们也包含'Analyst'）
        analyst_nodes = []
        tool_nodes = []
        msg_clear_nodes = []
        research_nodes = []
        trader_nodes = []
        risk_nodes = []
        other_nodes = []

        for node_name, elapsed in node_timings.items():
            # 优先匹配风险管理团队（因为它们也包含'Analyst'）
            if 'Risky' in node_name or 'Safe' in node_name or 'Neutral' in node_name or 'Risk Judge' in node_name:
                risk_nodes.append((node_name, elapsed))
            # 然后匹配分析师团队
            elif 'Analyst' in node_name:
                analyst_nodes.append((node_name, elapsed))
            # 工具节点
            elif node_name.startswith('tools_'):
                tool_nodes.append((node_name, elapsed))
            # 消息清理节点
            elif node_name.startswith('Msg Clear'):
                msg_clear_nodes.append((node_name, elapsed))
            # 研究团队
            elif 'Researcher' in node_name or 'Research Manager' in node_name:
                research_nodes.append((node_name, elapsed))
            # 交易团队
            elif 'Trader' in node_name:
                trader_nodes.append((node_name, elapsed))
            # 其他节点
            else:
                other_nodes.append((node_name, elapsed))

        # 打印分类统计
        def print_category(title: str, nodes: List[Tuple[str, float]]):
            if not nodes:
                return
            logger.info(f"\n📊 {title}")
            logger.info("-" * 80)
            total_category_time = sum(t for _, t in nodes)
            for node_name, elapsed in sorted(nodes, key=lambda x: x[1], reverse=True):
                percentage = (elapsed / total_elapsed * 100) if total_elapsed > 0 else 0
                logger.info(f"  • {node_name:40s} {elapsed:8.2f}秒  ({percentage:5.1f}%)")
            logger.info(f"  {'小计':40s} {total_category_time:8.2f}秒  ({total_category_time/total_elapsed*100:5.1f}%)")

        print_category("分析师团队", analyst_nodes)
        print_category("工具调用", tool_nodes)
        print_category("消息清理", msg_clear_nodes)
        print_category("研究团队", research_nodes)
        print_category("交易团队", trader_nodes)
        print_category("风险管理团队", risk_nodes)
        print_category("其他节点", other_nodes)

        # 打印总体统计
        logger.info("\n" + "=" * 80)
        logger.info(f"🎯 总执行时间: {total_elapsed:.2f}秒 ({total_elapsed/60:.2f}分钟)")
        logger.info(f"📈 节点总数: {len(node_timings)}")
        if node_timings:
            avg_time = sum(node_timings.values()) / len(node_timings)
            logger.info(f"⏱️  平均节点耗时: {avg_time:.2f}秒")
            slowest_node = max(node_timings.items(), key=lambda x: x[1])
            logger.info(f"🐌 最慢节点: {slowest_node[0]} ({slowest_node[1]:.2f}秒)")
            fastest_node = min(node_timings.items(), key=lambda x: x[1])
            logger.info(f"⚡ 最快节点: {fastest_node[0]} ({fastest_node[1]:.2f}秒)")

        # 打印LLM配置信息
        logger.info(f"\n🤖 LLM配置:")
        logger.info(f"  • 提供商: {self.config.get('llm_provider', 'unknown')}")
        logger.info(f"  • 深度思考模型: {self.config.get('deep_think_llm', 'unknown')}")
        logger.info(f"  • 快速思考模型: {self.config.get('quick_think_llm', 'unknown')}")
        logger.info("=" * 80)

    def _log_state(self, trade_date, final_state):
        """Log the final state to a JSON file."""
        self.log_states_dict[str(trade_date)] = {
            "company_of_interest": final_state["company_of_interest"],
            "trade_date": final_state["trade_date"],
            "planner_plan": final_state.get("planner_plan", {}),
            "focus_hint": final_state.get("focus_hint", ""),
            "market_report": final_state["market_report"],
            "sentiment_report": final_state["sentiment_report"],
            "news_report": final_state["news_report"],
            "fundamentals_report": final_state["fundamentals_report"],
            "investment_debate_state": {
                "bull_history": final_state["investment_debate_state"]["bull_history"],
                "bear_history": final_state["investment_debate_state"]["bear_history"],
                "history": final_state["investment_debate_state"]["history"],
                "current_response": final_state["investment_debate_state"][
                    "current_response"
                ],
                "judge_decision": final_state["investment_debate_state"][
                    "judge_decision"
                ],
            },
            "trader_investment_decision": final_state["trader_investment_plan"],
            "risk_debate_state": {
                "risky_history": final_state["risk_debate_state"]["risky_history"],
                "safe_history": final_state["risk_debate_state"]["safe_history"],
                "neutral_history": final_state["risk_debate_state"]["neutral_history"],
                "history": final_state["risk_debate_state"]["history"],
                "judge_decision": final_state["risk_debate_state"]["judge_decision"],
            },
            "investment_plan": final_state["investment_plan"],
            "final_trade_decision": final_state["final_trade_decision"],
        }

        # Save to file
        directory = Path(f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/")
        directory.mkdir(parents=True, exist_ok=True)

        with open(
            f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/full_states_log.json",
            "w",
        ) as f:
            json.dump(self.log_states_dict, f, indent=4)

    def reflect_and_remember(self, returns_losses):
        """Reflect on decisions and update memory based on returns."""
        self.reflector.reflect_bull_researcher(
            self.curr_state, returns_losses, self.bull_memory
        )
        self.reflector.reflect_bear_researcher(
            self.curr_state, returns_losses, self.bear_memory
        )
        self.reflector.reflect_trader(
            self.curr_state, returns_losses, self.trader_memory
        )
        self.reflector.reflect_invest_judge(
            self.curr_state, returns_losses, self.invest_judge_memory
        )
        self.reflector.reflect_risk_manager(
            self.curr_state, returns_losses, self.risk_manager_memory
        )

    def process_signal(self, full_signal, stock_symbol=None):
        """Process a signal to extract the core decision."""
        return self.signal_processor.process_signal(full_signal, stock_symbol)
