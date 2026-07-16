from __future__ import annotations

import logging
import math
from datetime import date
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import async_session
from ..models.entities import AdminUser, AppBillingOrder, AppPlan, AppSubscription
from .billing import METRIC_ACCOUNTS, METRIC_AI_CALLS, metric_label
from .notify_dispatcher import dispatch_notification_detailed

logger = logging.getLogger(__name__)

EVENT_BILLING_ORDER_PENDING = "账单待支付"
EVENT_BILLING_ORDER_PAID = "账单支付确认"
EVENT_BILLING_ORDER_CLOSED = "账单订单关闭"
EVENT_SUBSCRIPTION_EXPIRING = "套餐到期提醒"
EVENT_SUBSCRIPTION_EXPIRED = "套餐已到期"
EVENT_AI_QUOTA_WARNING = "AI 额度预警"
EVENT_ACCOUNT_QUOTA_WARNING = "账号配额预警"
EVENT_FEATURE_BLOCKED = "套餐权益提醒"


def _money(cents: int | None) -> str:
    return f"¥{(int(cents or 0) / 100):.2f}"


def _dt(value: Any) -> str:
    try:
        return value.isoformat(sep=" ", timespec="seconds") if value else "长期有效"
    except TypeError:
        return str(value or "长期有效")


def _safe_reference_type(value: str) -> str:
    return str(value or "billing")[:100]


async def _load_user(db: AsyncSession, user_id: int) -> AdminUser | None:
    return (
        await db.execute(select(AdminUser).where(AdminUser.id == int(user_id)))
    ).scalar_one_or_none()


async def _load_plan(db: AsyncSession, plan_code: str) -> AppPlan | None:
    return (
        await db.execute(select(AppPlan).where(AppPlan.code == str(plan_code or "")))
    ).scalar_one_or_none()


