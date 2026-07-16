from __future__ import annotations

import math
import json
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
    XianyuSysSetting,
)

METRIC_ACCOUNTS = "accounts"
METRIC_AI_CALLS = "ai_calls"
BILLING_PAYMENT_CONFIG_KEY = "billing_payment_config"

FEATURE_CATALOG: tuple[dict[str, str], ...] = (
    {"key": "accounts", "label": "闲鱼账号"},
    {"key": "products", "label": "商品管理"},
    {"key": "messages", "label": "在线消息"},
    {"key": "ai_customer_service", "label": "AI 客服"},
    {"key": "auto_reply", "label": "自动回复"},
    {"key": "auto_delivery", "label": "自动发货"},
    {"key": "card_warehouse", "label": "卡密仓库"},
    {"key": "source_library", "label": "货源库"},
    {"key": "rag", "label": "RAG 知识库"},
    {"key": "scheduled_tasks", "label": "定时任务"},
    {"key": "item_polish", "label": "商品擦亮"},
    {"key": "notifications", "label": "通知设置"},
)
DEFAULT_FEATURE_FLAGS: dict[str, bool] = {item["key"]: True for item in FEATURE_CATALOG}

DEFAULT_PAYMENT_CONFIG: dict[str, Any] = {
    "enabled": False,
    "orderExpireMinutes": 1440,
    "paymentMethods": ["manual_transfer"],
    "instructions": "请联系管理员确认付款方式。付款完成后，管理员会在后台确认订单并开通套餐。",
    "contact": "",
    "alipayQrUrl": "",
    "wechatQrUrl": "",
    "bankAccount": "",
}


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
    features: dict[str, bool]


def utcnow() -> datetime:
    return datetime.utcnow()


def _date_today() -> date:
    return utcnow().date()


def _dt(value: datetime | None) -> str:
    return value.isoformat() if value else ""


def _order_no() -> str:
    return "B" + utcnow().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:10].upper()


def normalize_feature_flags(raw: Any = None) -> dict[str, bool]:
    result = dict(DEFAULT_FEATURE_FLAGS)
    if isinstance(raw, dict):
        for key in result:
            if key in raw:
                result[key] = bool(raw.get(key))
    return result


def feature_items(flags: dict[str, bool] | None = None) -> list[dict[str, Any]]:
    normalized = normalize_feature_flags(flags)
    return [
        {"key": item["key"], "label": item["label"], "enabled": bool(normalized.get(item["key"], True))}
        for item in FEATURE_CATALOG
    ]


def plan_payload(plan: AppPlan) -> dict[str, Any]:
    flags = normalize_feature_flags(plan.feature_flags)
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
        "features": flags,
        "featureItems": feature_items(flags),
    }


def _clean_int(value: Any, default: int = 0, minimum: int | None = None, maximum: int | None = None) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        result = default
    if minimum is not None:
        result = max(result, minimum)
    if maximum is not None:
        result = min(result, maximum)
    return result


def normalize_payment_config(raw: dict[str, Any] | None = None) -> dict[str, Any]:
    data = {**DEFAULT_PAYMENT_CONFIG, **(raw or {})}
    methods = data.get("paymentMethods", data.get("payment_methods"))
    if not isinstance(methods, list):
        methods = DEFAULT_PAYMENT_CONFIG["paymentMethods"]
    return {
        "enabled": bool(data.get("enabled")),
        "orderExpireMinutes": _clean_int(
            data.get("orderExpireMinutes", data.get("order_expire_minutes")),
            1440,
            5,
            30 * 24 * 60,
        ),
        "paymentMethods": [str(item).strip() for item in methods if str(item or "").strip()][:8],
        "instructions": str(data.get("instructions") or "").strip()[:5000],
        "contact": str(data.get("contact") or "").strip()[:500],
        "alipayQrUrl": str(data.get("alipayQrUrl", data.get("alipay_qr_url")) or "").strip()[:1000],
        "wechatQrUrl": str(data.get("wechatQrUrl", data.get("wechat_qr_url")) or "").strip()[:1000],
        "bankAccount": str(data.get("bankAccount", data.get("bank_account")) or "").strip()[:1000],
    }


