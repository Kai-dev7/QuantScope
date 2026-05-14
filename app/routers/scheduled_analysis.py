"""
股票定时分析计划 API。
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.database import get_mongo_db
from app.core.response import ok
from app.models.analysis import AnalysisParameters, SingleAnalysisRequest
from app.routers.auth_db import get_current_user
from app.services.simple_analysis_service import get_simple_analysis_service
from app.utils.timezone import now_tz

router = APIRouter(prefix="/api/scheduled-analysis", tags=["scheduled-analysis"])


class ScheduledAnalysisCreate(BaseModel):
    stock_code: str = Field(..., min_length=1)
    stock_name: Optional[str] = None
    market_type: str = "A股"
    frequency: str = Field("daily", pattern="^(daily|weekly|monthly)$")
    run_time: str = Field("16:00", pattern="^([01]\\d|2[0-3]):[0-5]\\d$")
    weekdays: List[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])
    research_depth: str = "标准"
    enabled: bool = True
    notes: str = ""


class ScheduledAnalysisUpdate(BaseModel):
    stock_name: Optional[str] = None
    market_type: Optional[str] = None
    frequency: Optional[str] = Field(None, pattern="^(daily|weekly|monthly)$")
    run_time: Optional[str] = Field(None, pattern="^([01]\\d|2[0-3]):[0-5]\\d$")
    weekdays: Optional[List[int]] = None
    research_depth: Optional[str] = None
    enabled: Optional[bool] = None
    notes: Optional[str] = None


def _serialize_plan(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc = dict(doc)
    doc.pop("_id", None)
    for key in ("created_at", "updated_at", "last_run_at"):
        value = doc.get(key)
        if hasattr(value, "isoformat"):
            doc[key] = value.isoformat()
    return doc


@router.get("")
async def list_scheduled_analysis(user: dict = Depends(get_current_user)):
    db = get_mongo_db()
    cursor = db.scheduled_analysis_plans.find({"user_id": user["id"]}).sort("created_at", -1)
    plans = []
    async for doc in cursor:
        plans.append(_serialize_plan(doc))
    return ok(plans, "获取股票定时分析计划成功")


@router.post("")
async def create_scheduled_analysis(
    payload: ScheduledAnalysisCreate,
    user: dict = Depends(get_current_user),
):
    db = get_mongo_db()
    stock_code = payload.stock_code.strip()
    if not stock_code:
        raise HTTPException(status_code=400, detail="股票代码不能为空")

    existing = await db.scheduled_analysis_plans.find_one({
        "user_id": user["id"],
        "stock_code": stock_code,
    })
    if existing:
        raise HTTPException(status_code=400, detail="该股票已存在定时分析计划")

    now = now_tz()
    plan = {
        "plan_id": str(uuid.uuid4()),
        "user_id": user["id"],
        "stock_code": stock_code,
        "stock_name": payload.stock_name or stock_code,
        "market_type": payload.market_type,
        "frequency": payload.frequency,
        "run_time": payload.run_time,
        "weekdays": payload.weekdays,
        "research_depth": payload.research_depth,
        "enabled": payload.enabled,
        "notes": payload.notes,
        "created_at": now,
        "updated_at": now,
        "last_run_at": None,
        "last_task_id": None,
    }
    await db.scheduled_analysis_plans.insert_one(plan)
    return ok(_serialize_plan(plan), "定时分析计划已创建")


@router.put("/{plan_id}")
async def update_scheduled_analysis(
    plan_id: str,
    payload: ScheduledAnalysisUpdate,
    user: dict = Depends(get_current_user),
):
    db = get_mongo_db()
    update = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="没有可更新的字段")
    update["updated_at"] = now_tz()

    result = await db.scheduled_analysis_plans.update_one(
        {"plan_id": plan_id, "user_id": user["id"]},
        {"$set": update},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="定时分析计划不存在")

    doc = await db.scheduled_analysis_plans.find_one({"plan_id": plan_id, "user_id": user["id"]})
    return ok(_serialize_plan(doc), "定时分析计划已更新")


@router.delete("/{plan_id}")
async def delete_scheduled_analysis(
    plan_id: str,
    user: dict = Depends(get_current_user),
):
    db = get_mongo_db()
    result = await db.scheduled_analysis_plans.delete_one({"plan_id": plan_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="定时分析计划不存在")
    return ok({"plan_id": plan_id}, "定时分析计划已删除")


@router.post("/{plan_id}/run")
async def run_scheduled_analysis_now(
    plan_id: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    db = get_mongo_db()
    plan = await db.scheduled_analysis_plans.find_one({"plan_id": plan_id, "user_id": user["id"]})
    if not plan:
        raise HTTPException(status_code=404, detail="定时分析计划不存在")

    request = SingleAnalysisRequest(
        stock_code=plan["stock_code"],
        parameters=AnalysisParameters(
            market_type=plan.get("market_type", "A股"),
            research_depth=plan.get("research_depth", "标准"),
        ),
    )

    service = get_simple_analysis_service()
    result = await service.create_analysis_task(user["id"], request)
    task_id = result["task_id"]

    async def run_analysis_task():
        task_service = get_simple_analysis_service()
        await task_service.execute_analysis_background(task_id, user["id"], request)

    background_tasks.add_task(run_analysis_task)
    await db.scheduled_analysis_plans.update_one(
        {"plan_id": plan_id, "user_id": user["id"]},
        {"$set": {"last_run_at": now_tz(), "last_task_id": task_id, "updated_at": now_tz()}},
    )
    return ok({"task_id": task_id}, "已提交分析任务")
