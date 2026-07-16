from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.tenancy import current_uid, is_superadmin
from ..models.entities import (
    AdminUser,
    AppBillingOrder,
    AppPlan,
    AppQuotaEvent,
    AppSubscription,
    AppUsageDaily,
    XianyuAccount,
)

METRIC_ACCOUNTS = "accounts"
METRIC_AI_CALLS = "ai_calls"


class BillingError(RuntimeError):
    def __init__(self, message: str, *, code: str = "billing_error") -> None:
        self.code = code
        super().__init__(message)


class BillingLimitError(BillingError):
    pass


@dataclass(frozen=True)
class BillingEntitlement:
    user_id: int
    plan_code: str
    plan_name: str
    max_accounts: int
    ai_daily_quota: int
    price_cents: int
    plan_expire_time: datetime | None
    expired: bool
    source: str


def utcnow() -> datetime:
    return datetime.utcnow()


def _date_today() -> date:
    return utcnow().date()


def _dt(value: datetime | None) -> str:
    return value.isoformat() if value else ""


def _order_no() -> str:
    return "B" + utcnow().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:10].upper()


def _is_expired(user: AdminUser, now: datetime | None = None) -> bool:
    expire_time = user.plan_expire_time
    if not expire_time:
        return False
    return expire_time < (now or utcnow())


async def load_user(db: AsyncSession, user_id: int) -> AdminUser:
    user = (
        await db.execute(select(AdminUser).where(AdminUser.id == int(user_id)))
    ).scalar_one_or_none()
    if not user:
        raise BillingError("用户不存在", code="user_not_found")
    return user


async def load_plan(db: AsyncSession, plan_code: str) -> AppPlan:
    code = str(plan_code or "").strip() or "free"
    plan = (
        await db.execute(select(AppPlan).where(AppPlan.code == code))
    ).scalar_one_or_none()
    if not plan:
        raise BillingError("套餐不存在", code="plan_not_found")
    return plan


async def resolve_entitlement(db: AsyncSession, user: AdminUser) -> BillingEntitlement:
    """Resolve the effective entitlement for a user.

    If a paid plan expires, the account remains usable but falls back to the
    active free plan limits until an admin/payment flow renews it.
    """

    now = utcnow()
    expired = _is_expired(user, now)
    desired_code = "free" if expired and not bool(user.is_super) else (user.plan_code or "free")
    plan = (
        await db.execute(select(AppPlan).where(AppPlan.code == desired_code))
    ).scalar_one_or_none()

    if plan:
        max_accounts = int(plan.max_accounts or 0)
        ai_daily_quota = int(plan.ai_daily_quota or 0)
        plan_name = plan.name
        price_cents = int(plan.price_cents or 0)
        source = "plan"
    else:
        max_accounts = int(user.max_accounts or 0)
        ai_daily_quota = int(user.ai_daily_quota or 0)
        plan_name = desired_code
        price_cents = 0
        source = "user"

    if bool(user.is_super):
        max_accounts = max(max_accounts, 999_999)
        ai_daily_quota = max(ai_daily_quota, 999_999)

    return BillingEntitlement(
        user_id=int(user.id),
        plan_code=desired_code,
        plan_name=plan_name,
        max_accounts=max_accounts,
        ai_daily_quota=ai_daily_quota,
        price_cents=price_cents,
        plan_expire_time=user.plan_expire_time,
        expired=expired,
        source=source,
    )


async def count_user_accounts(db: AsyncSession, user_id: int) -> int:
    return int((
        await db.execute(
            select(func.count()).select_from(XianyuAccount).where(
                XianyuAccount.owner_user_id == int(user_id),
                XianyuAccount.deleted == 0,
            )
        )
    ).scalar() or 0)


async def usage_count_today(db: AsyncSession, user_id: int, metric: str) -> int:
    row = (
        await db.execute(
            select(AppUsageDaily).where(
                AppUsageDaily.user_id == int(user_id),
                AppUsageDaily.usage_date == _date_today(),
                AppUsageDaily.metric == metric,
            )
        )
    ).scalar_one_or_none()
    return int(row.used_count or 0) if row else 0


