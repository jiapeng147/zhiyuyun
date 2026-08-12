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
    def __init__(
        self,
        payload: dict,
        *,
        redirect_uid: str = "fixture-unb",
        has_login_uid: str = "",
        token_login_uid: str = "",
        nav_uid: str = "",
        verification_code: str = "0",
        verification_callback_uid: str = "",
    ) -> None:
        self.cookies: dict = {}
        self.payload = payload
        self.redirect_visited = False
        self.redirect_uid = redirect_uid
        self.has_login_uid = has_login_uid
        self.token_login_uid = token_login_uid
        self.nav_uid = nav_uid
        self.verification_code = verification_code
        self.verification_callback_uid = verification_callback_uid
        self.token_login_visited = False
        self.nav_visited = False
        self.query_params: dict = {}

    def post(self, url="", *_args, **kwargs):
        if "login_token/login.do" in str(url):
            self.token_login_visited = True
            if self.token_login_uid:
                self.cookies["unb"] = self.token_login_uid
            return _FakeResponse(200, text=json.dumps({"content": {"data": {"loginResult": "success"}}}))
        if "hasLogin.do" in str(url):
            text = json.dumps(
                {"success": True, "userId": self.has_login_uid},
                ensure_ascii=False,
            )
            return _FakeResponse(200, text=text)
        if "mtop.idle.web.user.page.nav" in str(url):
            self.nav_visited = True
            text = json.dumps(
                {
                    "ret": ["SUCCESS::调用成功"],
                    "data": {"userId": self.nav_uid},
                },
                ensure_ascii=False,
            )
            return _FakeResponse(200, text=text)
        self.query_params = dict(kwargs.get("params") or {})
        text = json.dumps(
            {"content": {"data": self.payload}},
            ensure_ascii=False,
        )
        return _FakeResponse(200, text=text)

    def get(self, url="", *_args, **_kwargs):
        self.redirect_visited = True
        if "photoVerify/check.do" in str(url):
            callback_url = (
                "https://passport.goofish.com/iv/ivCheckLogin.htm"
                if self.verification_code == "3"
                else ""
            )
            return _FakeResponse(
                200,
                text=json.dumps(
                    {"content": {"code": self.verification_code, "url": callback_url}}
                ),
                url=str(url),
            )
        if "ivCheckLogin.htm" in str(url):
            if self.verification_callback_uid:
                self.cookies["unb"] = self.verification_callback_uid
            return _FakeResponse(200, text="ok", url=str(url))
        if self.redirect_uid:
            self.cookies["unb"] = self.redirect_uid
        return _FakeResponse(
            200,
            text=(
                'window.location.href="https://passport.goofish.com/iv/mini/verify_modes.htm?htoken=verify-token&_umidfg=";'
                if str(url).rstrip("/") == "https://passport.goofish.com/verify"
                else 'new Qrcode({ text: "https://passport.goofish.com/iv/face-qr" });'
            ),
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

    def test_confirmed_payload_user_id_alone_does_not_forge_login_cookie(self) -> None:
        session = _FakeQrQuerySession(
            {
                "qrCodeStatus": "CONFIRMED",
                "userId": "2200000012345",
            },
            redirect_uid="",
        )
        result = xianyu_qr_login._poll_status_once(session, {})
        self.assertEqual(result["status"], "failed")
        self.assertNotIn("unb", session.cookies)

    def test_verification_payload_user_id_is_used_when_redirect_lacks_unb(self) -> None:
        session = _FakeQrQuerySession(
            {
                "qrCodeStatus": "CONFIRMED",
                "iframeRedirect": True,
                "iframeRedirectUrl": "https://passport.goofish.com/verify",
                "userId": "2200000012345",
            },
            redirect_uid="",
            verification_code="3",
            verification_callback_uid="2200000012345",
        )
        result = xianyu_qr_login._poll_status_once(session, {})
        self.assertTrue(session.redirect_visited)
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["cookies"]["unb"], "2200000012345")

    def test_verification_pending_exposes_second_qr_when_required(self) -> None:
        session = _FakeQrQuerySession(
            {
                "qrCodeStatus": "CONFIRMED",
                "iframeRedirect": True,
                "iframeRedirectUrl": "https://passport.goofish.com/verify",
            },
            redirect_uid="",
            verification_code="0",
        )
        result = xianyu_qr_login._poll_status_once(session, {})
        self.assertEqual(result["status"], "verification_required")
        self.assertTrue(result["faceQrImage"].startswith("data:image/png;base64,"))

    def test_confirmed_has_login_user_id_is_used_when_cookie_lacks_unb(self) -> None:
        session = _FakeQrQuerySession(
            {"qrCodeStatus": "CONFIRMED"},
            redirect_uid="",
            has_login_uid="2200000012345",
        )
        result = xianyu_qr_login._poll_status_once(session, {"appName": "xianyu"})
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["cookies"]["unb"], "2200000012345")

    def test_confirmed_login_token_is_exchanged_before_persisting(self) -> None:
        session = _FakeQrQuerySession(
            {"qrCodeStatus": "CONFIRMED", "token": "confirmed-token"},
            redirect_uid="",
            token_login_uid="2200000012345",
        )
        result = xianyu_qr_login._poll_status_once(session, {"appName": "xianyu"})
        self.assertTrue(session.token_login_visited)
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["cookies"]["unb"], "2200000012345")

    def test_generated_lg_token_is_exchanged_when_confirm_payload_omits_token(self) -> None:
        session = _FakeQrQuerySession(
            {"qrCodeStatus": "CONFIRMED"},
            redirect_uid="",
            token_login_uid="2200000012345",
        )
        result = xianyu_qr_login._poll_status_once(
            session,
            {"appName": "xianyu", "lgToken": "generated-token"},
        )
        self.assertTrue(session.token_login_visited)
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["cookies"]["unb"], "2200000012345")

    def test_confirmed_user_nav_id_is_used_when_token_exchange_lacks_uid(self) -> None:
        session = _FakeQrQuerySession(
            {"qrCodeStatus": "CONFIRMED"},
            redirect_uid="",
            has_login_uid="",
            nav_uid="2200000012345",
        )
        session.cookies["_m_h5_tk"] = "token_fixture_123"
        result = xianyu_qr_login._poll_status_once(session, {"appName": "xianyu"})
        self.assertTrue(session.nav_visited)
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["cookies"]["unb"], "2200000012345")

    def test_qr_query_uses_current_passport_site_parameters(self) -> None:
        session = _FakeQrQuerySession({"qrCodeStatus": "NEW"}, redirect_uid="")
        result = xianyu_qr_login._poll_status_once(session, {})
        self.assertEqual(result["status"], "new")
        self.assertEqual(session.query_params, {"appName": "xianyu", "fromSite": "77"})

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
