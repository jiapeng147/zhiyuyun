"""多租户行级隔离核心助手 (智鱼云商业版 2B)。

隔离锚点: ``xianyu_account.owner_user_id``。
每个用户拥有一批闲鱼账号, 账号下的数据(商品/订单/消息/会话/发货...)通过
``account_id`` 传递隔离。少数无 account_id 的表(知识库/规则/卡组/定时任务)
自带 owner_user_id 直接隔离。平台级配置(sys_setting/敏感词/模型配置)仅超管可写。

角色约定 (JWT 携带):
  - ``superadmin`` : 平台超级管理员, 可见并可管理全部租户数据。
  - ``user``       : 普通注册用户, 仅可见自己名下账号及其数据。

用法约定:
  * 读列表: ``ids = await owned_account_ids(db, current_user)``
            ``stmt = scope_by_account(stmt, Model.account_id, ids)``
  * 读/改单条(带 account_id): 先 ``await assert_account_owned(db, current_user, account_id)``
  * 写账号: 落库时 ``owner_user_id = current_uid(current_user)``
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.entities import XianyuAccount


def is_superadmin(current_user: dict | None) -> bool:
    return (current_user or {}).get("role") == "superadmin"


def current_uid(current_user: dict | None) -> int:
    try:
        return int((current_user or {}).get("user_id") or 0)
    except (TypeError, ValueError):
        return 0


async def owned_account_ids(
    db: AsyncSession, current_user: dict | None
) -> Optional[list[int]]:
    """当前用户拥有的闲鱼账号ID列表。

    返回 ``None`` 表示不限制(超管, 全部可见)。
    普通用户返回其账号ID列表(可能为空列表 → 应产生空结果集)。
    """
    if is_superadmin(current_user):
        return None
    uid = current_uid(current_user)
    if not uid:
        return []
    rows = (
        await db.execute(
            select(XianyuAccount.id).where(
                XianyuAccount.owner_user_id == uid,
                XianyuAccount.deleted == 0,
            )
        )
    ).scalars().all()
    return [int(r) for r in rows]


def scope_by_account(stmt, account_id_column, account_ids: Optional[list[int]]):
    """按用户账号集合过滤带 account_id 的查询。

    ``account_ids=None`` → 超管不限制; 空列表 → 强制空结果(``IN (-1)``)。
    """
    if account_ids is None:
        return stmt
    if not account_ids:
        return stmt.where(account_id_column.in_([-1]))
    return stmt.where(account_id_column.in_(account_ids))


def scope_by_owner(stmt, owner_column, current_user: dict | None):
    """按 owner_user_id 直接过滤自带归属列的表。超管不限制。"""
    if is_superadmin(current_user):
        return stmt
    uid = current_uid(current_user)
    if not uid:
        return stmt.where(owner_column.in_([-1]))
    return stmt.where(owner_column == uid)


async def assert_account_owned(
    db: AsyncSession, current_user: dict | None, account_id
) -> bool:
    """校验闲鱼账号是否归当前用户(超管恒真)。"""
    if is_superadmin(current_user):
        return True
    uid = current_uid(current_user)
    if not uid or account_id is None:
        return False
    row = (
        await db.execute(
            select(XianyuAccount.id).where(
                XianyuAccount.id == account_id,
                XianyuAccount.owner_user_id == uid,
            )
        )
    ).scalars().first()
    return row is not None
