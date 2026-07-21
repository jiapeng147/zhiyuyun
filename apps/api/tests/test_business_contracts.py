from __future__ import annotations

import asyncio
import json
import unittest
from unittest.mock import AsyncMock, patch

from sqlalchemy import select
from sqlalchemy.dialects import mysql

from app.core.tenancy import scope_by_owner
from app.core.xianyu_qr_login import _poll_status_once, _qr_status_result
from app.models.entities import RagKnowledgeBase
from app.services import ai_provider
from app.services.ai_reply_batcher import AiAutoReplyBatcher
from app.services.ws_delivery_handler import _delivery_rule_match_rank
from app.services.ws_storage import stable_chat_message_uid
from app.services.xianyu_goods_sync import _parse_card_to_goods, _parse_item_status
from app.services.xianyu_order_sync import (
    ORDER_STATUS_UNKNOWN,
    _map_order_status,
    _parse_remote_order_item,
)


class _FakeProviderResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class _FakeQrResponse:
    def __init__(self, status: str) -> None:
        self.status_code = 200
        self.headers = {"content-type": "application/json"}
        self._status = status

    @property
    def text(self) -> str:
        return json.dumps(
            {"content": {"data": {"qrCodeStatus": self._status}}},
            ensure_ascii=False,
        )

    def json(self) -> dict:
        return json.loads(self.text)


class _FakeQrSession:
    def __init__(self, status: str) -> None:
        self.cookies = {"unb": "fixture-user"}
        self.status = status

    def post(self, *_args, **_kwargs):
        return _FakeQrResponse(self.status)