async def _insert_in_app_once(
    db: AsyncSession,
    *,
    event: str,
    title: str,
    content: str,
    reference_type: str,
    reference_id: int,
    priority: int = 2,
) -> bool:
    ref_type = _safe_reference_type(reference_type)
    ref_id = int(reference_id or 0)
    exists = int((
        await db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM notification
                WHERE deleted = 0
                  AND reference_type = :reference_type
                  AND reference_id = :reference_id
                """
            ),
            {"reference_type": ref_type, "reference_id": ref_id},
        )
    ).scalar() or 0)
    if exists:
        return False
    await db.execute(
        text(
            """
            INSERT INTO notification (
                notification_type, title, content, reference_type, reference_id,
                is_read, priority, deleted, created_time, updated_time
            ) VALUES (
                :event, :title, :content, :reference_type, :reference_id,
                0, :priority, 0, NOW(), NOW()
            )
            """
        ),
        {
            "event": event[:50],
            "title": title[:300],
            "content": content,
            "reference_type": ref_type,
            "reference_id": ref_id,
            "priority": int(priority or 0),
        },
    )
    await db.flush()
    return True


async def _dispatch(event: str, title: str, content: str, context: dict[str, Any]) -> None:
    try:
        await dispatch_notification_detailed(
            event_display_name=event,
            title=title,
            content=content,
            template_context=context,
        )
    except Exception:
        logger.warning("billing notification dispatch failed event=%s", event, exc_info=True)


async def _notify_once(
    db: AsyncSession,
    *,
    event: str,
    title: str,
    content: str,
    reference_type: str,
    reference_id: int,
    priority: int = 2,
    context: dict[str, Any] | None = None,
) -> bool:
    inserted = await _insert_in_app_once(
        db,
        event=event,
        title=title,
        content=content,
        reference_type=reference_type,
        reference_id=reference_id,
        priority=priority,
    )
    if inserted:
        await _dispatch(event, title, content, context or {})
    return inserted


async def notify_billing_order_pending(
    db: AsyncSession,
    order: AppBillingOrder,
    *,
    user: AdminUser | None = None,
    plan: AppPlan | None = None,
) -> None:
    user = user or await _load_user(db, int(order.user_id))
    plan = plan or await _load_plan(db, order.plan_code)
    username = user.username if user else f"#{order.user_id}"
    title = "账单待支付提醒"
    content = (
        f"用户：{username}\n"
        f"订单号：{order.order_no}\n"
        f"套餐：{plan.name if plan else order.plan_code}\n"
        f"金额：{_money(order.amount_cents)}\n"
        f"有效期至：{_dt(order.expire_time)}\n"
        "请按账单页支付说明完成付款，管理员确认后套餐生效。"
    )
    await _notify_once(
        db,
        event=EVENT_BILLING_ORDER_PENDING,
        title=title,
        content=content,
        reference_type="billing_order_pending",
        reference_id=int(order.id),
        priority=2,
        context={"account": username, "orderNo": order.order_no, "plan": order.plan_code},
    )


async def notify_billing_order_paid(
    db: AsyncSession,
    order: AppBillingOrder,
    subscription: AppSubscription | None = None,
    *,
    user: AdminUser | None = None,
    plan: AppPlan | None = None,
) -> None:
    user = user or await _load_user(db, int(order.user_id))
    plan = plan or await _load_plan(db, order.plan_code)
    username = user.username if user else f"#{order.user_id}"
    title = "套餐已开通"
    content = (
        f"用户：{username}\n"
        f"订单号：{order.order_no}\n"
        f"套餐：{plan.name if plan else order.plan_code}\n"
        f"金额：{_money(order.amount_cents)}\n"
        f"到期时间：{_dt(subscription.current_period_end if subscription else order.expire_time)}\n"
        "订单已确认，套餐权益已生效。"
    )
    await _notify_once(
        db,
        event=EVENT_BILLING_ORDER_PAID,
        title=title,
        content=content,
        reference_type="billing_order_paid",
        reference_id=int(order.id),
        priority=2,
        context={"account": username, "orderNo": order.order_no, "plan": order.plan_code},
    )


async def notify_billing_order_closed(
    db: AsyncSession,
    order: AppBillingOrder,
    *,
    reason: str = "",
) -> None:
    user = await _load_user(db, int(order.user_id))
    username = user.username if user else f"#{order.user_id}"
    title = "账单订单已关闭"
    content = (
        f"用户：{username}\n"
        f"订单号：{order.order_no}\n"
        f"套餐：{order.plan_code}\n"
        f"原因：{reason or '订单已关闭'}\n"
        f"关闭时间：{_dt(order.closed_time)}"
    )
    await _notify_once(
        db,
        event=EVENT_BILLING_ORDER_CLOSED,
        title=title,
        content=content,
        reference_type="billing_order_closed",
        reference_id=int(order.id),
        priority=1,
        context={"account": username, "orderNo": order.order_no, "plan": order.plan_code},
    )


async def notify_subscription_expiring(
    db: AsyncSession,
    sub: AppSubscription,
    *,
    days_left: int,
) -> bool:
    user = await _load_user(db, int(sub.user_id))
    username = user.username if user else f"#{sub.user_id}"
    title = f"套餐将在 {days_left} 天内到期"
    content = (
        f"用户：{username}\n"
        f"套餐：{sub.plan_code}\n"
        f"到期时间：{_dt(sub.current_period_end)}\n"
        "请及时续费或联系管理员开通新周期，避免到期后权益降级。"
    )
    return await _notify_once(
        db,
        event=EVENT_SUBSCRIPTION_EXPIRING,
        title=title,
        content=content,
        reference_type=f"subscription_expiring_{int(days_left)}d",
        reference_id=int(sub.id),
        priority=2,
        context={"account": username, "plan": sub.plan_code, "daysLeft": days_left},
    )


async def notify_subscription_expired(db: AsyncSession, sub: AppSubscription) -> None:
    user = await _load_user(db, int(sub.user_id))
    username = user.username if user else f"#{sub.user_id}"
    title = "套餐已到期"
    content = (
        f"用户：{username}\n"
        f"套餐：{sub.plan_code}\n"
        f"到期时间：{_dt(sub.current_period_end)}\n"
        "系统已将该订阅标记为过期，用户会按免费套餐权益继续使用。"
    )
    await _notify_once(
        db,
        event=EVENT_SUBSCRIPTION_EXPIRED,
        title=title,
        content=content,
        reference_type="subscription_expired",
        reference_id=int(sub.id),
        priority=3,
        context={"account": username, "plan": sub.plan_code},
    )


async def notify_quota_usage_warning(
    db: AsyncSession,
    *,
    user_id: int,
    metric: str,
    used: int,
    limit: int,
    threshold_percent: int,
) -> None:
    if int(limit or 0) <= 0 or int(limit or 0) >= 999_000:
        return
    user = await _load_user(db, int(user_id))
    username = user.username if user else f"#{user_id}"
    label = metric_label(metric)
    event = EVENT_AI_QUOTA_WARNING if metric == METRIC_AI_CALLS else EVENT_ACCOUNT_QUOTA_WARNING
    title = f"{label}额度已使用 {threshold_percent}%"
    content = (
        f"用户：{username}\n"
        f"指标：{label}\n"
        f"当前用量：{int(used or 0)} / {int(limit or 0)}\n"
        "请评估是否需要升级套餐或调整自动化策略。"
    )
    await _notify_once(
        db,
        event=event,
        title=title,
        content=content,
        reference_type=f"quota_{metric}_{threshold_percent}_{date.today().isoformat()}",
        reference_id=int(user_id),
        priority=3 if threshold_percent >= 100 else 2,
        context={"account": username, "metric": label, "used": used, "limit": limit},
    )


async def maybe_notify_usage_threshold(
    db: AsyncSession,
    *,
    user_id: int,
    metric: str,
    before_used: int,
    after_used: int,
    limit_count: int,
) -> None:
    limit_count = int(limit_count or 0)
    if limit_count <= 0 or limit_count >= 999_000:
        return
    for threshold in (80, 100):
        threshold_count = max(1, math.ceil(limit_count * threshold / 100))
        if int(before_used or 0) < threshold_count <= int(after_used or 0):
            await notify_quota_usage_warning(
                db,
                user_id=user_id,
                metric=metric,
                used=after_used,
                limit=limit_count,
                threshold_percent=threshold,
            )


async def notify_quota_rejection(
    *,
    user_id: int,
    metric: str,
    source_type: str,
    source_id: str = "",
    reason: str = "",
) -> None:
    async with async_session() as db:
        user = await _load_user(db, int(user_id))
        username = user.username if user else f"#{user_id}"
        label = metric_label(metric)
        if source_type == "feature_block":
            event = EVENT_FEATURE_BLOCKED
            title = "套餐权益拦截提醒"
        elif metric == METRIC_ACCOUNTS:
            event = EVENT_ACCOUNT_QUOTA_WARNING
            title = "账号配额不足提醒"
        elif metric == METRIC_AI_CALLS:
            event = EVENT_AI_QUOTA_WARNING
            title = "AI 额度不足提醒"
        else:
            event = EVENT_FEATURE_BLOCKED
            title = "套餐额度拦截提醒"
        content = (
            f"用户：{username}\n"
            f"指标：{label}\n"
            f"来源：{source_type or 'quota_block'} {source_id or ''}\n"
            f"原因：{reason or '套餐额度或权益不足'}"
        )
        inserted = await _notify_once(
            db,
            event=event,
            title=title,
            content=content,
            reference_type=f"{source_type or 'quota_block'}_{metric}_{date.today().isoformat()}",
            reference_id=int(user_id),
            priority=3,
            context={"account": username, "metric": label, "reason": reason},
        )
        if inserted:
            await db.commit()
