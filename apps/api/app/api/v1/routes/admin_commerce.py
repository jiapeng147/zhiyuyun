"""超级管理员: 商业版管理端点(用户管理 / 注册开关 / 邮箱SMTP)。"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.security import hash_password

from ....core.camel import CamelModel
from ....core.config import settings
from ....core.database import get_db
from ....core.response import ResultObject
from ....models.entities import (
    AdminUser,
    AppBillingOrder,
    AppPlan,
    AppSubscription,
    XianyuAccount,
    XianyuGoods,
    XianyuTradeOrder,
    XianyuSysSetting,
)
from ....services.billing import (
    BillingError,
    activate_order,
    billing_overview,
    billing_state_for_user,
    close_billing_order,
    create_billing_order,
    load_payment_config,
    normalize_feature_flags,
    feature_items,
    reconcile_billing_lifecycle,
    save_payment_config,
)
from ....services.email_service import (
    load_email_smtp_config,
    save_email_smtp_config,
    build_public_smtp_config,
)
from ..deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

REGISTRATION_SETTING_KEY = "registration_enabled"


async def require_superadmin(current_user: dict = Depends(get_current_user)) -> dict:
    if (current_user or {}).get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return current_user


async def _load_setting(db: AsyncSession, key: str, default: str = "") -> str:
    row = (await db.execute(
        select(XianyuSysSetting).where(XianyuSysSetting.setting_key == key)
    )).scalar_one_or_none()
    return row.setting_value if row and row.setting_value is not None else default


async def _save_setting(db: AsyncSession, key: str, value: str) -> None:
    row = (await db.execute(
        select(XianyuSysSetting).where(XianyuSysSetting.setting_key == key)
    )).scalar_one_or_none()
    if row:
        row.setting_value = value
    else:
        db.add(XianyuSysSetting(setting_key=key, setting_value=value))


async def registration_open(db: AsyncSession) -> bool:
    """运行时注册开关: DB 设置优先, 回退 env 默认。"""
    raw = (await _load_setting(db, REGISTRATION_SETTING_KEY, "")).strip()
    if raw in ("1", "true", "True"):
        return True
    if raw in ("0", "false", "False"):
        return False
    return bool(settings.registration_enabled)


def _dt(v) -> str:
    try:
        return v.isoformat() if v else ""
    except Exception:
        return ""


class UserRespDTO(CamelModel):
    id: int
    username: str
    email: Optional[str] = ""
    role: str = "user"
    plan_code: Optional[str] = "free"
    status: int = 1
    email_verified: bool = False
    max_accounts: int = 0
    ai_daily_quota: int = 0
    created_time: Optional[str] = ""
    last_login_time: Optional[str] = ""


class UpdateUserReqDTO(CamelModel):
    status: Optional[int] = None
    plan_code: Optional[str] = None


class RegistrationReqDTO(CamelModel):
    enabled: bool


class EmailConfigReqDTO(CamelModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None
    from_name: Optional[str] = None


class PlanReqDTO(CamelModel):
    code: str
    name: str
    max_accounts: int = 1
    ai_daily_quota: int = 100
    price_cents: int = 0
    sort_order: int = 0
    status: int = 1
    description: Optional[str] = None
    features: Optional[dict[str, bool]] = None


class PlanRespDTO(CamelModel):
    id: int
    code: str
    name: str
    max_accounts: int
    ai_daily_quota: int
    price_cents: int
    sort_order: int
    status: int
    description: Optional[str] = ""
    features: dict[str, bool] = {}
    feature_items: list[dict[str, Any]] = []
    created_time: Optional[str] = ""
    updated_time: Optional[str] = ""


class CreateUserReqDTO(CamelModel):
    username: str
    email: Optional[str] = None
    password: str
    plan_code: Optional[str] = "free"
    is_super: bool = False


class ResetPasswordReqDTO(CamelModel):
    new_password: str


class AdminActivateSubscriptionReqDTO(CamelModel):
    plan_code: str
    duration_days: int = 30
    note: Optional[str] = None


class AdminMarkBillingOrderPaidReqDTO(CamelModel):
    note: Optional[str] = None


class AdminCloseBillingOrderReqDTO(CamelModel):
    reason: Optional[str] = "admin_close"


class BillingPaymentConfigReqDTO(CamelModel):
    enabled: bool = False
    order_expire_minutes: int = 1440
    payment_methods: Optional[list[str]] = None
    instructions: Optional[str] = None
    contact: Optional[str] = None
    alipay_qr_url: Optional[str] = None
    wechat_qr_url: Optional[str] = None
    bank_account: Optional[str] = None


def _plan_to_dto(p: AppPlan) -> PlanRespDTO:
    flags = normalize_feature_flags(p.feature_flags)
    return PlanRespDTO(
        id=int(p.id), code=p.code, name=p.name,
        max_accounts=int(p.max_accounts or 0), ai_daily_quota=int(p.ai_daily_quota or 0),
        price_cents=int(p.price_cents or 0), sort_order=int(p.sort_order or 0),
        status=int(p.status or 0), description=p.description or "",
        features=flags, feature_items=feature_items(flags),
        created_time=_dt(p.created_time), updated_time=_dt(p.updated_time),
    )


def _billing_order_payload(order: AppBillingOrder, user: AdminUser | None = None) -> dict:
    return {
        "id": int(order.id),
        "orderNo": order.order_no,
        "userId": int(order.user_id),
        "username": user.username if user else "",
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


def _subscription_payload(sub: AppSubscription, user: AdminUser | None = None) -> dict:
    return {
        "id": int(sub.id),
        "userId": int(sub.user_id),
        "username": user.username if user else "",
        "planCode": sub.plan_code,
        "status": sub.status,
        "currentPeriodStart": _dt(sub.current_period_start),
        "currentPeriodEnd": _dt(sub.current_period_end),
        "sourceOrderId": int(sub.source_order_id or 0),
        "cancelAtPeriodEnd": bool(sub.cancel_at_period_end),
        "createdTime": _dt(sub.created_time),
    }


@router.get("/users", response_model=ResultObject[list[UserRespDTO]])
async def list_users(db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin)):
    rows = (await db.execute(select(AdminUser).order_by(AdminUser.id))).scalars().all()
    return ResultObject.success([
        UserRespDTO(
            id=int(u.id), username=u.username, email=u.email or "",
            role=("superadmin" if u.is_super else "user"),
            plan_code=u.plan_code or "free", status=int(u.status or 0),
            email_verified=bool(u.email_verified),
            max_accounts=int(u.max_accounts or 0), ai_daily_quota=int(u.ai_daily_quota or 0),
            created_time=_dt(u.created_time), last_login_time=_dt(u.last_login_time),
        ) for u in rows
    ])


@router.put("/users/{uid}", response_model=ResultObject[str])
async def update_user(
    uid: int, req: UpdateUserReqDTO,
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    user = (await db.execute(select(AdminUser).where(AdminUser.id == uid))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.is_super and req.status is not None and int(req.status) == 0:
        raise HTTPException(status_code=400, detail="不能禁用超级管理员")
    if req.status is not None:
        user.status = int(req.status)
    if req.plan_code:
        plan = (await db.execute(select(AppPlan).where(AppPlan.code == req.plan_code))).scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=400, detail="套餐不存在")
        user.plan_code = plan.code
        user.max_accounts = plan.max_accounts
        user.ai_daily_quota = plan.ai_daily_quota
    await db.commit()
    return ResultObject.success("已更新")


@router.get("/registration", response_model=ResultObject[dict])
async def get_registration(db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin)):
    return ResultObject.success({"enabled": await registration_open(db)})


@router.put("/registration", response_model=ResultObject[dict])
async def set_registration(
    req: RegistrationReqDTO,
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    await _save_setting(db, REGISTRATION_SETTING_KEY, "1" if req.enabled else "0")
    await db.commit()
    return ResultObject.success({"enabled": bool(req.enabled)})


@router.get("/email-config", response_model=ResultObject[dict])
async def get_email_config(db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin)):
    cfg = await load_email_smtp_config(db)
    return ResultObject.success(build_public_smtp_config(cfg))


@router.put("/email-config", response_model=ResultObject[dict])
async def set_email_config(
    req: EmailConfigReqDTO,
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    payload = {k: v for k, v in req.model_dump().items() if v is not None}
    saved = await save_email_smtp_config(db, payload)
    return ResultObject.success(build_public_smtp_config(saved))



@router.get("/overview", response_model=ResultObject[dict])
async def platform_overview(
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    """平台总览: 用户/账号/商品/订单 + 今日新增 + 活跃用户(7 日内登录) + 套餐分布。"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = now - timedelta(days=7)

    user_count = int((await db.execute(select(func.count()).select_from(AdminUser))).scalar() or 0)
    active_user_count = int((await db.execute(
        select(func.count()).select_from(AdminUser).where(
            AdminUser.last_login_time.is_not(None),
            AdminUser.last_login_time >= seven_days_ago,
        )
    )).scalar() or 0)
    new_user_today = int((await db.execute(
        select(func.count()).select_from(AdminUser).where(AdminUser.created_time >= today_start)
    )).scalar() or 0)

    account_count = int((await db.execute(
        select(func.count()).select_from(XianyuAccount).where(XianyuAccount.deleted == 0)
    )).scalar() or 0)
    goods_count = int((await db.execute(
        select(func.count()).select_from(XianyuGoods).where(XianyuGoods.deleted == 0)
    )).scalar() or 0)
    order_count = int((await db.execute(
        select(func.count()).select_from(XianyuTradeOrder)
    )).scalar() or 0)
    new_order_today = int((await db.execute(
        select(func.count()).select_from(XianyuTradeOrder).where(
            XianyuTradeOrder.created_time >= today_start
        ) if hasattr(XianyuTradeOrder, "created_time") else select(func.count()).select_from(XianyuTradeOrder)
    )).scalar() or 0)

    plan_rows = (await db.execute(
        select(AdminUser.plan_code, func.count().label("n")).group_by(AdminUser.plan_code)
    )).all()
    plan_distribution = [{"plan_code": (r[0] or "free"), "count": int(r[1] or 0)} for r in plan_rows]

    return ResultObject.success({
        "user": {
            "total": user_count,
            "active_7d": active_user_count,
            "new_today": new_user_today,
        },
        "account": {"total": account_count},
        "goods": {"total": goods_count},
        "order": {"total": order_count, "new_today": new_order_today},
        "plan_distribution": plan_distribution,
        "generated_at": now.isoformat(),
    })


