"""QR login contract tests.

Covers the parts of the QR login flow that are guaranteed by construction:
- The optional mtop ``_m_h5_tk`` collection step degrades gracefully when
  upstream is slow or unreachable, rather than bubbling 502 to the client.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

import requests

from app.core import xianyu_qr_login


class _FakeResponse:
    def __init__(self, status_code: int = 200, text: str = "{}") -> None:
        self.status_code = status_code
        self.text = text
        self.headers: dict = {}


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


def _raise_timeout(*_args, **_kwargs):
    raise requests.exceptions.ReadTimeout("h5api.m.goofish.com read timed out")


class GetMH5TkContractTests(unittest.TestCase):
    def test_verification_required_remains_recoverable(self) -> None:
        self.assertFalse(
            xianyu_qr_login._is_terminal_session(
                {"status": "verification_required"}
            )
        )
        self.assertTrue(
            xianyu_qr_login._is_terminal_session({"status": "expired"})
        )

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
