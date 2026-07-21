from __future__ import annotations

import asyncio
import datetime as dt
import unittest
from dataclasses import dataclass

from app.models.entities import CardItem, RealtimeDeliveryAttempt
from app.services.manual_delivery import (
    AttemptLease,
    DeliveryContext,
    ExternalStepResult,
    ManualDeliveryCommand,
    ManualDeliveryCoordinator,
)
from app.services.realtime_delivery import (
    ExternalDeliveryResult,
    RealtimeDeliveryAttemptLease,
    RealtimeDeliveryCommand,
    RealtimeDeliveryCoordinator,
    SqlRealtimeDeliveryStore,
)


class _Result:
    def __init__(self, *, scalar=None, rows=None):
        self._scalar = scalar
        self._rows = list(rows or [])

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return self

    def all(self):
        return list(self._rows)

    def mappings(self):
        return self

    def first(self):
        return self._rows[0] if self._rows else None


@dataclass
class _ManualState:
    lease: AttemptLease
    message_started: bool = False
    message_confirmed: bool = False
    platform_confirmed: bool = False


class _FakeManualStore:
    def __init__(self, context: DeliveryContext):
        self.state = _ManualState(
            lease=AttemptLease(
                attempt_id=1,
                idempotency_key="manual-key",
                state="pending",
                action="send_message",
                lease_token="lease-1",
                context=context,
                retry_safe=True,
                retry_scope="message",
            )
        )
        self.acquire_calls = 0

    async def acquire(self, order_id, command, idempotency_key, content_digest):
        self.acquire_calls += 1
        lease = self.state.lease
        if lease.state in {"success", "unknown"} or (
            lease.state == "failed" and not lease.retry_safe
        ):
            return AttemptLease(**{**lease.__dict__, "action": "return", "repeated": True})
        if lease.state == "message_sent":
            return AttemptLease(
                **{
                    **lease.__dict__,
                    "action": "confirm_platform",
                    "repeated": True,
                    "retry_scope": "platform_confirm",
                    "retry_safe": True,
                    "message_confirmed": True,
                }
            )
        return lease

    async def mark_message_started(self, lease):
        self.state.message_started = True

    async def mark_message_sent(self, lease):
        self.state.message_confirmed = True
        self.state.lease = AttemptLease(
            **{
                **lease.__dict__,
                "state": "message_sent",
                "action": "confirm_platform",
                "retry_scope": "platform_confirm",
                "retry_safe": True,
                "message_confirmed": True,
            }
        )
        return self.state.lease

    async def mark_failed(self, lease, result, *, retry_scope):
        self.state.lease = AttemptLease(
            **{
                **lease.__dict__,
                "state": "failed",
                "action": "return",
                "retry_scope": retry_scope,
                "retry_safe": result.retry_safe,
                "error_code": result.error_code,
                "error_message": result.message,
            }
        )
        return self.state.lease

    async def mark_unknown(self, lease, result, *, retry_scope):
        self.state.lease = AttemptLease(
            **{
                **lease.__dict__,
                "state": "unknown",
                "action": "return",
                "retry_scope": retry_scope,
                "retry_safe": False,
                "error_code": result.error_code,
                "error_message": result.message,
            }
        )
        return self.state.lease

    async def mark_platform_failed(self, lease, result):
        self.state.lease = AttemptLease(
            **{
                **lease.__dict__,
                "state": "message_sent",
                "action": "return",
                "retry_scope": "platform_confirm",
                "retry_safe": result.retry_safe,
                "error_code": result.error_code,
                "error_message": result.message,
                "message_confirmed": True,
            }
        )
        return self.state.lease

    async def mark_success(self, lease, command):
        self.state.lease = AttemptLease(
            **{
                **lease.__dict__,
                "state": "success",
                "action": "return",
                "retry_scope": None,
                "retry_safe": False,
                "platform_confirmed": True,
                "message_confirmed": True,
            }
        )
        return self.state.lease


class _FakeManualGateway:
    def __init__(self, message_results, platform_results):
        self.message_results = list(message_results)
        self.platform_results = list(platform_results)
        self.message_calls = 0
        self.platform_calls = 0

    async def send_message(self, context, content):
        self.message_calls += 1
        return self.message_results.pop(0)

    async def confirm_shipment(self, context):
        self.platform_calls += 1
        return self.platform_results.pop(0)