# ============================================================
# 套餐管理
# ============================================================

@router.get("/plans", response_model=ResultObject[list[PlanRespDTO]])
async def list_plans(
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    rows = (await db.execute(
        select(AppPlan).order_by(AppPlan.sort_order.asc(), AppPlan.id.asc())
    )).scalars().all()
    return ResultObject.success([_plan_to_dto(p) for p in rows])


@router.post("/plans", response_model=ResultObject[PlanRespDTO])
async def create_plan(
    req: PlanReqDTO,
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    code = (req.code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="套餐代码不能为空")
    existing = (await db.execute(select(AppPlan).where(AppPlan.code == code))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"套餐代码 {code} 已存在")
    plan = AppPlan(
        code=code, name=req.name.strip(),
        max_accounts=int(req.max_accounts), ai_daily_quota=int(req.ai_daily_quota),
        price_cents=int(req.price_cents), sort_order=int(req.sort_order),
        status=int(req.status), description=req.description,
        feature_flags=normalize_feature_flags(req.features),
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return ResultObject.success(_plan_to_dto(plan))


@router.put("/plans/{plan_id}", response_model=ResultObject[PlanRespDTO])
async def update_plan(
    plan_id: int, req: PlanReqDTO,
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    plan = (await db.execute(select(AppPlan).where(AppPlan.id == plan_id))).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")
    if req.code.strip() and req.code.strip() != plan.code:
        clash = (await db.execute(select(AppPlan).where(
            AppPlan.code == req.code.strip(), AppPlan.id != plan_id
        ))).scalar_one_or_none()
        if clash:
            raise HTTPException(status_code=409, detail="套餐代码已被占用")
        plan.code = req.code.strip()
    plan.name = (req.name or plan.name).strip()
    plan.max_accounts = int(req.max_accounts)
    plan.ai_daily_quota = int(req.ai_daily_quota)
    plan.price_cents = int(req.price_cents)
    plan.sort_order = int(req.sort_order)
    plan.status = int(req.status)
    plan.description = req.description
    if req.features is not None:
        plan.feature_flags = normalize_feature_flags(req.features)
    await db.commit()
    await db.refresh(plan)
    return ResultObject.success(_plan_to_dto(plan))


@router.delete("/plans/{plan_id}", response_model=ResultObject[str])
async def delete_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    plan = (await db.execute(select(AppPlan).where(AppPlan.id == plan_id))).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")
    in_use = int((await db.execute(
        select(func.count()).select_from(AdminUser).where(AdminUser.plan_code == plan.code)
    )).scalar() or 0)
    if in_use > 0:
        # 不级联,下架即可
        plan.status = 0
        await db.commit()
        return ResultObject.success(f"套餐已被 {in_use} 个用户引用,已下架(未删除)")
    await db.delete(plan)
    await db.commit()
    return ResultObject.success("已删除")


# ============================================================
# 手动建用户 + 重置密码
# ============================================================

@router.post("/users", response_model=ResultObject[UserRespDTO])
async def create_user(
    req: CreateUserReqDTO,
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    username = (req.username or "").strip()
    password = req.password or ""
    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="密码至少 8 位")
    clash = (await db.execute(select(AdminUser).where(AdminUser.username == username))).scalar_one_or_none()
    if clash:
        raise HTTPException(status_code=409, detail="用户名已存在")
    if req.email:
        e = req.email.strip().lower()
        ec = (await db.execute(select(AdminUser).where(AdminUser.email == e))).scalar_one_or_none()
        if ec:
            raise HTTPException(status_code=409, detail="邮箱已被使用")
    plan_code = (req.plan_code or "free").strip() or "free"
    plan = (await db.execute(select(AppPlan).where(AppPlan.code == plan_code))).scalar_one_or_none()
    user = AdminUser(
        username=username,
        email=(req.email.strip().lower() if req.email else None),
        password_hash=hash_password(password),
        is_super=1 if req.is_super else 0,
        plan_code=plan.code if plan else plan_code,
        max_accounts=(plan.max_accounts if plan else 1),
        ai_daily_quota=(plan.ai_daily_quota if plan else 100),
        status=1,
        email_verified=1,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return ResultObject.success(UserRespDTO(
        id=int(user.id), username=user.username, email=user.email or "",
        role=("superadmin" if user.is_super else "user"),
        plan_code=user.plan_code or "free", status=int(user.status or 0),
        email_verified=bool(user.email_verified),
        max_accounts=int(user.max_accounts or 0), ai_daily_quota=int(user.ai_daily_quota or 0),
        created_time=_dt(user.created_time), last_login_time=_dt(user.last_login_time),
    ))


@router.post("/users/{uid}/reset-password", response_model=ResultObject[str])
async def reset_password(
    uid: int, req: ResetPasswordReqDTO,
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    new_pw = req.new_password or ""
    if len(new_pw) < 8:
        raise HTTPException(status_code=400, detail="新密码至少 8 位")
    user = (await db.execute(select(AdminUser).where(AdminUser.id == uid))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password_hash = hash_password(new_pw)
    await db.commit()
    return ResultObject.success(f"已重置 {user.username} 的密码")


# ============================================================
# 商业计费：订阅 / 订单 / 手动开通
# ============================================================

@router.get("/subscriptions", response_model=ResultObject[list[dict]])
async def list_subscriptions(
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    reconciled = await reconcile_billing_lifecycle(db)
    if reconciled["closedOrders"] or reconciled["expiredSubscriptions"]:
        await db.commit()
    rows = (
        await db.execute(
            select(AppSubscription, AdminUser)
            .outerjoin(AdminUser, AdminUser.id == AppSubscription.user_id)
            .order_by(AppSubscription.id.desc())
        )
    ).all()
    return ResultObject.success([_subscription_payload(sub, user) for sub, user in rows])


@router.get("/billing-orders", response_model=ResultObject[list[dict]])
async def list_billing_orders(
    status: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    reconciled = await reconcile_billing_lifecycle(db)
    if reconciled["closedOrders"] or reconciled["expiredSubscriptions"]:
        await db.commit()
    statement = (
        select(AppBillingOrder, AdminUser)
        .outerjoin(AdminUser, AdminUser.id == AppBillingOrder.user_id)
    )
    if status:
        statement = statement.where(AppBillingOrder.status == status)
    rows = (
        await db.execute(
            statement.order_by(AppBillingOrder.id.desc())
        )
    ).all()
    return ResultObject.success([_billing_order_payload(order, user) for order, user in rows])


@router.get("/billing-overview", response_model=ResultObject[dict])
async def get_billing_overview(
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    return ResultObject.success(await billing_overview(db))


@router.get("/billing-settings", response_model=ResultObject[dict])
async def get_billing_settings(
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    return ResultObject.success(await load_payment_config(db))


@router.put("/billing-settings", response_model=ResultObject[dict])
async def set_billing_settings(
    req: BillingPaymentConfigReqDTO,
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    return ResultObject.success(await save_payment_config(db, req.model_dump()), message="账单设置已保存")


@router.get("/users/{uid}/billing", response_model=ResultObject[dict])
async def get_user_billing(
    uid: int,
    db: AsyncSession = Depends(get_db), _: dict = Depends(require_superadmin),
):
    return ResultObject.success(await billing_state_for_user(db, uid))


@router.post("/users/{uid}/subscription", response_model=ResultObject[dict])
async def activate_user_subscription(
    uid: int,
    req: AdminActivateSubscriptionReqDTO,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_superadmin),
):
    try:
        order = await create_billing_order(
            db,
            user_id=uid,
            plan_code=req.plan_code,
            duration_days=req.duration_days,
            order_type="manual",
            payment_method="admin_grant",
        )
        order.metadata_json = {
            **(order.metadata_json or {}),
            "adminNote": req.note or "",
        }
        await activate_order(db, order, operator=str(current_user.get("username") or "admin"))
        await db.commit()
        await db.refresh(order)
        user = (await db.execute(select(AdminUser).where(AdminUser.id == uid))).scalar_one_or_none()
        return ResultObject.success(_billing_order_payload(order, user), message="套餐已开通")
    except BillingError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/billing-orders/{order_id}/mark-paid", response_model=ResultObject[dict])
async def mark_billing_order_paid(
    order_id: int,
    req: AdminMarkBillingOrderPaidReqDTO,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_superadmin),
):
    order = (
        await db.execute(select(AppBillingOrder).where(AppBillingOrder.id == order_id))
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status == "paid":
        user = (
            await db.execute(select(AdminUser).where(AdminUser.id == order.user_id))
        ).scalar_one_or_none()
        return ResultObject.success(_billing_order_payload(order, user), message="订单已是已支付状态")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="当前订单状态不能确认支付")
    order.metadata_json = {
        **(order.metadata_json or {}),
        "adminPaidNote": req.note or "",
    }
    try:
        await activate_order(db, order, operator=str(current_user.get("username") or "admin"))
        await db.commit()
        await db.refresh(order)
        user = (
            await db.execute(select(AdminUser).where(AdminUser.id == order.user_id))
        ).scalar_one_or_none()
        return ResultObject.success(_billing_order_payload(order, user), message="订单已确认支付并激活套餐")
    except BillingError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/billing-orders/{order_id}/close", response_model=ResultObject[dict])
async def close_admin_billing_order(
    order_id: int,
    req: AdminCloseBillingOrderReqDTO,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_superadmin),
):
    order = (
        await db.execute(select(AppBillingOrder).where(AppBillingOrder.id == order_id))
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    try:
        await close_billing_order(
            db,
            order,
            operator=str(current_user.get("username") or "admin"),
            reason=req.reason or "admin_close",
        )
        await db.commit()
        await db.refresh(order)
        user = (
            await db.execute(select(AdminUser).where(AdminUser.id == order.user_id))
        ).scalar_one_or_none()
        return ResultObject.success(_billing_order_payload(order, user), message="订单已关闭")
    except BillingError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
