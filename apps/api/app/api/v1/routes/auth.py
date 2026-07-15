import asyncio
import logging
import hmac
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.camel import CamelModel
from ....core.config import settings
from ....core.database import get_db
from ....core.response import ResultObject
from ....core.redis_client import RedisUnavailableError
from ....core.security import (
    clear_login_failures,
    create_token,
    hash_password,
    login_retry_after,
    record_login_failure,
    request_client_ip,
    revoke_all_tokens,
    revoke_token_payload,
    validate_password_strength,
    verify_password,
)
from sqlalchemy.exc import IntegrityError

from ....models.entities import XianyuOperationLog, XianyuSysSetting, AdminUser, AppPlan
from ....services.email_service import send_verification_email, verify_code
from ..deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

PASSWORD_SETTING_KEY = "admin_password_hash"
LAST_LOGIN_SETTING_KEY = "admin_last_login_time"
LAST_SECURITY_UPDATE_SETTING_KEY = "admin_last_security_update_time"
ADMIN_PHONE_SETTING_KEY = "admin_phone"
ADMIN_PHONE_VERIFIED_SETTING_KEY = "admin_phone_verified"
ADMIN_EMAIL_SETTING_KEY = "admin_email"
ADMIN_EMAIL_VERIFIED_SETTING_KEY = "admin_email_verified"


class LoginReqDTO(CamelModel):
    username: str
    password: str


class LoginRespDTO(CamelModel):
    token: str
    username: str
    role: str = "admin"


class ProfileRespDTO(CamelModel):
    user_id: int = 0
    username: str
    role: str = "admin"
    avatar: Optional[str] = ""
    email: Optional[str] = ""
    nickname: Optional[str] = ""
    plan_code: Optional[str] = ""
    max_accounts: int = 0
    ai_daily_quota: int = 0
    email_verified: bool = False


class ChangePasswordReqDTO(CamelModel):
    old_password: str
    new_password: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def load_setting_value(db: AsyncSession, key: str, default: str = "") -> str:
    result = await db.execute(
        select(XianyuSysSetting).where(XianyuSysSetting.setting_key == key)
    )
    setting = result.scalar_one_or_none()
    if setting and setting.setting_value is not None:
        return setting.setting_value
    return default


async def save_setting_value(
    db: AsyncSession,
    key: str,
    value: str,
    *,
    commit: bool = True,
) -> None:
    result = await db.execute(
        select(XianyuSysSetting).where(XianyuSysSetting.setting_key == key)
    )
    setting = result.scalar_one_or_none()
    if setting:
        setting.setting_value = value
    else:
        db.add(XianyuSysSetting(setting_key=key, setting_value=value))
    if commit:
        await db.commit()


async def load_admin_password_hash(db: AsyncSession) -> str:
    try:
        stored = await load_setting_value(db, PASSWORD_SETTING_KEY, "")
        if stored:
            return stored
    except Exception:
        if (settings.app_env or "").strip().casefold() != "test":
            logger.error("Failed to load admin password hash from database", exc_info=True)
            raise
        logger.warning("Failed to load admin password hash from db, fallback to test env", exc_info=True)
    return settings.admin_password_hash


async def save_admin_password_hash(
    db: AsyncSession,
    new_hash: str,
    *,
    commit: bool = True,
) -> None:
    await save_setting_value(db, PASSWORD_SETTING_KEY, new_hash, commit=commit)


async def mark_admin_login(db: AsyncSession, *, commit: bool = True) -> None:
    await save_setting_value(
        db,
        LAST_LOGIN_SETTING_KEY,
        now_iso(),
        commit=commit,
    )


async def mark_admin_security_update(db: AsyncSession, *, commit: bool = True) -> None:
    await save_setting_value(
        db,
        LAST_SECURITY_UPDATE_SETTING_KEY,
        now_iso(),
        commit=commit,
    )


