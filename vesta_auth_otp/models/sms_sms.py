# Copyright 2026 Vesta AI (https://vestaai.ir)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import models
from odoo.addons.vesta_marketing.tools.sms_api import SmsApiSmsIr

from ..tools.sms import SmsApiSmsIrOtp


class SmsSms(models.Model):
    _inherit = "sms.sms"

    def _split_by_api(self):
        """Login codes go through sms.ir with a short timeout."""
        if self.env.context.get("vesta_otp_sms") and SmsApiSmsIr.is_configured(self.env):
            yield SmsApiSmsIrOtp(self.env), self
        else:
            yield from super()._split_by_api()
