from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.camel import CamelModel
from ....core.database import get_db
from ....core.response import ResultObject
from ....core.tenancy import current_uid
from ....models.entities import AppBillingOrder, AppPlan
from ....services.billing import (
    BillingError,
    billing_state_for_user,
    create_billing_order,
)
from ..deps import get_current_user

router = APIRouter(prefix="/billing", tags=["billing"])


class CreateBillingOrderReqDTO(CamelModel):
    plan_code: str
    duration_days: int = 30
    payment_method: Optional[str] = "manual"


def _dt(value) -> str:
    return value.isoformat() if value else ""


def _plan_payload(plan: AppPlan) -> dict:
    return {
        "id": int(plan.id),
        "code": plan.code,
        "name": plan.name,
        "maxAccounts": int(plan.max_accounts or 0),
        "aiDailyQuota": int(plan.ai_daily_quota or 0),
        "priceCents": int(plan.price_cents or 0),
        "sortOrder": int(plan.sort_order or 0),
        "status": int(plan.status or 0),
        "description": plan.description or "",
    }


def _order_payload(order: AppBillingOrder) -> dict:
    return {
        "id": int(order.id),
        "orderNo": order.order_no,
        "planCode": order.plan_code,
        "orderType": order.order_type,
        "amountCents": int(order.amount_cents or 0),
        "durationDays": int(order.duration_days or 0),
        "status": order.status,
        "paymentProvider": order.payment_provider or "",
        "paymentMethod": order.payment_method or "",
        "paidTime": _dt(order.paid_time),
        "closedTime": _dt(order.closed_time),
        "expireTime": _dt(order.expire_time),
        "createdTime": _dt(order.created_time),
    }


@router.get("/me", response_model=ResultObject[dict])
async def get_my_billing(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ResultObject.success(await billing_state_for_user(db, current_uid(current_user)))


@router.get("/plans", response_model=ResultObject[list[dict]])
async def list_billing_plans(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(AppPlan)
            .where(AppPlan.status == 1)
            .order_by(AppPlan.sort_order.asc(), AppPlan.id.asc())
        )
    ).scalars().all()
    return ResultObject.success([_plan_payload(row) for row in rows])


@router.get("/orders", response_model=ResultObject[dict])
async def list_my_billing_orders(
    current: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_uid(current_user)
    base = select(AppBillingOrder).where(AppBillingOrder.user_id == uid)
    total = len((await db.execute(base)).scalars().all())
    rows = (
        await db.execute(
            base.order_by(AppBillingOrder.id.desc())
            .offset((current - 1) * size)
            .limit(size)
        )
    ).scalars().all()
    return ResultObject.success({
        "records": [_order_payload(row) for row in rows],
        "total": total,
        "current": current,
        "size": size,
    })


@router.post("/orders", response_model=ResultObject[dict])
async def create_my_billing_order(
    req: CreateBillingOrderReqDTO,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        order = await create_billing_order(
            db,
            user_id=current_uid(current_user),
            plan_code=req.plan_code,
            duration_days=req.duration_days,
            payment_method=req.payment_method or "manual",
        )
        await db.commit()
        await db.refresh(order)
        payload = _order_payload(order)
        payload["message"] = (
            "免费套餐已生效"
            if order.status == "paid" and int(order.amount_cents or 0) == 0
            else "订阅订单已创建，等待支付或管理员确认"
        )
        return ResultObject.success(payload)
    except BillingError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