async def validate_admin_credentials(db: AsyncSession, username: str, password: str) -> Optional[str]:
    username = (username or "").strip()
    password = password or ""
    if not username or not password:
        return "用户名或密码不能为空"

    password_hash = await load_admin_password_hash(db)
    if not password_hash:
        return "管理员密码未配置，请在 .env 中设置 ADMIN_PASSWORD_HASH"
    username_matches = hmac.compare_digest(username, settings.admin_username)
    password_matches = await asyncio.to_thread(
        verify_password,
        password,
        password_hash,
    )
    if not username_matches or not password_matches:
        return "用户名或密码错误"
    return None


async def update_admin_password(
    db: AsyncSession,
    *,
    old_password: str,
    new_password: str,
    operator: str,
    ip_address: str,
    operation_desc: str,
    target_type: str,
) -> str | None:
    """Apply the single password-change policy used by every compatibility API."""
    old_password = old_password or ""
    new_password = new_password or ""
    if not old_password or not new_password:
        return "当前密码和新密码不能为空"

    strength_error = validate_password_strength(new_password, settings.admin_username)
    if strength_error:
        return strength_error

    stored_hash = await load_admin_password_hash(db)
    if not stored_hash:
        return "管理员密码尚未配置"
    if not await asyncio.to_thread(verify_password, old_password, stored_hash):
        return "当前密码错误"
    if await asyncio.to_thread(verify_password, new_password, stored_hash):
        return "新密码不能与当前密码相同"

    try:
        new_password_hash = await asyncio.to_thread(hash_password, new_password)
        await save_admin_password_hash(db, new_password_hash, commit=False)
        await mark_admin_security_update(db, commit=False)
        db.add(XianyuOperationLog(
            operator=operator,
            operation_type="change_password",
            operation_desc=operation_desc,
            target_type=target_type,
            target_id="admin",
            ip_address=ip_address,
        ))
        await revoke_all_tokens()
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return None


async def enforce_login_rate_limit(request: Request) -> None:
    retry_after = await login_retry_after(request)
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail="登录尝试次数过多，请稍后重试",
            headers={"Retry-After": str(retry_after)},
        )


