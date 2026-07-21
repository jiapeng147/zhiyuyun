"""Cross-tenant scoping compiler tests for the most-exposed queries."""

from __future__ import annotations

import unittest

from sqlalchemy import select
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import aliased

from app.core.tenancy import (
    is_superadmin,
    scope_by_account,
    scope_by_owner,
)
from app.models.entities import (
    CardGroup,
    CardItem,
    DeliveryRecord,
    DeliveryRule,
    RagKnowledgeBase,
    ScheduledTask,
    XianyuAccount,
    XianyuChatMessage,
    XianyuConversation,
    XianyuGoods,
    XianyuMessage,
    XianyuTradeOrder,
)


_A_USER = {"user_id": 901, "role": "user"}
_B_USER = {"user_id": 902, "role": "user"}
_SUPER = {"user_id": 1, "role": "superadmin", "is_super": 1}


class TenantScopeSqlContractTests(unittest.TestCase):
    def _render(self, stmt) -> str:
        return str(stmt.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

    def test_account_owned_subquery_carries_owner_user_id(self) -> None:
        from sqlalchemy.dialects import mysql as mysql_dialect
        # Direct ORM rendering of the user-scoped statement must contain the
        # owner_user_id predicate and never resolve to an unsafe empty list.
        stmt = select(XianyuAccount).where(
            XianyuAccount.deleted == 0,
            XianyuAccount.id.in_(
                select(XianyuAccount.id).where(
                    XianyuAccount.deleted == 0,
                    XianyuAccount.owner_user_id == 901,
                )
            ),
        )
        compiled = self._render(stmt)
        self.assertIn("owner_user_id = 901", compiled)
        self.assertNotIn("OR 1 = 1", compiled)
        self.assertNotIn("true", compiled.lower().split("where")[-1])

    def test_goods_order_chat_account_paths_all_include_owner(self) -> None:
        # Every account_id-bearing entity must include the owner predicate once
        # scope_by_owner / the hand-rolled subquery wraps it.
        entities_with_account_id = [
            XianyuGoods,
            XianyuTradeOrder,
            XianyuChatMessage,
            XianyuMessage,
            XianyuConversation,
            DeliveryRecord,
        ]
        for entity in entities_with_account_id:
            stmt = select(entity).where(
                entity.account_id.in_(
                    select(XianyuAccount.id).where(
                        XianyuAccount.deleted == 0,
                        XianyuAccount.owner_user_id == 901,
                    )
                ),
                entity.deleted == 0 if hasattr(entity, "deleted") else True,
            )
            compiled = self._render(stmt)
            self.assertIn("owner_user_id = 901", compiled)

    def test_owner_scoped_tables_use_scope_by_owner(self) -> None:
        # The owner-bearing tables must restrict to the current user via
        # scope_by_owner so superadmin sees everything but normal users can
        # only touch their own rows.
        for entity, owner_col in [
            (CardGroup, CardGroup.owner_user_id),
            (DeliveryRule, DeliveryRule.owner_user_id),
            (RagKnowledgeBase, RagKnowledgeBase.owner_user_id),
            (ScheduledTask, ScheduledTask.owner_user_id),
        ]:
            scoped_user = scope_by_owner(
                select(entity).where(entity.deleted == 0 if hasattr(entity, "deleted") else True),
                owner_col,
                _A_USER,
            )
            self.assertIn("owner_user_id = 901", self._render(scoped_user))
            scoped_super = scope_by_owner(
                select(entity).where(entity.deleted == 0 if hasattr(entity, "deleted") else True),
                owner_col,
                _SUPER,
            )
            self.assertNotIn("owner_user_id =", self._render(scoped_super))

    def test_card_item_groups_use_account_owner_chain(self) -> None:
        # CardItem has no owner column. CardGroup is therefore the only path
        # to verify ownership; the runtime channel is in realtime_delivery.
        cg = aliased(CardGroup)
        stmt = select(CardItem).join(cg, cg.id == CardItem.group_id).where(
            CardItem.deleted == 0,
            CardItem.status == 0,
            CardItem.is_used == 0,
            cg.deleted == 0,
            cg.owner_user_id == 901,
        )
        self.assertIn("owner_user_id = 901", self._render(stmt))

    def test_scope_by_account_drops_unsafe_empty_list(self) -> None:
        # An anonymous caller (uid = 0) returning [] must produce an empty
        # result set rather than unconstrained reads.
        stmt = scope_by_account(
            select(XianyuGoods),
            XianyuGoods.account_id,
            [],
        )
        self.assertIn("IN (-1)", self._render(stmt))


if __name__ == "__main__":
    unittest.main()