async def load_payment_config(db: AsyncSession) -> dict[str, Any]:
    row = (
        await db.execute(
            select(XianyuSysSetting).where(XianyuSysSetting.setting_key == BILLING_PAYMENT_CONFIG_KEY)
        )
    ).scalar_one_or_none()
    if not row or not row.setting_value:
        return normalize_payment_config()
    try:
        parsed = json.loads(row.setting_value)
    except (TypeError, json.JSONDecodeError):
        parsed = {}
    return normalize_payment_config(parsed if isinstance(parsed, dict) else {})


async def save_payment_config(db: AsyncSession, payload: dict[str, Any]) -> dict[str, Any]:
    config = normalize_payment_config(payload)
    raw = json.dumps(config, ensure_ascii=False)
    row = (
        await db.execute(
            select(XianyuSysSetting).where(XianyuSysSetting.setting_key == BILLING_PAYMENT_CONFIG_KEY)
        )
    ).scalar_one_or_none()
    if row:
        row.setting_value = raw
    else:
        db.add(XianyuSysSetting(setting_key=BILLING_PAYMENT_CONFIG_KEY, setting_value=raw))
    await db.commit()
    return config


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
        features = normalize_feature_flags(plan.feature_flags)
    else:
        max_accounts = int(user.max_accounts or 0)
        ai_daily_quota = int(user.ai_daily_quota or 0)
        plan_name = desired_code
        price_cents = 0
        source = "user"
        features = normalize_feature_flags()

    if bool(user.is_super):
        max_accounts = max(max_accounts, 999_999)
        ai_daily_quota = max(ai_daily_quota, 999_999)
        features = normalize_feature_flags()

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
        features=features,
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
    reconciled = await reconcile_billing_lifecycle(db, user_id=user_id)
    if reconciled["closedOrders"] or reconciled["expiredSubscriptions"]:
        await db.commit()
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
            "features": entitlement.features,
            "featureItems": feature_items(entitlement.features),
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


async def ensure_feature_available(
    db: AsyncSession,
    current_user: dict | None,
    feature_key: str,
) -> None:
    if is_superadmin(current_user):
        return
    uid = current_uid(current_user)
    if not uid:
        raise BillingLimitError("无法确认当前用户，功能访问已阻止", code="user_unknown")
    user = await load_user(db, uid)
    if int(user.status or 0) != 1:
        raise BillingLimitError("账号已被禁用，不能使用该功能", code="user_disabled")
    entitlement = await resolve_entitlement(db, user)
    if entitlement.features.get(feature_key, True) is False:
        label = next((item["label"] for item in FEATURE_CATALOG if item["key"] == feature_key), feature_key)
        raise BillingLimitError(
            f"当前套餐未包含「{label}」功能，请升级套餐或联系管理员开通。",
            code="feature_not_in_plan",
        )


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
    expire_minutes: int = 1440,
) -> AppBillingOrder:
    plan = await load_plan(db, plan_code)
    if int(plan.status or 0) != 1:
        raise BillingError("套餐已下架，不能购买", code="plan_inactive")
    days = _clean_int(duration_days, 30, 1, 3650)
    month_units = max(1, math.ceil(days / 30))
    amount = int(plan.price_cents or 0) * month_units
    expires_in = _clean_int(expire_minutes, 1440, 5, 30 * 24 * 60)
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
        expire_time=utcnow() + timedelta(minutes=expires_in),
        metadata_json={"monthUnits": month_units, "expireMinutes": expires_in},
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
    is_paid_plan = int(plan.price_cents or 0) > 0
    current_expire = user.plan_expire_time if user.plan_code == plan.code else None
    period_start = current_expire if is_paid_plan and current_expire and current_expire > now else now
    end_time = None if not is_paid_plan else period_start + timedelta(days=int(order.duration_days or 30))

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
        current_period_start=period_start,
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


