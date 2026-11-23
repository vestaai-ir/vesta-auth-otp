# Copyright 2026 Vesta AI (https://vestaai.ir)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""sms.ir for login codes: the fast «verify» template send, and short timeouts for the plain SMS."""

from odoo.addons.vesta_marketing.tools import smsir
from odoo.addons.vesta_marketing.tools.sms_api import SmsApiSmsIr

TIMEOUT = 8  # the code must arrive now or not at all


class SmsIrVerifyClient(smsir.SmsIrClient):
    """The sms.ir client of Vesta Marketing with the «ارسال سریع» (verify) endpoint."""

    def __init__(self, api_key, timeout=TIMEOUT):
        super().__init__(api_key, timeout=timeout)

    def send_verify(self, mobile, template_id, parameters):
        """Send the approved template ``template_id`` to ``mobile`` (``09…``) with ``parameters``.

        :param parameters: ``{name: value}`` of the template, e.g. ``{"Code": "123456"}``
        :return: ``{"messageId", "cost"}``
        """
        return self._request(
            "POST",
            "/send/verify",
            {
                "mobile": mobile,
                "templateId": int(template_id),
                "parameters": [{"name": name, "value": str(value)} for name, value in parameters.items()],
            },
        )


class SmsApiSmsIrOtp(SmsApiSmsIr):
    """The sms.ir provider of Vesta Marketing with a short timeout, for the login codes sent as plain SMS."""

    def _send_chunk(self, client, recipients, texts):
        return super()._send_chunk(smsir.SmsIrClient(self.api_key, timeout=TIMEOUT), recipients, texts)