async def billing_state_for_user(db: AsyncSession, user_id: int) -> dict[str, Any]:
    user = await load_user(db, user_id)
    entitlement = await resolve_entitlement(db, user)
    account_used = await count_user_accounts(db, int(user.id))
    ai_used = await usage_count_today(db, int(user.id), METRIC_AI_CALLS)
    subscription = (
        await db.execute(
            select(AppSubscription)
            .where(AppSubscription.user_id == int(user.id))
            .order_by(AppSubscription.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return {
        "user": {
            "id": int(user.id),
            "username": user.username,
            "email": user.email or "",
            "status": int(user.status or 0),
        },
        "plan": {
            "code": entitlement.plan_code,
            "name": entitlement.plan_name,
            "priceCents": entitlement.price_cents,
            "expireTime": _dt(entitlement.plan_expire_time),
            "expired": entitlement.expired,
            "source": entitlement.source,
        },
        "subscription": {
            "id": int(subscription.id) if subscription else None,
            "status": subscription.status if subscription else "",
            "currentPeriodStart": _dt(subscription.current_period_start) if subscription else "",
            "currentPeriodEnd": _dt(subscription.current_period_end) if subscription else "",
            "cancelAtPeriodEnd": bool(subscription.cancel_at_period_end) if subscription else False,
        },
        "usage": {
            "accounts": {
                "used": account_used,
                "limit": entitlement.max_accounts,
                "remaining": max(entitlement.max_accounts - account_used, 0),
            },
            "aiCallsToday": {
                "used": ai_used,
                "limit": entitlement.ai_daily_quota,
                "remaining": max(entitlement.ai_daily_quota - ai_used, 0),
            },
        },
        "generatedAt": utcnow().isoformat(),
    }


async def ensure_account_quota_available(
    db: AsyncSession,
    current_user: dict | None,
    *,
    restoring_existing: bool = False,
) -> None:
    if is_superadmin(current_user):
        return
    uid = current_uid(current_user)
    if not uid:
        raise BillingLimitError("无法确认当前用户，账号添加已阻止", code="user_unknown")
    user = await load_user(db, uid)
    if int(user.status or 0) != 1:
        raise BillingLimitError("账号已被禁用，不能添加闲鱼账号", code="user_disabled")
    entitlement = await resolve_entitlement(db, user)
    used = await count_user_accounts(db, uid)
    if used >= entitlement.max_accounts:
        action = "恢复" if restoring_existing else "添加"
        raise BillingLimitError(
            f"当前套餐最多绑定 {entitlement.max_accounts} 个闲鱼账号，已绑定 {used} 个，不能继续{action}。请升级套餐或删除不用的账号。",
            code="account_quota_exhausted",
        )


async def record_usage_delta(
    db: AsyncSession,
    *,
    user_id: int,
    metric: str,
    delta: int = 1,
    limit_count: int = 0,
    source_type: str = "",
    source_id: str = "",
    reason: str = "",
) -> None:
    today = _date_today()
    row = (
        await db.execute(
            select(AppUsageDaily).where(
                AppUsageDaily.user_id == int(user_id),
                AppUsageDaily.usage_date == today,
                AppUsageDaily.metric == metric,
            )
        )
    ).scalar_one_or_none()
    if row:
        row.used_count = int(row.used_count or 0) + int(delta)
        row.limit_count = int(limit_count or row.limit_count or 0)
    else:
        db.add(AppUsageDaily(
            user_id=int(user_id),
            usage_date=today,
            metric=metric,
            used_count=max(int(delta), 0),
            limit_count=int(limit_count or 0),
        ))
    db.add(AppQuotaEvent(
        user_id=int(user_id),
        metric=metric,
        delta=int(delta),
        source_type=source_type or None,
        source_id=source_id or None,
        reason=reason or None,
    ))


async def create_billing_order(
    db: AsyncSession,
    *,
    user_id: int,
    plan_code: str,
    duration_days: int = 30,
    order_type: str = "subscription",
    payment_method: str = "manual",
) -> AppBillingOrder:
    plan = await load_plan(db, plan_code)
    if int(plan.status or 0) != 1:
        raise BillingError("套餐已下架，不能购买", code="plan_inactive")
    days = max(int(duration_days or 30), 1)
    month_units = max(1, math.ceil(days / 30))
    amount = int(plan.price_cents or 0) * month_units
    order = AppBillingOrder(
        order_no=_order_no(),
        user_id=int(user_id),
        plan_code=plan.code,
        order_type=order_type,
        amount_cents=amount,
        duration_days=days,
        status="pending",
        payment_provider="internal",
        payment_method=payment_method,
        expire_time=utcnow() + timedelta(minutes=30),
        metadata_json={"monthUnits": month_units},
    )
    db.add(order)
    await db.flush()
    if amount == 0:
        await activate_order(db, order, operator="system")
    return order


async def activate_order(
    db: AsyncSession,
    order: AppBillingOrder,
    *,
    operator: str = "admin",
) -> AppSubscription:
    plan = await load_plan(db, order.plan_code)
    user = await load_user(db, int(order.user_id))
    now = utcnow()
    end_time = None if int(plan.price_cents or 0) <= 0 else now + timedelta(days=int(order.duration_days or 30))

    active_rows = (
        await db.execute(
            select(AppSubscription).where(
                AppSubscription.user_id == int(user.id),
                AppSubscription.status == "active",
            )
        )
    ).scalars().all()
    for row in active_rows:
        row.status = "replaced"

    subscription = AppSubscription(
        user_id=int(user.id),
        plan_code=plan.code,
        status="active",
        current_period_start=now,
        current_period_end=end_time,
        source_order_id=int(order.id),
    )
    db.add(subscription)

    user.plan_code = plan.code
    user.max_accounts = int(plan.max_accounts or 0)
    user.ai_daily_quota = int(plan.ai_daily_quota or 0)
    user.plan_expire_time = end_time

    order.status = "paid"
    order.paid_time = order.paid_time or now
    order.metadata_json = {
        **(order.metadata_json or {}),
        "activatedBy": operator,
        "activatedAt": now.isoformat(),
    }
    await db.flush()
    return subscription