async def close_billing_order(
    db: AsyncSession,
    order: AppBillingOrder,
    *,
    operator: str,
    reason: str = "",
) -> AppBillingOrder:
    if order.status != "pending":
        raise BillingError("只有待确认订单可以关闭", code="order_not_pending")
    now = utcnow()
    order.status = "closed"
    order.closed_time = now
    order.metadata_json = {
        **(order.metadata_json or {}),
        "closedBy": operator,
        "closedReason": reason or "manual",
        "closedAt": now.isoformat(),
    }
    await db.flush()
    return order


async def reconcile_billing_lifecycle(db: AsyncSession, user_id: int | None = None) -> dict[str, int]:
    now = utcnow()
    closed_orders = 0
    expired_subscriptions = 0

    order_query = select(AppBillingOrder).where(
        AppBillingOrder.status == "pending",
        AppBillingOrder.expire_time.is_not(None),
        AppBillingOrder.expire_time < now,
    )
    if user_id:
        order_query = order_query.where(AppBillingOrder.user_id == int(user_id))
    orders = (await db.execute(order_query)).scalars().all()
    for order in orders:
        order.status = "closed"
        order.closed_time = now
        order.metadata_json = {
            **(order.metadata_json or {}),
            "closedBy": "system",
            "closedReason": "expired",
            "closedAt": now.isoformat(),
        }
        closed_orders += 1

    sub_query = select(AppSubscription).where(
        AppSubscription.status == "active",
        AppSubscription.current_period_end.is_not(None),
        AppSubscription.current_period_end < now,
    )
    if user_id:
        sub_query = sub_query.where(AppSubscription.user_id == int(user_id))
    subs = (await db.execute(sub_query)).scalars().all()
    for sub in subs:
        sub.status = "expired"
        expired_subscriptions += 1

    if closed_orders or expired_subscriptions:
        await db.flush()
    return {"closedOrders": closed_orders, "expiredSubscriptions": expired_subscriptions}


async def billing_overview(db: AsyncSession) -> dict[str, Any]:
    reconciled = await reconcile_billing_lifecycle(db)
    if reconciled["closedOrders"] or reconciled["expiredSubscriptions"]:
        await db.commit()
    now = utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    paid_filter = AppBillingOrder.status == "paid"
    paid_amount = int((
        await db.execute(select(func.coalesce(func.sum(AppBillingOrder.amount_cents), 0)).where(paid_filter))
    ).scalar() or 0)
    paid_today = int((
        await db.execute(
            select(func.coalesce(func.sum(AppBillingOrder.amount_cents), 0)).where(
                paid_filter,
                AppBillingOrder.paid_time.is_not(None),
                AppBillingOrder.paid_time >= today,
            )
        )
    ).scalar() or 0)
    pending_amount = int((
        await db.execute(
            select(func.coalesce(func.sum(AppBillingOrder.amount_cents), 0)).where(
                AppBillingOrder.status == "pending"
            )
        )
    ).scalar() or 0)
    pending_count = int((
        await db.execute(
            select(func.count()).select_from(AppBillingOrder).where(AppBillingOrder.status == "pending")
        )
    ).scalar() or 0)
    active_subscriptions = int((
        await db.execute(
            select(func.count()).select_from(AppSubscription).where(AppSubscription.status == "active")
        )
    ).scalar() or 0)
    order_status_rows = (
        await db.execute(select(AppBillingOrder.status, func.count()).group_by(AppBillingOrder.status))
    ).all()
    return {
        "paidAmountCents": paid_amount,
        "paidTodayCents": paid_today,
        "pendingAmountCents": pending_amount,
        "pendingOrderCount": pending_count,
        "activeSubscriptionCount": active_subscriptions,
        "orderStatus": [{"status": row[0] or "", "count": int(row[1] or 0)} for row in order_status_rows],
        "generatedAt": now.isoformat(),
    }
