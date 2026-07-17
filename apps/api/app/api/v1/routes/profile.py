from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.camel import CamelModel
from ....core.config import settings
from ....core.database import get_db
from ....core.tenancy import owned_account_id_subquery, current_uid, is_superadmin
from ....core.response import ResultObject
from ....core.security import request_client_ip
from ....models.entities import (
    XianyuAccount,
    XianyuConversation,
    XianyuGoods,
    XianyuTradeOrder,
)
from ..deps import get_current_user
from .auth import (
    LAST_LOGIN_SETTING_KEY,
    LAST_SECURITY_UPDATE_SETTING_KEY,
    load_setting_value,
    update_admin_password,
)

router = APIRouter(prefix="/profile", tags=["profile"])


class ChangeProfilePasswordReqDTO(CamelModel):
    old_password: str
    new_password: str


async def count_rows(db: AsyncSession, model, current_user=None) -> int:
    statement = select(func.count()).select_from(model)
    deleted_column = getattr(model, "deleted", None)
    if deleted_column is not None:
        statement = statement.where(deleted_column == 0)
    # 多租户: 账号本身按 owner; 挂 account_id 的表按 owner 的账号集合
    if model is XianyuAccount:
        if current_user is not None and not is_superadmin(current_user):
            statement = statement.where(XianyuAccount.owner_user_id == current_uid(current_user))
    elif getattr(model, "account_id", None) is not None:
        statement = statement.where(model.account_id.in_(owned_account_id_subquery(current_user)))
    result = await db.execute(statement)
    return int(result.scalar() or 0)


@router.get("/overview", response_model=ResultObject[dict])
async def get_profile_overview(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    account_count = await count_rows(db, XianyuAccount, current_user)
    goods_count = await count_rows(db, XianyuGoods, current_user)
    order_count = await count_rows(db, XianyuTradeOrder, current_user)
    conversation_count = await count_rows(db, XianyuConversation, current_user)

    last_login_time = await load_setting_value(db, LAST_LOGIN_SETTING_KEY, "")
    last_security_update_time = await load_setting_value(db, LAST_SECURITY_UPDATE_SETTING_KEY, "")

    return ResultObject.success({
        "userId": current_user.get("user_id", 0),
        "username": current_user.get("username", settings.admin_username),
        "nickname": current_user.get("username", settings.admin_username),
        "tenantName": "智鱼云运营实例",
        "lastLoginTime": last_login_time or None,
        "lastSecurityUpdateTime": last_security_update_time or None,
        "updatedTime": last_security_update_time or last_login_time or None,
        "stats": {
            "xianyuAccountCount": account_count,
            "goodsCount": goods_count,
            "orderCount": order_count,
            "conversationCount": conversation_count,
        },
    })


@router.post("/change-password", response_model=ResultObject[str])
async def change_profile_password(
    req: ChangeProfilePasswordReqDTO,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    error = await update_admin_password(
        db,
        old_password=req.old_password,
        new_password=req.new_password,
        operator=current_user.get("username", settings.admin_username),
        ip_address=request_client_ip(request),
        operation_desc="个人中心修改登录密码",
        target_type="profile",
    )
    if error:
        return ResultObject.validate_failed(error)
    return ResultObject.success("密码修改成功")
