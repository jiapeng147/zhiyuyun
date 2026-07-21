"""QR login contract tests.

Covers the parts of the QR login flow that are guaranteed by construction:
- The optional mtop ``_m_h5_tk`` collection step degrades gracefully when
  upstream is slow or unreachable, rather than bubbling 502 to the client.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch
import json

import requests

from app.core import xianyu_qr_login


class _FakeResponse:
    def __init__(
        self,
        status_code: int = 200,
        text: str = "{}",
        url: str = "https://passport.goofish.com/",
    ) -> None:
        self.status_code = status_code
        self.text = text
        self.url = url
        self.headers: dict = {"content-type": "application/json"}

    def json(self) -> dict:
        return json.loads(self.text or "{}")


class _FakeSession:
    """Minimal session double. Forwards HTTP calls through the patched
    ``xianyu_qr_login.requests.get/post`` so each test can override at the
    boundary instead of binding methods here."""

    def __init__(self) -> None:
        self.cookies: dict = {}

    def get(self, *args, **kwargs):
        return xianyu_qr_login.requests.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return xianyu_qr_login.requests.post(*args, **kwargs)

    def close(self) -> None:
        return None


class _FakeQrGenerateSession:
    def __init__(self) -> None:
        self.cookies: dict = {}

    def get(self, *_args, **_kwargs):
        return _FakeResponse(
            200,
            text=json.dumps(
                {
                    "content": {
                        "data": {
                            "t": 1234567890,
                            "ck": "ck-fixture",
                            "codeContent": (
                                "https://passport.goofish.com/qrcodeCheck.htm"
                                "?lgToken=token_fixture_0000000&_from=havana"
                            ),
                        }
                    },
                    "hasError": False,
                }
            ),
        )


class _FakeQrQuerySession:
    def __init__(self, payload: dict, *, redirect_uid: str = "fixture-unb") -> None:
        self.cookies: dict = {}
        self.payload = payload
        self.redirect_visited = False
        self.redirect_uid = redirect_uid

    def post(self, *_args, **_kwargs):
        text = json.dumps(
            {"content": {"data": self.payload}},
            ensure_ascii=False,
        )
        return _FakeResponse(200, text=text)

    def get(self, *_args, **_kwargs):
        self.redirect_visited = True
        if self.redirect_uid:
            self.cookies["unb"] = self.redirect_uid
        return _FakeResponse(
            200,
            text="ok",
            url="https://passport.goofish.com/callback",
        )


def _raise_timeout(*_args, **_kwargs):
    raise requests.exceptions.ReadTimeout("h5api.m.goofish.com read timed out")


class GetMH5TkContractTests(unittest.TestCase):
    def test_generate_qrcode_preserves_login_form_for_polling(self) -> None:
        form = {"appName": "xianyu", "_csrf_token": "csrf-fixture"}
        qr = xianyu_qr_login._generate_qrcode(_FakeQrGenerateSession(), form)
        self.assertTrue(qr.startswith("data:image/png;base64,"))
        self.assertEqual(form["appName"], "xianyu")
        self.assertEqual(form["_csrf_token"], "csrf-fixture")
        self.assertEqual(form["lgToken"], "token_fixture_0000000")
        self.assertEqual(form["ck"], "ck-fixture")
        self.assertEqual(form["defaultCheck"], "1")

    def test_verification_required_remains_recoverable(self) -> None:
        self.assertFalse(
            xianyu_qr_login._is_terminal_session(
                {"status": "verification_required"}
            )
        )
        self.assertTrue(
            xianyu_qr_login._is_terminal_session({"status": "expired"})
        )

    def test_confirmed_verification_redirect_can_persist_cookies(self) -> None:
        session = _FakeQrQuerySession(
            {
                "qrCodeStatus": "CONFIRMED",
                "iframeRedirect": True,
                "iframeRedirectUrl": "https://passport.goofish.com/verify",
            }
        )
        result = xianyu_qr_login._poll_status_once(session, {})
        self.assertTrue(session.redirect_visited)
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["cookies"]["unb"], "fixture-unb")

    def test_confirmed_payload_user_id_is_used_when_cookie_lacks_unb(self) -> None:
        session = _FakeQrQuerySession(
            {
                "qrCodeStatus": "CONFIRMED",
                "userId": "2200000012345",
            }
        )
        result = xianyu_qr_login._poll_status_once(session, {})
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["cookies"]["unb"], "2200000012345")

    def test_verification_payload_user_id_is_used_when_redirect_lacks_unb(self) -> None:
        session = _FakeQrQuerySession(
            {
                "qrCodeStatus": "CONFIRMED",
                "iframeRedirect": True,
                "iframeRedirectUrl": "https://passport.goofish.com/verify",
                "userId": "2200000012345",
            },
            redirect_uid="",
        )
        result = xianyu_qr_login._poll_status_once(session, {})
        self.assertTrue(session.redirect_visited)
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["cookies"]["unb"], "2200000012345")

    def test_expired_after_confirm_uses_existing_cookies(self) -> None:
        session = _FakeQrQuerySession({"qrCodeStatus": "EXPIRED"})
        session.cookies["unb"] = "fixture-unb"
        result = xianyu_qr_login._poll_status_once(session, {})
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["rawStatus"], "EXPIRED")

    def test_expired_during_verification_window_stays_recoverable(self) -> None:
        session = _FakeQrQuerySession({"qrCodeStatus": "EXPIRED"}, redirect_uid="")
        xianyu_qr_login._set_verification_redirect_state(
            session,
            "https://passport.goofish.com/verify",
        )
        result = xianyu_qr_login._poll_status_once(session, {})
        self.assertTrue(session.redirect_visited)
        self.assertEqual(result["status"], "verification_required")
        self.assertEqual(result["rawStatus"], "EXPIRED")

    def test_expired_during_verification_window_can_finish_after_app_auth(self) -> None:
        session = _FakeQrQuerySession(
            {"qrCodeStatus": "EXPIRED"},
            redirect_uid="2200000012345",
        )
        xianyu_qr_login._set_verification_redirect_state(
            session,
            "https://passport.goofish.com/verify",
        )
        result = xianyu_qr_login._poll_status_once(session, {})
        self.assertTrue(session.redirect_visited)
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["cookies"]["unb"], "2200000012345")

    def test_returns_empty_on_timeout_without_raising(self) -> None:
        fake = _FakeSession()
        with patch.object(xianyu_qr_login.requests, "get", _raise_timeout), patch.object(
            xianyu_qr_login.requests, "post", _raise_timeout
        ):
            try:
                result = xianyu_qr_login._get_m_h5_tk(fake)
            except Exception as exc:
                self.fail(f"_get_m_h5_tk raised on timeout: {exc!r}")
            self.assertEqual(result, "")

    def test_returns_empty_on_runtime_error(self) -> None:
        """If upstream returns 200 but no _m_h5_tk cookie, the function
        must return empty rather than raising."""

        def _ok_post(*_args, **_kwargs):
            return _FakeResponse()

        def _ok_get(*_args, **_kwargs):
            return _FakeResponse()

        fake = _FakeSession()
        with patch.object(xianyu_qr_login.requests, "get", _ok_get), patch.object(
            xianyu_qr_login.requests, "post", _ok_post
        ):
            try:
                result = xianyu_qr_login._get_m_h5_tk(fake)
            except Exception as exc:
                self.fail(f"_get_m_h5_tk raised unexpectedly: {exc!r}")
            self.assertEqual(result, "")

    def test_returns_cookie_when_present(self) -> None:
        def _post_with_cookie(*_args, **_kwargs):
            return _FakeResponse(200, text="{}")

        def _ok_get(*_args, **_kwargs):
            return _FakeResponse()

        fake = _FakeSession()
        fake.cookies["_m_h5_tk"] = "99999_tokenvalue"
        with patch.object(xianyu_qr_login.requests, "get", _ok_get), patch.object(
            xianyu_qr_login.requests, "post", _post_with_cookie
        ):
            try:
                result = xianyu_qr_login._get_m_h5_tk(fake)
            except Exception as exc:
                self.fail(f"_get_m_h5_tk raised unexpectedly: {exc!r}")
            self.assertEqual(result, "99999_tokenvalue")


if __name__ == "__main__":
    unittest.main()