class _SharedCardInventory:
    def __init__(self, cards: list[CardItem]):
        self.cards = cards
        self.lock = asyncio.Lock()
        self.lock_owner = None

    async def claim_lock(self):
        await self.lock.acquire()
        self.lock_owner = asyncio.current_task()

    def release_lock(self):
        if self.lock_owner is asyncio.current_task():
            self.lock_owner = None
            self.lock.release()


class _RealtimeDb:
    """Small transaction double for the SQL store's card claim protocol."""

    def __init__(self, inventory: _SharedCardInventory, attempt: RealtimeDeliveryAttempt):
        self.inventory = inventory
        self.attempt = attempt

    async def execute(self, statement, *args, **kwargs):
        sql = str(statement)
        if "realtime_delivery_attempt" in sql:
            return _Result(scalar=self.attempt)
        if "card_group" in sql:
            return _Result(scalar=9)
        if "card_item" in sql:
            await self.inventory.claim_lock()
            if "WHERE card_item.realtime_attempt_id" in sql:
                rows = [
                    card
                    for card in self.inventory.cards
                    if card.realtime_attempt_id == self.attempt.id
                    and card.status == 1
                ]
            else:
                rows = [
                    card
                    for card in self.inventory.cards
                    if card.group_id == 9
                    and card.deleted == 0
                    and card.status == 0
                    and card.is_used == 0
                ]
            return _Result(rows=rows[:2])
        if "delivery_record" in sql:
            return _Result(scalar=None)
        raise AssertionError(f"unexpected SQL in test double: {sql}")

    async def commit(self):
        self.inventory.release_lock()

    async def rollback(self):
        self.inventory.release_lock()


def _delivery_attempt(attempt_id: int) -> RealtimeDeliveryAttempt:
    return RealtimeDeliveryAttempt(
        id=attempt_id,
        event_key=f"event-{attempt_id}",
        account_id=10,
        external_order_id="order-1",
        source_event_id="source-1",
        session_id="session-1",
        peer_id="buyer-1",
        item_id="item-1",
        delivery_mode="card",
        content_digest="digest",
        quantity_requested=2,
        card_group_id=9,
        state="pending",
        retry_scope="message",
        retry_safe=1,
        attempt_count=1,
        lease_token=f"lease-{attempt_id}",
        lease_until=dt.datetime.now() + dt.timedelta(seconds=30),
    )


def _delivery_lease(attempt: RealtimeDeliveryAttempt) -> RealtimeDeliveryAttemptLease:
    return RealtimeDeliveryAttemptLease(
        attempt_id=attempt.id,
        event_key=attempt.event_key,
        state="pending",
        action="send_message",
        lease_token=attempt.lease_token,
        account_id=attempt.account_id,
        external_order_id=attempt.external_order_id,
        session_id=attempt.session_id,
        peer_id=attempt.peer_id,
        item_id=attempt.item_id,
        delivery_mode="card",
        quantity_requested=2,
        auto_confirm_shipment=False,
        retry_safe=True,
        retry_scope="message",
    )


class ManualDeliveryContractTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.context = DeliveryContext(
            order_id=7,
            external_order_id="remote-order-7",
            account_id=10,
            buyer_id="buyer-1",
            item_id="item-1",
            session_id="session-1",
            peer_id="buyer-1",
        )
        self.command = ManualDeliveryCommand(
            delivery_mode="text",
            delivery_content="已发货",
            quantity_requested=1,
            idempotency_key="manual-key",
        )

    async def test_idempotent_success_does_not_send_twice(self):
        store = _FakeManualStore(self.context)
        gateway = _FakeManualGateway(
            [ExternalStepResult.confirmed()],
            [ExternalStepResult.confirmed()],
        )
        coordinator = ManualDeliveryCoordinator(store=store, gateway=gateway)

        first = await coordinator.execute(7, self.command)
        second = await coordinator.execute(7, self.command)

        self.assertEqual(first.status, "success")
        self.assertTrue(second.repeated)
        self.assertEqual(gateway.message_calls, 1)
        self.assertEqual(gateway.platform_calls, 1)

    async def test_platform_retry_does_not_resend_message(self):
        store = _FakeManualStore(self.context)
        gateway = _FakeManualGateway(
            [ExternalStepResult.confirmed()],
            [
                ExternalStepResult.failed(
                    "platform_busy",
                    "平台暂时繁忙",
                    retry_safe=True,
                ),
                ExternalStepResult.confirmed(),
            ],
        )
        coordinator = ManualDeliveryCoordinator(store=store, gateway=gateway)

        first = await coordinator.execute(7, self.command)
        second = await coordinator.execute(7, self.command)

        self.assertEqual(first.status, "message_sent")
        self.assertTrue(first.retry_safe)
        self.assertEqual(second.status, "success")
        self.assertEqual(gateway.message_calls, 1)
        self.assertEqual(gateway.platform_calls, 2)

    async def test_unknown_message_result_is_not_automatically_retried(self):
        store = _FakeManualStore(self.context)
        gateway = _FakeManualGateway(
            [],
            [],
        )

        class UnknownGateway(_FakeManualGateway):
            async def send_message(self, context, content):
                self.message_calls += 1
                return ExternalStepResult.unknown("ack_unknown", "结果未知")

        gateway = UnknownGateway([], [])
        coordinator = ManualDeliveryCoordinator(store=store, gateway=gateway)
        first = await coordinator.execute(7, self.command)
        second = await coordinator.execute(7, self.command)

        self.assertEqual(first.status, "unknown")
        self.assertFalse(first.retry_safe)
        self.assertTrue(second.repeated)
        self.assertEqual(gateway.message_calls, 1)


class RealtimeDeliveryContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_card_claim_only_consumes_available_inventory(self):
        cards = [
            CardItem(id=1, group_id=9, card_key="A", status=0, is_used=0, deleted=0),
            CardItem(id=2, group_id=9, card_key="B", status=0, is_used=0, deleted=0),
            CardItem(id=3, group_id=9, card_key="C", status=0, is_used=0, deleted=0),
        ]
        inventory = _SharedCardInventory(cards)
        attempt_a = _delivery_attempt(1)
        attempt_b = _delivery_attempt(2)
        store_a = SqlRealtimeDeliveryStore(_RealtimeDb(inventory, attempt_a))
        store_b = SqlRealtimeDeliveryStore(_RealtimeDb(inventory, attempt_b))
        command = RealtimeDeliveryCommand(
            event_key="event",
            account_id=10,
            external_order_id="order-1",
            source_event_id="source-1",
            session_id="session-1",
            peer_id="buyer-1",
            item_id="item-1",
            rule_id=1,
            delivery_mode="card",
            delivery_content="{卡密}",
            quantity_requested=2,
            card_group_id=9,
            auto_confirm_shipment=False,
        )

        prepared_a, prepared_b = await asyncio.gather(
            store_a.prepare_message(_delivery_lease(attempt_a), command),
            store_b.prepare_message(_delivery_lease(attempt_b), command),
        )

        self.assertEqual(prepared_a.status, "ready")
        self.assertEqual(prepared_b.status, "failed")
        self.assertEqual(prepared_b.error_code, "card_inventory_insufficient")
        self.assertEqual(
            sorted(card.status for card in cards),
            [0, 1, 1],
        )
        self.assertEqual(
            sorted(card.realtime_attempt_id for card in cards if card.status == 1),
            [1, 1],
        )

    async def test_message_failure_releases_claimed_cards(self):
        cards = [
            CardItem(id=1, group_id=9, card_key="A", status=0, is_used=0, deleted=0),
            CardItem(id=2, group_id=9, card_key="B", status=0, is_used=0, deleted=0),
        ]
        inventory = _SharedCardInventory(cards)
        attempt = _delivery_attempt(1)
        db = _RealtimeDb(inventory, attempt)
        store = SqlRealtimeDeliveryStore(db)
        command = RealtimeDeliveryCommand(
            event_key="event-1",
            account_id=10,
            external_order_id="order-1",
            source_event_id="source-1",
            session_id="session-1",
            peer_id="buyer-1",
            item_id="item-1",
            rule_id=1,
            delivery_mode="card",
            delivery_content="{卡密}",
            quantity_requested=2,
            card_group_id=9,
            auto_confirm_shipment=False,
        )

        prepared = await store.prepare_message(_delivery_lease(attempt), command)
        self.assertEqual(prepared.status, "ready")
        await store.mark_message_failed(
            _delivery_lease(attempt),
            ExternalDeliveryResult.failed(
                "websocket_unavailable",
                "连接不可用",
                retry_safe=True,
            ),
        )

        self.assertEqual([card.status for card in cards], [0, 0])
        self.assertEqual([card.realtime_attempt_id for card in cards], [None, None])
