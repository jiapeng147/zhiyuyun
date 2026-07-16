"""超级管理员: 商业版管理端点(用户管理 / 注册开关 / 邮箱SMTP)。"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.camel import CamelModel
from ....core.config import settings
from ....core.database import get_db
from ....core.response import ResultObject
from ....models.entities import AdminUser, AppPlan, XianyuSysSetting
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
