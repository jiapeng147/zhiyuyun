from __future__ import annotations

from datetime import datetime
import logging
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
    close_billing_order,
    create_billing_order,
    list_quota_events,
    list_usage_daily,
    load_payment_config,
    plan_payload,
    reconcile_billing_lifecycle,
)
from ..deps import get_current_user

router = APIRouter(prefix="/billing", tags=["billing"])
logger = logging.getLogger(__name__)


class CreateBillingOrderReqDTO(CamelModel):
    plan_code: str
    duration_days: int = 30
    payment_method: Optional[str] = "manual"
    coupon_code: Optional[str] = ""


class CloseBillingOrderReqDTO(CamelModel):
    reason: Optional[str] = "user_cancel"


class SubmitPaymentProofReqDTO(CamelModel):
    paid_amount_cents: Optional[int] = None
    paid_at: Optional[str] = ""
    channel: Optional[str] = ""
    payer_name: Optional[str] = ""
    transaction_no: Optional[str] = ""
    proof_url: Optional[str] = ""
    remark: Optional[str] = ""


class PreviewCouponReqDTO(CamelModel):
    plan_code: str
    duration_days: int = 30
    coupon_code: str


def _dt(value) -> str:
    return value.isoformat() if value else ""


def _clean_text(value: object, limit: int = 500) -> str:
    return str(value or "").strip()[:limit]


def _parse_paid_at(value: str | None) -> str:
    raw = _clean_text(value, 64)
    if not raw:
        return ""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None).isoformat()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="付款时间格式无效") from exc


def _order_payload(order: AppBillingOrder) -> dict:
    meta = order.metadata_json if isinstance(order.metadata_json, dict) else {}
    proof = meta.get("paymentProof") if isinstance(meta.get("paymentProof"), dict) else None
    refund_amount = meta.get("refundAmountCents")
    return {
        "id": int(order.id),
        "orderNo": order.order_no,
        "planCode": order.plan_code,
        "orderType": order.order_type,
        "listAmountCents": int(meta.get("listAmountCents") or order.amount_cents or 0),
        "discountCents": int(meta.get("discountCents") or 0),
        "couponCode": str(meta.get("couponCode") or ""),
        "couponName": str(meta.get("couponName") or ""),
        "refundAmountCents": int(refund_amount if refund_amount is not None else 0),
        "refundReason": str(meta.get("refundReason") or ""),
        "refundedAt": str(meta.get("refundedAt") or ""),
        "amountCents": int(order.amount_cents or 0),
        "durationDays": int(order.duration_days or 0),
        "status": order.status,
        "paymentProvider": order.payment_provider or "",
        "paymentMethod": order.payment_method or "",
        "paymentProof": proof,
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


@router.get("/payment-config", response_model=ResultObject[dict])
async def get_payment_config(db: AsyncSession = Depends(get_db)):
    return ResultObject.success(await load_payment_config(db))


@router.get("/plans", response_model=ResultObject[list[dict]])
async def list_billing_plans(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(AppPlan)
            .where(AppPlan.status == 1)
            .order_by(AppPlan.sort_order.asc(), AppPlan.id.asc())
        )
    ).scalars().all()
    return ResultObject.success([plan_payload(row) for row in rows])


@router.post("/coupons/preview", response_model=ResultObject[dict])
async def preview_coupon(
    req: PreviewCouponReqDTO,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        from ....services.billing import preview_billing_coupon

        return ResultObject.success(await preview_billing_coupon(
            db,
            user_id=current_uid(current_user),
            plan_code=req.plan_code,
            duration_days=req.duration_days,
            coupon_code=req.coupon_code,
        ))
    except BillingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/usage-daily", response_model=ResultObject[dict])
async def list_my_usage_daily(
    metric: Optional[str] = Query(default=None),
    current: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ResultObject.success(await list_usage_daily(
        db,
        user_id=current_uid(current_user),
        metric=metric,
        current=current,
        size=size,
    ))


@router.get("/quota-events", response_model=ResultObject[dict])
async def list_my_quota_events(
    metric: Optional[str] = Query(default=None),
    current: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ResultObject.success(await list_quota_events(
        db,
        user_id=current_uid(current_user),
        metric=metric,
        current=current,
        size=size,
    ))


@router.get("/orders", response_model=ResultObject[dict])
async def list_my_billing_orders(
    current: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_uid(current_user)
    reconciled = await reconcile_billing_lifecycle(db, user_id=uid)
    if reconciled["closedOrders"] or reconciled["expiredSubscriptions"] or reconciled.get("expiringReminders"):
        await db.commit()
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
        payment_config = await load_payment_config(db)
        order = await create_billing_order(
            db,
            user_id=current_uid(current_user),
            plan_code=req.plan_code,
            duration_days=req.duration_days,
            payment_method=req.payment_method or "manual",
            expire_minutes=int(payment_config.get("orderExpireMinutes") or 1440),
            coupon_code=req.coupon_code or "",
        )
        await db.commit()
        await db.refresh(order)
        payload = _order_payload(order)
        if order.status == "pending":
            payload["paymentConfig"] = payment_config
        payload["message"] = (
            "免费套餐已生效"
            if order.status == "paid" and int(order.amount_cents or 0) == 0
            else "订阅订单已创建，等待支付或管理员确认"
        )
        return ResultObject.success(payload)
    except BillingError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/orders/{order_id}/payment-proof", response_model=ResultObject[dict])
async def submit_payment_proof(
    order_id: int,
    req: SubmitPaymentProofReqDTO,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_uid(current_user)
    order = (
        await db.execute(
            select(AppBillingOrder).where(
                AppBillingOrder.id == order_id,
                AppBillingOrder.user_id == uid,
            )
        )
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="只有待确认订单可以提交付款凭证")
    amount = int(req.paid_amount_cents or order.amount_cents or 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="付款金额必须大于 0")
    now = datetime.utcnow().isoformat()
    meta = order.metadata_json if isinstance(order.metadata_json, dict) else {}
    proof = {
        "status": "submitted",
        "paidAmountCents": amount,
        "paidAt": _parse_paid_at(req.paid_at),
        "channel": _clean_text(req.channel, 80),
        "payerName": _clean_text(req.payer_name, 120),
        "transactionNo": _clean_text(req.transaction_no, 160),
        "proofUrl": _clean_text(req.proof_url, 1000),
        "remark": _clean_text(req.remark, 1000),
        "submittedAt": now,
        "updatedAt": now,
    }
    order.metadata_json = {**meta, "paymentProof": proof}
    await db.flush()
    try:
        from ....services.billing_notifications import notify_billing_payment_proof_submitted

        await notify_billing_payment_proof_submitted(db, order, proof=proof)
    except Exception:
        logger.warning("payment proof notification failed", exc_info=True)
    await db.commit()
    await db.refresh(order)
    return ResultObject.success(_order_payload(order), message="付款凭证已提交，等待管理员核对")


@router.post("/orders/{order_id}/close", response_model=ResultObject[dict])
async def close_my_billing_order(
    order_id: int,
    req: CloseBillingOrderReqDTO,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_uid(current_user)
    order = (
        await db.execute(
            select(AppBillingOrder).where(
                AppBillingOrder.id == order_id,
                AppBillingOrder.user_id == uid,
            )
        )
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    try:
        await close_billing_order(db, order, operator=f"user:{uid}", reason=req.reason or "user_cancel")
        await db.commit()
        await db.refresh(order)
        return ResultObject.success(_order_payload(order), message="订单已关闭")
    except BillingError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
