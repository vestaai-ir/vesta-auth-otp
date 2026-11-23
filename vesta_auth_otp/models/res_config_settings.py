# Copyright 2026 Vesta AI (https://vestaai.ir)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import secrets

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..tools import bale, phone
from .vesta_auth_otp import PARAM

SYSTEM = "base.group_system"


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    vesta_otp_enabled = fields.Boolean(
        "Login with Mobile",
        config_parameter=PARAM + "enabled",
        groups=SYSTEM,
        help="Customers log in and sign up on the website with their mobile number and a one-time code.",
    )
    vesta_otp_test_mode = fields.Boolean(
        "Test Mode",
        config_parameter=PARAM + "test_mode",
        default=True,
        groups=SYSTEM,
        help="Nothing is sent: the code is shown on the login page and written in the server log. Turn it off"
        " once sms.ir or Bale is set up; never leave it on for real customers.",
    )
    vesta_otp_code_length = fields.Integer(
        "Code Length", config_parameter=PARAM + "code_length", default=6, groups=SYSTEM
    )
    vesta_otp_expiry = fields.Integer(
        "Code Lifetime (seconds)", config_parameter=PARAM + "expiry", default=120, groups=SYSTEM
    )
    vesta_otp_resend_delay = fields.Integer(
        "Resend After (seconds)", config_parameter=PARAM + "resend_delay", default=60, groups=SYSTEM
    )
    vesta_otp_max_attempts = fields.Integer(
        "Wrong Attempts per Code", config_parameter=PARAM + "max_attempts", default=5, groups=SYSTEM
    )
    vesta_otp_phone_limit = fields.Integer(
        "Codes per Number per Hour", config_parameter=PARAM + "phone_limit", default=5, groups=SYSTEM
    )
    vesta_otp_ip_limit = fields.Integer(
        "Codes per IP Address per Hour", config_parameter=PARAM + "ip_limit", default=20, groups=SYSTEM
    )
    vesta_otp_allow_internal = fields.Boolean(
        "Colleagues Too",
        config_parameter=PARAM + "allow_internal",
        groups=SYSTEM,
        help="Internal users may log in with a code too (two-factor authentication still applies). Off: only"
        " customers (portal users).",
    )
    vesta_otp_sms_enabled = fields.Boolean(
        "Send by SMS", config_parameter=PARAM + "sms_enabled", default=True, groups=SYSTEM
    )
    vesta_otp_sms_template_id = fields.Char(
        "sms.ir Template ID",
        config_parameter=PARAM + "sms_template_id",
        groups=SYSTEM,
        help="Optional: the id of an approved «verify» template of sms.ir (fast send). Empty: a plain SMS.",
    )
    vesta_otp_sms_template_param = fields.Char(
        "Template Parameter",
        config_parameter=PARAM + "sms_template_param",
        default="Code",
        groups=SYSTEM,
        help="The name of the parameter of the template that receives the code (#Code# in the template: Code).",
    )
    vesta_otp_bale_enabled = fields.Boolean("Send on Bale", config_parameter=PARAM + "bale_enabled", groups=SYSTEM)
    vesta_otp_bale_api_key = fields.Char("Safir API Key", config_parameter=PARAM + "bale_api_key", groups=SYSTEM)
    vesta_otp_bale_bot_id = fields.Char("Bot ID", config_parameter=PARAM + "bale_bot_id", groups=SYSTEM)
    vesta_otp_test_mobile = fields.Char("Login Test Mobile", config_parameter=PARAM + "test_mobile", groups=SYSTEM)

    @api.constrains(
        "vesta_otp_code_length",
        "vesta_otp_expiry",
        "vesta_otp_resend_delay",
        "vesta_otp_max_attempts",
        "vesta_otp_phone_limit",
        "vesta_otp_ip_limit",
        "vesta_otp_bale_bot_id",
        "vesta_otp_sms_template_id",
    )
    def _check_vesta_otp(self):
        _ = self.env._
        for settings in self:
            if not 4 <= settings.vesta_otp_code_length <= 6:
                raise ValidationError(_("The code has 4 to 6 digits."))
            if not 30 <= settings.vesta_otp_expiry <= 900:
                raise ValidationError(_("A code lives 30 to 900 seconds."))
            if not 0 <= settings.vesta_otp_resend_delay <= 600:
                raise ValidationError(_("The resend delay is 0 to 600 seconds."))
            if min(settings.vesta_otp_max_attempts, settings.vesta_otp_phone_limit, settings.vesta_otp_ip_limit) < 1:
                raise ValidationError(_("The limits are at least 1."))
            if (settings.vesta_otp_bale_bot_id or "").strip() and not settings.vesta_otp_bale_bot_id.strip().isdigit():
                raise ValidationError(_("The bot ID of Bale is a number."))
            template = (settings.vesta_otp_sms_template_id or "").strip()
            if template and not template.isdigit():
                raise ValidationError(_("The template ID of sms.ir is a number."))

    def _vesta_otp_notify(self, title, message, notif_type="success"):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"title": title, "message": message, "type": notif_type, "sticky": notif_type != "success"},
        }

    def _vesta_otp_test_number(self):
        normal = phone.normalize(phone.ascii_digits(self.vesta_otp_test_mobile or ""))
        if not normal:
            raise UserError(self.env._("Enter the test mobile (an Iranian mobile number) first."))
        return normal

    def action_vesta_otp_bale_test(self):
        """Send a test code on Bale with the values of this form; in test mode, only check them."""
        self.ensure_one()
        _ = self.env._
        key = (self.vesta_otp_bale_api_key or "").strip()
        bot_id = (self.vesta_otp_bale_bot_id or "").strip()
        if not key or not bot_id.isdigit():
            raise UserError(_("Enter the Safir API key and the bot ID (a number) of Bale first."))
        normal = self._vesta_otp_test_number()
        code = "".join(secrets.choice("0123456789") for _i in range(self.vesta_otp_code_length or 6))
        if self.vesta_otp_test_mode:
            return self._vesta_otp_notify(
                _("Bale (test mode)"),
                _(
                    "Test mode: nothing was sent. The settings look right; Bale would get the code %(code)s for"
                    " %(phone)s. Turn test mode off to send a real test message.",
                    code=code,
                    phone=normal,
                ),
                "info",
            )
        try:
            message_id = bale.SafirClient(key, bot_id).send_otp(normal, code)
        except bale.BaleError as error:
            return self._vesta_otp_notify(
                _("Bale"),
                _("The test message was not sent: %(error)s", error=self._vesta_otp_bale_error_text(error)),
                "danger",
            )
        return self._vesta_otp_notify(
            _("Bale"),
            _("Test code %(code)s sent to %(phone)s (message %(id)s).", code=code, phone=normal, id=message_id),
        )

    def _vesta_otp_bale_error_text(self, error):
        _ = self.env._
        texts = {
            bale.INTERNAL_ERROR: _("Bale had an internal error; try again later."),
            bale.RATE_LIMIT: _("Too many requests; try again in a minute."),
            bale.INVALID_INPUT: _("Bale rejected the request; check the bot ID."),
            bale.INVALID_PHONE: _("The number is not valid for Bale."),
            bale.NOT_BALE_USER: _("This number has no Bale account."),
            bale.PAYMENT_REQUIRED: _("The Safir account has no credit."),
            bale.CONTACT_LIMIT: _("The Safir account reached its contact limit."),
            bale.NETWORK_ERROR: _("Bale could not be reached, or the API key was rejected."),
        }
        return f"{texts.get(error.code, error.description)} ({error.code})"

    def action_vesta_otp_sms_test(self):
        """Send a test code by SMS with the values of this form; in test mode, only say what would be sent."""
        self.ensure_one()
        _ = self.env._
        normal = self._vesta_otp_test_number()
        otp_model = self.env["vesta.auth.otp"].sudo()
        settings = dict(
            otp_model._otp_settings(),
            test_mode=self.vesta_otp_test_mode,
            sms_template_id=(self.vesta_otp_sms_template_id or "").strip(),
            sms_template_param=(self.vesta_otp_sms_template_param or "").strip() or "Code",
            bale_enabled=False,
        )
        code = "".join(secrets.choice("0123456789") for _i in range(self.vesta_otp_code_length or 6))
        if settings["test_mode"]:
            return self._vesta_otp_notify(
                _("SMS (test mode)"),
                _(
                    "Test mode: nothing was sent. The SMS to %(phone)s would read: %(text)s",
                    phone=normal,
                    text=otp_model.new({"phone": normal})._sms_text(code),
                ),
                "info",
            )
        otp = otp_model.create(
            {"phone": normal, "purpose": "login", "state": "dead", "challenge": secrets.token_urlsafe(24)}
        )
        state, info, _error = otp._send_sms(code, settings)
        otp.write({"sms_state": state, "sms_info": info})
        if state == "sent":
            return self._vesta_otp_notify(_("SMS"), _("Test code %(code)s sent to %(phone)s.", code=code, phone=normal))
        return self._vesta_otp_notify(_("SMS"), _("The test SMS was not sent: %(error)s", error=info), "danger")
