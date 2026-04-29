from __future__ import annotations

import asyncio
from typing import Any, Dict, Literal, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import TransportSecuritySettings

from app.core.database import get_mongo_db_sync
from app.models.analysis import AnalysisParameters, SingleAnalysisRequest
from app.services.simple_analysis_service import get_simple_analysis_service

_transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*", "host.docker.internal:*", "backend:*", "quantscope-backend:*"],
    allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*", "http://host.docker.internal:*", "http://backend:*", "http://quantscope-backend:*"],
)

server = FastMCP(name="analysis-server", stateless_http=False, transport_security=_transport_security)

MCP_USER_ID = "mcp-system"
MarketType = Literal["A股", "港股", "美股"]
ResearchDepth = Literal["快速", "基础", "标准", "深度", "全面"]
AnalystName = Literal["market", "fundamentals", "news", "social"]


def _safe_string(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _safe_number(value: Any, default: float = 0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _format_report_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    reports = _safe_dict(doc.get("reports"))
    cleaned_reports = {}
    for key, value in reports.items():
        safe_key = _safe_string(key, "unknown_report")
        safe_value = _safe_string(value, "").strip()
        if safe_value:
            cleaned_reports[safe_key] = safe_value

    return {
        "analysis_id": _safe_string(doc.get("analysis_id"), "unknown"),
        "task_id": _safe_string(doc.get("task_id"), ""),
        "stock_symbol": _safe_string(doc.get("stock_symbol"), "UNKNOWN"),
        "stock_name": _safe_string(doc.get("stock_name"), ""),
        "market_type": _safe_string(doc.get("market_type"), ""),
        "analysis_date": _safe_string(doc.get("analysis_date"), ""),
        "summary": _safe_string(doc.get("summary"), "分析摘要暂无"),
        "recommendation": _safe_string(doc.get("recommendation"), "投资建议暂无"),
        "confidence_score": _safe_number(doc.get("confidence_score"), 0.0),
        "risk_level": _safe_string(doc.get("risk_level"), "中等"),
        "key_points": _safe_list(doc.get("key_points")),
        "execution_time": _safe_number(doc.get("execution_time"), 0),
        "tokens_used": _safe_number(doc.get("tokens_used"), 0),
        "analysts": _safe_list(doc.get("analysts")),
        "research_depth": _safe_string(doc.get("research_depth"), "标准"),
        "reports": cleaned_reports,
        "decision": _safe_dict(doc.get("decision")),
        "planner_plan": _safe_dict(doc.get("planner_plan")),
        "focus_hint": _safe_string(doc.get("focus_hint"), ""),
        "status": _safe_string(doc.get("status"), "completed"),
        "model_info": _safe_string(doc.get("model_info"), ""),
        "created_at": _safe_string(doc.get("created_at"), ""),
        "updated_at": _safe_string(doc.get("updated_at"), ""),
    }


def _find_report_document(
    *,
    task_id: str = "",
    analysis_id: str = "",
    stock_symbol: str = "",
) -> Optional[Dict[str, Any]]:
    db = get_mongo_db_sync()

    if task_id:
        doc = db.analysis_reports.find_one({"task_id": task_id}, {"_id": 0})
        if doc:
            return doc

        tasks_doc = db.analysis_tasks.find_one({"task_id": task_id}, {"result.analysis_id": 1})
        fallback_analysis_id = ((tasks_doc or {}).get("result") or {}).get("analysis_id")
        if fallback_analysis_id:
            doc = db.analysis_reports.find_one({"analysis_id": fallback_analysis_id}, {"_id": 0})
            if doc:
                return doc

    if analysis_id:
        doc = db.analysis_reports.find_one({"analysis_id": analysis_id}, {"_id": 0})
        if doc:
            return doc

    if stock_symbol:
        return db.analysis_reports.find_one(
            {"stock_symbol": stock_symbol},
            {"_id": 0},
            sort=[("created_at", -1)],
        )

    return None


@server.tool(name="submit_single_analysis")
async def submit_single_analysis(
    symbol: str,
    market_type: MarketType = "A股",
    research_depth: ResearchDepth = "标准",
    selected_analysts: Optional[list[AnalystName]] = None,
    custom_prompt: Optional[str] = None,
    planner_enabled: bool = True,
    include_sentiment: bool = True,
    include_risk: bool = True,
    language: str = "zh-CN",
    quick_analysis_model: Optional[str] = "qwen-turbo",
    deep_analysis_model: Optional[str] = "qwen-max",
) -> dict:
    """
    Submit a long-running single-stock analysis task and return immediately.

    Use this tool when the user wants a fresh analysis for one stock.
    This tool does not wait for the final report. It creates a background
    task and returns a `task_id`.

    Recommended workflow:
    1. Call `submit_single_analysis` once.
    2. Store the returned `task_id`.
    3. Later call `get_final_report(task_id=...)` to retrieve the final report.

    Important behavior:
    - This is a long-running task and may take several minutes.
    - Do not expect the final report in this response.
    - Prefer `task_id` as the follow-up lookup key.

    Parameters:
    - symbol: Stock ticker or code, for example `AAPL`, `TSLA`, `600519`, `00700`.
    - market_type: One of `A股`, `港股`, `美股`.
    - research_depth: One of `快速`, `基础`, `标准`, `深度`, `全面`.
    - selected_analysts: Optional analyst modules. Allowed values are
      `market`, `fundamentals`, `news`, `social`.
    - custom_prompt: Optional user goal or focus request for this analysis.
    - planner_enabled: If true, QuantScope may refine analyst selection,
      research depth, and focus hints before execution.
    - include_sentiment: Keep sentiment-related analysis enabled.
    - include_risk: Keep risk-analysis stages enabled.
    - language: Preferred output language. Current default is `zh-CN`.
    - quick_analysis_model: Optional fast model name.
    - deep_analysis_model: Optional deep-reasoning model name.
    """
    service = get_simple_analysis_service()
    request = SingleAnalysisRequest(
        symbol=symbol,
        parameters=AnalysisParameters(
            market_type=market_type,
            research_depth=research_depth,
            selected_analysts=selected_analysts or ["market", "fundamentals", "news", "social"],
            custom_prompt=custom_prompt,
            planner_enabled=planner_enabled,
            include_sentiment=include_sentiment,
            include_risk=include_risk,
            language=language,
            quick_analysis_model=quick_analysis_model,
            deep_analysis_model=deep_analysis_model,
        ),
    )

    result = await service.create_analysis_task(MCP_USER_ID, request)
    task_id = _safe_string(result.get("task_id"))

    async def _run() -> None:
        await service.execute_analysis_background(task_id, MCP_USER_ID, request)

    asyncio.create_task(_run())

    return {
        "success": True,
        "task_id": task_id,
        "status": _safe_string(result.get("status"), "pending"),
        "message": _safe_string(result.get("message"), "分析任务已提交"),
        "planner_plan": result.get("planner_plan"),
        "query_hint": "Use get_final_report with task_id after the analysis completes.",
    }


@server.tool(name="get_final_report")
def get_final_report(
    task_id: str = "",
    analysis_id: str = "",
    stock_symbol: str = "",
) -> dict:
    """
    Retrieve the final completed report for a previously submitted analysis task.

    Use this tool after `submit_single_analysis`.

    Lookup priority:
    1. Prefer `task_id` when available. This is the most precise lookup key.
    2. Use `analysis_id` if you already have the persisted report id.
    3. Use `stock_symbol` only when you want the latest known report for a stock.

    Important behavior:
    - If the analysis is still running or no report exists yet, this tool returns
      `success=false` and `found=false`.
    - `stock_symbol` may return the latest existing report, which is less precise
      than `task_id`.

    Parameters:
    - task_id: Preferred lookup key from `submit_single_analysis`.
    - analysis_id: Optional persisted report id.
    - stock_symbol: Optional stock symbol used to fetch the latest available report.
    """
    doc = _find_report_document(
        task_id=_safe_string(task_id).strip(),
        analysis_id=_safe_string(analysis_id).strip(),
        stock_symbol=_safe_string(stock_symbol).strip(),
    )
    if not doc:
        return {
            "success": False,
            "found": False,
            "message": "Final report is not ready or does not exist.",
        }

    return {
        "success": True,
        "found": True,
        "report": _format_report_document(doc),
    }