class BusinessContractTests(unittest.TestCase):
    def test_unknown_order_status_is_quarantined(self) -> None:
        self.assertEqual(_map_order_status("new-platform-state"), ORDER_STATUS_UNKNOWN)
        self.assertEqual(_map_order_status({"code": "future_status"}), ORDER_STATUS_UNKNOWN)
        self.assertEqual(_map_order_status("退款中"), 2)
        self.assertEqual(_map_order_status("退款成功"), 5)

    def test_order_fixture_preserves_multiple_skus(self) -> None:
        parsed = _parse_remote_order_item(
            {
                "commonData": {
                    "orderId": "order-fixture-1",
                    "orderStatus": "已付款",
                    "itemId": "10001",
                },
                "buyerInfoVO": {"buyerId": "buyer-1", "userNick": "买家"},
                "priceVO": {"buyNum": 3, "unitPrice": "10.00", "totalPrice": "30.00"},
                "itemInfoVO": {
                    "title": "组合商品",
                    "skuList": [
                        {
                            "itemId": "10001",
                            "skuId": "red",
                            "skuName": "红色",
                            "quantity": 2,
                            "unitPrice": "10.00",
                        },
                        {
                            "itemId": "10001",
                            "skuId": "blue",
                            "skuName": "蓝色",
                            "quantity": 1,
                            "unitPrice": "10.00",
                        },
                    ],
                },
            }
        )
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["order_status"], 1)
        self.assertEqual(sum(item["quantity"] for item in parsed["items"]), 3)
        self.assertEqual(
            [(item["sku_id"], item["sku_name"]) for item in parsed["items"]],
            [("red", "红色"), ("blue", "蓝色")],
        )

    def test_goods_status_requires_positive_evidence(self) -> None:
        current = _parse_card_to_goods(
            {
                "id": "10001",
                "itemStatus": 0,
                "priceInfo": {"price": "10"},
                "picInfo": {"picUrl": "https://img.example/item.jpg"},
            },
            7,
        )
        legacy = _parse_card_to_goods(
            {"id": "10002", "status": 1, "title": "legacy"},
            7,
        )
        unknown = _parse_card_to_goods(
            {"id": "10003", "itemStatus": 99, "title": "future"},
            7,
        )
        self.assertEqual(current["status"], 0)
        self.assertEqual(current["raw_payload"]["_statusEvidence"], "current_numeric")
        self.assertEqual(legacy["status"], 0)
        self.assertEqual(legacy["raw_payload"]["_statusEvidence"], "legacy_numeric")
        self.assertEqual(unknown["status"], 1)
        self.assertEqual(unknown["raw_payload"]["_statusEvidence"], "current_numeric")
        self.assertEqual(_parse_item_status({}), (1, "status_missing_or_unknown"))

    def test_delivery_wildcard_precedence_and_rejection(self) -> None:
        exact = _delivery_rule_match_rank(
            {"id": 1, "account_id": 10, "goods_id": 88, "trigger_keyword": ""},
            account_id=10,
            local_goods_id=88,
            external_id="10001",
            goods_title="数字商品",
        )
        wildcard = _delivery_rule_match_rank(
            {
                "id": 2,
                "account_id": 10,
                "goods_id": None,
                "trigger_keyword": "100*",
            },
            account_id=10,
            local_goods_id=88,
            external_id="10001",
            goods_title="数字商品",
        )
        rejected = _delivery_rule_match_rank(
            {
                "id": 3,
                "account_id": 10,
                "goods_id": None,
                "trigger_keyword": "200*",
            },
            account_id=10,
            local_goods_id=88,
            external_id="10001",
            goods_title="数字商品",
        )
        self.assertEqual(exact[0], 0)
        self.assertEqual(wildcard[0], 1)
        self.assertIsNone(rejected)

    def test_tenant_scope_has_owner_predicate(self) -> None:
        statement = scope_by_owner(
            select(RagKnowledgeBase).where(RagKnowledgeBase.deleted == 0),
            RagKnowledgeBase.owner_user_id,
            {"user_id": 17, "role": "user"},
        )
        compiled = str(statement.compile(dialect=mysql.dialect()))
        self.assertIn("owner_user_id", compiled)
        self.assertIn("deleted", compiled)

    def test_qr_status_machine_has_explicit_states(self) -> None:
        self.assertEqual(
            _qr_status_result("new", "等待扫码", "NEW"),
            {"status": "new", "message": "等待扫码", "rawStatus": "NEW"},
        )
        self.assertEqual(
            _qr_status_result(
                "verification_required",
                "需要验证",
                "CONFIRMED",
                iframe_redirect_url="https://passport.goofish.com/verify",
            )["status"],
            "verification_required",
        )
        self.assertEqual(
            _poll_status_once(_FakeQrSession("SCANNED"), {}),
            {
                "status": "scanned",
                "message": "已扫码，请在闲鱼 App 点击确认登录。",
                "rawStatus": "SCANNED",
            },
        )
        confirmed = _poll_status_once(_FakeQrSession("CONFIRMED"), {})
        self.assertEqual(confirmed["status"], "confirmed")
        self.assertEqual(confirmed["cookies"]["unb"], "fixture-user")

    def test_repeated_text_uses_time_or_sequence_evidence(self) -> None:
        base = {
            "sId": "sid-1",
            "senderUserId": "buyer-1",
            "receiverUserId": "seller-1",
            "msgContent": "还在吗",
            "direction": "IN",
            "messageTime": 1000,
            "pnmId": "pnm-1",
        }
        replay = {**base, "pnmId": "pnm-2"}
        later = {**base, "pnmId": "pnm-3", "messageTime": 2000}
        no_time_a = {**base, "pnmId": "pnm-4", "messageTime": 0}
        no_time_b = {**base, "pnmId": "pnm-5", "messageTime": 0}
        self.assertIsNotNone(AiAutoReplyBatcher._semantic_fingerprint(base))
        self.assertEqual(
            AiAutoReplyBatcher._semantic_fingerprint(base),
            AiAutoReplyBatcher._semantic_fingerprint(replay),
        )
        self.assertNotEqual(
            AiAutoReplyBatcher._semantic_fingerprint(base),
            AiAutoReplyBatcher._semantic_fingerprint(later),
        )
        self.assertIsNone(AiAutoReplyBatcher._semantic_fingerprint(no_time_a))
        self.assertIsNone(AiAutoReplyBatcher._semantic_fingerprint(no_time_b))

    def test_stable_uid_keeps_outbound_echo_and_separates_inbound_repeats(self) -> None:
        outbound = {
            "sId": "sid-1",
            "senderUserId": "seller-1",
            "receiverUserId": "buyer-1",
            "direction": "OUT",
            "msgContent": "你好",
            "messageTime": 0,
        }
        outbound_echo = {**outbound, "messageTime": 2000}
        inbound_a = {
            **outbound,
            "direction": "IN",
            "senderUserId": "buyer-1",
            "receiverUserId": "seller-1",
            "messageTime": 1000,
        }
        inbound_b = {**inbound_a, "messageTime": 2001}
        self.assertEqual(
            stable_chat_message_uid(outbound),
            stable_chat_message_uid(outbound_echo),
        )
        self.assertNotEqual(
            stable_chat_message_uid(inbound_a),
            stable_chat_message_uid(inbound_b),
        )


class AsyncBusinessContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_batcher_deduplicates_replay_but_allows_later_same_text(self) -> None:
        handled: list[list[dict]] = []

        async def handler(_account_id: int, messages: list[dict], _seller: str) -> None:
            handled.append(messages)

        batcher = AiAutoReplyBatcher(handler, delay_seconds=0)
        first = {
            "sId": "sid-1",
            "senderUserId": "buyer-1",
            "msgContent": "还在吗",
            "pnmId": "pnm-1",
            "messageTime": 1000,
        }
        replay = {**first, "pnmId": "pnm-2"}
        later = {**first, "pnmId": "pnm-3", "messageTime": 2000}
        self.assertTrue(batcher.enqueue(1, first, "seller"))
        self.assertFalse(batcher.enqueue(1, replay, "seller"))
        self.assertTrue(batcher.enqueue(1, later, "seller"))
        await batcher.drain()
        await batcher.shutdown()
        self.assertEqual(len(handled), 1)
        self.assertEqual(
            [item["pnmId"] for item in handled[0]],
            ["pnm-1", "pnm-3"],
        )

    async def test_ai_chat_completions_contract(self) -> None:
        response = _FakeProviderResponse(
            {"choices": [{"message": {"content": "你好，欢迎咨询"}}]}
        )
        config = {
            "base_url": "https://relay.example.test/v1",
            "api_key": "fixture-key",
            "model": "fixture-chat",
            "enabled": True,
            "source": "test",
            "request_timeout": 5,
            "api_mode": "chat_completions",
        }
        transport = AsyncMock(return_value=response)
        with patch.object(ai_provider, "_resolve_ai_config", new=AsyncMock(return_value=config)), patch.object(
            ai_provider, "request_public_https", new=transport
        ):
            result = await ai_provider.generate_text(
                "test",
                "",
                "请问还在吗",
                messages=[{"role": "user", "content": "请问还在吗"}],
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["content"], "你好，欢迎咨询")
        payload = json.loads(transport.await_args.kwargs["content"].decode("utf-8"))
        self.assertEqual(payload["messages"][0]["content"], "请问还在吗")

    async def test_ai_responses_contract(self) -> None:
        response = _FakeProviderResponse({"output_text": "可以，马上为你处理"})
        config = {
            "base_url": "https://relay.example.test/v1",
            "api_key": "fixture-key",
            "model": "fixture-responses",
            "enabled": True,
            "source": "test",
            "request_timeout": 5,
            "api_mode": "responses",
        }
        transport = AsyncMock(return_value=response)
        with patch.object(ai_provider, "_resolve_ai_config", new=AsyncMock(return_value=config)), patch.object(
            ai_provider, "request_public_https", new=transport
        ):
            result = await ai_provider.generate_text(
                "test",
                "你是客服",
                "",
                messages=[{"role": "user", "content": "帮我查一下"}],
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["content"], "可以，马上为你处理")
        payload = json.loads(transport.await_args.kwargs["content"].decode("utf-8"))
        self.assertEqual(payload["input"], "帮我查一下")
        self.assertEqual(payload["instructions"], "你是客服")
