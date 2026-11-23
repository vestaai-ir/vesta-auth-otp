# Copyright 2026 Vesta AI (https://vestaai.ir)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import json
from contextlib import contextmanager
from unittest.mock import patch
from urllib.parse import urlsplit

import requests

from odoo.addons.vesta_marketing.tools import smsir
from odoo.addons.vesta_marketing.tools.sms_api import PARAM_API_KEY, PARAM_LINE
from odoo.tests import HOST

from ..models.vesta_auth_otp import PARAM
from ..tools import bale

SMSIR_KEY = "test-smsir-key"
SMSIR_LINE = "30004505000017"
BALE_KEY = "test-bale-key"
BALE_BOT = "4242"


class FakeResponse:
    def __init__(self, body, status_code=200):
        self.status_code = status_code
        self.ok = status_code < 400
        self._body = body

    def json(self):
        if isinstance(self._body, str):
            return json.loads(self._body)
        return self._body


class OtpMockMixin:
    """sms.ir and Bale answer from these mocks; anything else that tries the network is recorded."""

    @classmethod
    def _otp_setup_settings(cls, env, **overrides):
        params = env["ir.config_parameter"].sudo()
        values = {
            "enabled": True,
            "test_mode": False,
            "sms_enabled": True,
            "bale_enabled": True,
            "bale_api_key": BALE_KEY,
            "bale_bot_id": BALE_BOT,
            "resend_delay": 60,
            "phone_limit": 5,
            "ip_limit": 20,
            "max_attempts": 5,
            "expiry": 120,
            "code_length": 6,
        }
        values.update(overrides)
        for key, value in values.items():
            if isinstance(value, bool):
                params.set_bool(PARAM + key, value)
            elif isinstance(value, int):
                params.set_int(PARAM + key, value)
            else:
                params.set_str(PARAM + key, value)
        params.set_str(PARAM_API_KEY, SMSIR_KEY)
        params.set_str(PARAM_LINE, SMSIR_LINE)

    def _otp_reset_mocks(self):
        self.smsir_calls = []
        self.bale_calls = []
        self.network_calls = []
        self.bale_answer = lambda payload: FakeResponse({"message_id": "bale-1", "error_data": []})
        self.smsir_answer = self._smsir_default_answer

    def _smsir_default_answer(self, method, path, payload):
        if path == "/send/likeToLike":
            return FakeResponse({"status": 1, "message": "موفق", "data": {"packId": "p1", "messageIds": [7001]}})
        if path == "/send/bulk":
            ids = list(range(8000, 8000 + len(payload["mobiles"])))
            return FakeResponse({"status": 1, "message": "موفق", "data": {"packId": "p2", "messageIds": ids}})
        if path == "/send/verify":
            return FakeResponse({"status": 1, "message": "موفق", "data": {"messageId": 9001, "cost": 1.0}})
        return FakeResponse({"status": 0, "message": "not found", "data": None}, 404)

    @contextmanager
    def mock_channels(self):
        test = self

        def fake_smsir(method, url, json=None, headers=None, timeout=None):
            test.assertTrue(url.startswith(smsir.API_URL), url)
            path = url[len(smsir.API_URL) :]
            test.smsir_calls.append(
                {"method": method, "path": path, "payload": json, "headers": headers, "timeout": timeout}
            )
            return test.smsir_answer(method, path, json)

        def fake_bale(url, json=None, headers=None, timeout=None):
            test.bale_calls.append({"url": url, "payload": json, "headers": headers, "timeout": timeout})
            return test.bale_answer(json)

        real_send = requests.sessions.Session.send

        def guard_send(session, prepared, **kwargs):
            # the HTTP test client talks to the local server; nothing else may go out
            if urlsplit(prepared.url).hostname in (HOST, "localhost", "127.0.0.1"):
                return real_send(session, prepared, **kwargs)
            test.network_calls.append(prepared.url)
            raise requests.exceptions.ConnectionError("network is off in the tests")

        with (
            patch.object(smsir.requests, "request", side_effect=fake_smsir),
            patch.object(bale.requests, "post", side_effect=fake_bale),
            patch.object(requests.sessions.Session, "send", guard_send),
        ):
            yield

    @contextmanager
    def no_network(self):
        """Any request at all (sms.ir, Bale, IAP…) is recorded and fails."""
        test = self
        real_send = requests.sessions.Session.send

        def record(*args, **kwargs):
            test.network_calls.append(args[1] if len(args) > 1 else kwargs.get("url"))
            raise requests.exceptions.ConnectionError("network is off in the tests")

        def guard_send(session, prepared, **kwargs):
            if urlsplit(prepared.url).hostname in (HOST, "localhost", "127.0.0.1"):
                return real_send(session, prepared, **kwargs)
            test.network_calls.append(prepared.url)
            raise requests.exceptions.ConnectionError("network is off in the tests")

        with (
            patch.object(smsir.requests, "request", side_effect=record),
            patch.object(bale.requests, "post", side_effect=lambda url, **kw: record(None, url)),
            patch.object(requests.sessions.Session, "send", guard_send),
        ):
            yield

    def bale_code(self):
        """The code of the last Bale payload."""
        return self.bale_calls[-1]["payload"]["message_data"]["otp_message"]["otp"]