@router.post("/login", response_model=ResultObject[LoginRespDTO])
async def login(req: LoginReqDTO, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        await enforce_login_rate_limit(request)
        login_id = (req.username or "").strip()
        password = req.password or ""
        if not login_id or not password:
            raise HTTPException(status_code=422, detail="用户名或密码不能为空")

        user = await load_user_by_login(db, login_id)
        authed_uid = 0
        authed_username = login_id
        authed_role = "user"

        if user is not None:
            is_super = bool(user.is_super)
            if is_super and user.username == settings.admin_username:
                # 种子超管: 历史改密写在 admin_password_hash 设置里, 走 legacy 校验保持兼容
                error = await validate_admin_credentials(db, user.username, password)
                if error:
                    if error.startswith("管理员密码未配置"):
                        raise HTTPException(status_code=503, detail="认证服务尚未完成管理员密码配置")
                    await record_login_failure(request)
                    raise HTTPException(status_code=401, detail="用户名或密码错误")
            else:
                ok = await asyncio.to_thread(verify_password, password, user.password_hash or "")
                if not ok:
                    await record_login_failure(request)
                    raise HTTPException(status_code=401, detail="用户名或密码错误")
                if not user.email_verified:
                    raise HTTPException(status_code=403, detail="邮箱未验证，请先完成邮箱验证")
            authed_uid = int(user.id)
            authed_username = user.username
            authed_role = "superadmin" if is_super else "user"
        else:
            # 表中无记录: 仅允许 legacy 种子管理员(admin_user 未种入的场景)
            if login_id == settings.admin_username:
                error = await validate_admin_credentials(db, login_id, password)
                if error:
                    if error.startswith("管理员密码未配置"):
                        raise HTTPException(status_code=503, detail="认证服务尚未完成管理员密码配置")
                    await record_login_failure(request)
                    raise HTTPException(status_code=401, detail="用户名或密码错误")
                authed_uid = 0
                authed_username = login_id
                authed_role = "superadmin"
            else:
                await record_login_failure(request)
                raise HTTPException(status_code=401, detail="用户名或密码错误")

        await clear_login_failures(request)
        token = create_token(authed_username, user_id=authed_uid, role=authed_role)
        try:
            if user is not None:
                user.last_login_time = datetime.now(timezone.utc)
                db.add(user)
            if authed_username == settings.admin_username:
                await mark_admin_login(db, commit=False)
            db.add(XianyuOperationLog(
                operator=authed_username,
                operation_type="login",
                operation_desc="用户登录",
                target_type="auth",
                target_id=str(authed_uid),
                ip_address=request_client_ip(request),
            ))
            await db.commit()
        except Exception:
            await db.rollback()
            logger.error("Failed to persist successful-login audit", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail="登录审计暂不可用，未签发会话",
            )

        return ResultObject.success(
            LoginRespDTO(token=token, username=authed_username, role=authed_role)
        )
    except RedisUnavailableError:
        raise HTTPException(
            status_code=503,
            detail="认证安全状态暂不可用，请稍后重试",
        )
    except HTTPException:
        raise
    except Exception:
        logger.error("登录失败", exc_info=True)
        raise HTTPException(status_code=503, detail="登录服务暂不可用，请稍后重试")


@router.get("/profile", response_model=ResultObject[ProfileRespDTO])
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = int(current_user.get("user_id") or 0)
    user = None
    if uid:
        user = (await db.execute(select(AdminUser).where(AdminUser.id == uid))).scalars().first()
    if user is not None:
        return ResultObject.success(ProfileRespDTO(
            user_id=int(user.id),
            username=user.username,
            role=("superadmin" if user.is_super else "user"),
            avatar=user.avatar_url or "",
            email=user.email or "",
            nickname=user.nickname or user.username,
            plan_code=user.plan_code or "free",
            max_accounts=int(user.max_accounts or 0),
            ai_daily_quota=int(user.ai_daily_quota or 0),
            email_verified=bool(user.email_verified),
        ))
    # legacy 种子管理员回退
    email = await load_setting_value(db, ADMIN_EMAIL_SETTING_KEY, "")
    return ResultObject.success(ProfileRespDTO(
        user_id=current_user.get("user_id", 0),
        username=current_user.get("username", settings.admin_username),
        role=current_user.get("role", "superadmin"),
        email=email,
        plan_code="max",
    ))


@router.post("/logout", response_model=ResultObject[None])
async def logout(current_user: dict = Depends(get_current_user)):
    try:
        await revoke_token_payload(current_user)
    except RedisUnavailableError:
        raise HTTPException(
            status_code=503,
            detail="认证安全状态暂不可用，退出结果未确认，请稍后重试",
        )
    return ResultObject.success(None, message="已退出登录")


@router.put("/password", response_model=ResultObject[str])
async def change_password(
    req: ChangePasswordReqDTO,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        error = await update_admin_password(
            db,
            old_password=req.old_password,
            new_password=req.new_password,
            operator=current_user.get("username", settings.admin_username),
            ip_address=request_client_ip(request),
            operation_desc="管理员修改登录密码",
            target_type="auth",
        )
        if error:
            return ResultObject.validate_failed(error)

        return ResultObject.success("密码修改成功")
    except RedisUnavailableError:
        raise HTTPException(
            status_code=503,
            detail="认证安全状态暂不可用，密码未修改，请稍后重试",
        )
    except Exception:
        logger.error("修改密码失败", exc_info=True)
        return ResultObject.failed("修改密码失败，请稍后重试")


# ============================================================
# 多用户: 注册 / 套餐 (智鱼云商业版 2A)
# ============================================================
async def load_user_by_login(db: AsyncSession, login: str) -> Optional[AdminUser]:
    """按用户名或邮箱加载启用状态的用户。"""
    login = (login or "").strip()
    if not login:
        return None
    stmt = select(AdminUser).where(
        (AdminUser.username == login) | (AdminUser.email == login.lower()),
        AdminUser.status == 1,
    )
    return (await db.execute(stmt)).scalars().first()


class RegisterSendCodeReqDTO(CamelModel):
    email: str


class RegisterReqDTO(CamelModel):
    email: str
    code: str
    username: str
    password: str
    nickname: Optional[str] = ""


class PlanRespDTO(CamelModel):
    code: str
    name: str
    max_accounts: int
    ai_daily_quota: int
    price_cents: int
    description: Optional[str] = ""


@router.get("/plans", response_model=ResultObject[list[PlanRespDTO]])
async def list_plans(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(AppPlan).where(AppPlan.status == 1).order_by(AppPlan.sort_order)
    )).scalars().all()
    return ResultObject.success([
        PlanRespDTO(
            code=p.code, name=p.name, max_accounts=p.max_accounts,
            ai_daily_quota=p.ai_daily_quota, price_cents=p.price_cents,
            description=p.description or "",
        ) for p in rows
    ])


@router.post("/register/send-code", response_model=ResultObject[None])
async def register_send_code(
    req: RegisterSendCodeReqDTO, request: Request, db: AsyncSession = Depends(get_db)
):
    if not settings.registration_enabled:
        raise HTTPException(status_code=403, detail="注册暂未开放")
    email = (req.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="请输入有效邮箱")
    exists = (await db.execute(select(AdminUser).where(AdminUser.email == email))).scalars().first()
    if exists:
        raise HTTPException(status_code=409, detail="该邮箱已注册")
    try:
        await send_verification_email(db, email, "register")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RedisUnavailableError:
        raise HTTPException(status_code=503, detail="验证码服务暂不可用，请稍后重试")
    return ResultObject.success(None, message="验证码已发送，5 分钟内有效")


@router.post("/register", response_model=ResultObject[LoginRespDTO])
async def register(
    req: RegisterReqDTO, request: Request, db: AsyncSession = Depends(get_db)
):
    if not settings.registration_enabled:
        raise HTTPException(status_code=403, detail="注册暂未开放")
    email = (req.email or "").strip().lower()
    username = (req.username or "").strip()
    password = req.password or ""
    code = (req.code or "").strip()

    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="请输入有效邮箱")
    if len(username) < 3 or len(username) > 32:
        raise HTTPException(status_code=422, detail="用户名长度需为 3-32 个字符")
    if username == settings.admin_username:
        raise HTTPException(status_code=409, detail="该用户名不可用")
    strength_error = validate_password_strength(password, username)
    if strength_error:
        raise HTTPException(status_code=422, detail=strength_error)

    ok, msg = await verify_code(email, "register", code)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    dup = (await db.execute(
        select(AdminUser).where((AdminUser.email == email) | (AdminUser.username == username))
    )).scalars().first()
    if dup:
        raise HTTPException(status_code=409, detail="用户名或邮箱已被占用")

    plan = (await db.execute(select(AppPlan).where(AppPlan.code == "free"))).scalars().first()
    max_accounts = int(plan.max_accounts) if plan else 1
    ai_quota = int(plan.ai_daily_quota) if plan else 100

    pwd_hash = await asyncio.to_thread(hash_password, password)
    user = AdminUser(
        username=username,
        email=email,
        password_hash=pwd_hash,
        is_super=0,
        status=1,
        email_verified=1,
        nickname=(req.nickname or username)[:100],
        plan_code="free",
        max_accounts=max_accounts,
        ai_daily_quota=ai_quota,
        register_ip=request_client_ip(request),
        last_login_time=datetime.now(timezone.utc),
    )
    db.add(user)
    try:
        db.add(XianyuOperationLog(
            operator=username,
            operation_type="register",
            operation_desc="用户注册",
            target_type="auth",
            target_id=email,
            ip_address=request_client_ip(request),
        ))
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="用户名或邮箱已被占用")
    except Exception:
        await db.rollback()
        logger.error("注册失败", exc_info=True)
        raise HTTPException(status_code=503, detail="注册服务暂不可用，请稍后重试")

    token = create_token(user.username, user_id=int(user.id), role="user")
    return ResultObject.success(
        LoginRespDTO(token=token, username=user.username, role="user"),
        message="注册成功",
    )
