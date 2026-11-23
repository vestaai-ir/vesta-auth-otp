# Copyright 2026 Vesta AI (https://vestaai.ir)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""Client of Safir, the OTP service of the Bale messenger (https://docs.bale.ai/safir).

Bale sends our code inside its own fixed message, from its verification-code bot.
"""

import logging
import uuid

import requests

_logger = logging.getLogger(__name__)

API_URL = "https://safir.bale.ai/api/v3/send_message"
TIMEOUT = 10

# ``code`` of the entries of ``error_data``
INTERNAL_ERROR = 2
RATE_LIMIT = 3
INVALID_INPUT = 4
INVALID_PHONE = 8
NOT_BALE_USER = 17
PAYMENT_REQUIRED = 20
CONTACT_LIMIT = 21
ERROR_NAMES = {
    INTERNAL_ERROR: "InternalServerError",
    RATE_LIMIT: "RateLimitExceeded",
    INVALID_INPUT: "InvalidInput",
    INVALID_PHONE: "InvalidPhone",
    NOT_BALE_USER: "NotBaleUser",
    PAYMENT_REQUIRED: "PaymentRequired",
    CONTACT_LIMIT: "MaximumContactLimitReached",
}
NETWORK_ERROR = -1  # no answer, or not JSON


class BaleError(Exception):
    def __init__(self, code, description=""):
        self.code = code
        self.description = description or ERROR_NAMES.get(code, "")
        super().__init__(f"Bale Safir {code}: {self.description}")


def build_payload(phone, otp, bot_id, request_id=None):
    """The body of ``send_message``; ``phone`` is ``98XXXXXXXXXX`` and ``otp`` holds digits only."""
    return {
        "request_id": request_id or str(uuid.uuid4()),
        "bot_id": int(bot_id),
        "phone_number": phone,
        "message_data": {"otp_message": {"otp": otp}},
    }


class SafirClient:
    def __init__(self, api_key, bot_id, timeout=TIMEOUT):
        self.api_key = (api_key or "").strip()
        self.bot_id = int(bot_id)
        self.timeout = timeout

    def send_otp(self, phone, otp, request_id=None):
        """Send ``otp`` to ``phone``; return the ``message_id`` or raise :class:`BaleError`."""
        payload = build_payload(phone, otp, self.bot_id, request_id)
        headers = {"api-access-key": self.api_key, "Content-Type": "application/json"}
        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=self.timeout)
        except requests.exceptions.RequestException as error:
            _logger.warning("Bale Safir request %s failed: %s", payload["request_id"], error)
            raise BaleError(NETWORK_ERROR, str(error)) from error
        try:
            body = response.json()
        except ValueError:
            body = None
        if not isinstance(body, dict):
            body = {}
        # errors come in error_data, even with HTTP 200
        errors = body.get("error_data") or []
        if errors:
            error = errors[0] if isinstance(errors[0], dict) else {}
            code = error.get("code")
            code = code if isinstance(code, int) else INTERNAL_ERROR
            _logger.info("Bale Safir request %s: error %s (%s)", payload["request_id"], code, error.get("description"))
            raise BaleError(code, error.get("description") or "")
        message_id = body.get("message_id")
        if response.status_code >= 400 or not message_id:
            _logger.info(
                "Bale Safir request %s: HTTP %s without message id", payload["request_id"], response.status_code
            )
            raise BaleError(NETWORK_ERROR, f"HTTP {response.status_code}")
        return str(message_id)
