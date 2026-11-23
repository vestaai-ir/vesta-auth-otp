# Copyright 2026 Vesta AI (https://vestaai.ir)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import hmac as std_hmac
import logging
import secrets
import threading
from datetime import timedelta

from odoo import api, fields, models
from odoo.addons.auth_signup.models.res_partner import SignupError
from odoo.addons.vesta_marketing.tools import smsir
from odoo.addons.vesta_marketing.tools.sms_api import PARAM_API_KEY, SmsApiSmsIr
from odoo.exceptions import AccessDenied, UserError, ValidationError
from odoo.fields import Domain
from odoo.http import request
from odoo.tools import hmac

from ..tools import bale, phone
from ..tools.sms import SmsIrVerifyClient

_logger = logging.getLogger(__name__)

PARAM = "vesta_auth_otp."
TOKEN_LIFETIME = 300  # seconds between a right code and the login or the sign-up
PURGE_AFTER = timedelta(days=1)
SENT = ("sent", "test")


class VestaAuthOtp(models.Model):
    """One login code: who asked for it, how it was sent, and what became of it.

    The code itself is never stored: only an HMAC of it (with the secret of the database and a salt of the
    record). A right code gives a one-time token, which logs in through ``res.users._check_credentials``.
    """

    _name = "vesta.auth.otp"
    _description = "Mobile Login Code"
    _order = "id desc"
    _rec_name = "phone"

    phone = fields.Char("Mobile", required=True, readonly=True, index=True, help="98 and the 10 digits of the mobile.")
    purpose = fields.Selection(
        [("login", "Login or sign-up"), ("change", "Change of mobile")],
        required=True,
        default="login",
        readonly=True,
    )
    user_id = fields.Many2one("res.users", "User", readonly=True, ondelete="cascade", index="btree_not_null")
    website_id = fields.Many2one("website", readonly=True, ondelete="set null")
    ip = fields.Char("IP Address", readonly=True, index=True)
    session_hash = fields.Char(readonly=True)
    challenge = fields.Char(readonly=True, index=True, copy=False)
    salt = fields.Char(readonly=True, copy=False)
    code_hash = fields.Char(readonly=True, copy=False)
    attempts = fields.Integer("Wrong Attempts", readonly=True)
    expire_at = fields.Datetime("Expires", readonly=True)
    state = fields.Selection(
        [("pending", "Waiting for the code"), ("verified", "Code verified"), ("used", "Used"), ("dead", "Dead")],
        required=True,
        default="pending",
        readonly=True,
    )
    sms_state = fields.Selection(
        [("sent", "Sent"), ("failed", "Failed"), ("off", "Off"), ("test", "Test mode")],
        "SMS",
        readonly=True,
        default="off",
    )
    sms_info = fields.Char("SMS Details", readonly=True)
    bale_state = fields.Selection(
        [("sent", "Sent"), ("failed", "Failed"), ("off", "Off"), ("test", "Test mode")],
        "Bale",
        readonly=True,
        default="off",
    )
    bale_info = fields.Char("Bale Details", readonly=True)
    token_hash = fields.Char(readonly=True, index="btree_not_null", copy=False)
    token_expire_at = fields.Datetime(readonly=True)

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    @api.model
    def _otp_settings(self):
        params = self.env["ir.config_parameter"].sudo()
        return {
            "enabled": params.get_bool(PARAM + "enabled", False),
            "test_mode": params.get_bool(PARAM + "test_mode", True),
            "code_length": min(6, max(4, params.get_int(PARAM + "code_length", 6))),
            "expiry": max(30, params.get_int(PARAM + "expiry", 120)),
            "resend_delay": max(0, params.get_int(PARAM + "resend_delay", 60)),
            "max_attempts": max(1, params.get_int(PARAM + "max_attempts", 5)),
            "phone_limit": max(1, params.get_int(PARAM + "phone_limit", 5)),
            "ip_limit": max(1, params.get_int(PARAM + "ip_limit", 20)),
            "allow_internal": params.get_bool(PARAM + "allow_internal", False),
            "sms_enabled": params.get_bool(PARAM + "sms_enabled", True),
            "sms_template_id": params.get_str(PARAM + "sms_template_id").strip(),
            "sms_template_param": params.get_str(PARAM + "sms_template_param").strip() or "Code",
            "bale_enabled": params.get_bool(PARAM + "bale_enabled", False),
            "bale_api_key": params.get_str(PARAM + "bale_api_key").strip(),
            "bale_bot_id": params.get_str(PARAM + "bale_bot_id").strip(),
        }

    @api.model
    def _otp_enabled(self):
        return self._otp_settings()["enabled"]

    @api.model
    def _bale_ready(self, settings):
        return bool(settings["bale_enabled"] and settings["bale_api_key"] and settings["bale_bot_id"].isdigit())

    # ------------------------------------------------------------------
    # Hashing
    # ------------------------------------------------------------------

    def _digest(self, scope, message):
        return hmac(self.env(su=True), "vesta_auth_otp." + scope, message)

    def _code_matches(self, code):
        self.ensure_one()
        expected = self._digest("code", f"{self.id}:{self.salt}:{code}")
        return bool(self.code_hash) and std_hmac.compare_digest(expected, self.code_hash)

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------

    @api.model
    def _request_code(self, raw_phone, purpose="login", ip=None, session_id="", website=None, user=None):
        """Create a code for ``raw_phone`` and send it; the answer never tells whether an account exists.

        :return: ``{"ok": True, "challenge", "message", "hint", "resend_in", "expires_in", "phone_display",
            "test_code"}`` or ``{"ok": False, "error", "resend_in"}``
        """
        _ = self.env._
        settings = self._otp_settings()
        normal = phone.normalize(phone.ascii_digits(raw_phone or ""))
        if not normal:
            return {"ok": False, "error": _("Enter a valid mobile number, like 0912 345 6789.")}
        now = fields.Datetime.now()
        hour_ago = now - timedelta(hours=1)
        last = self.search([("phone", "=", normal), ("purpose", "=", purpose)], order="id desc", limit=1)
        if last and settings["resend_delay"]:
            wait = int((last.create_date + timedelta(seconds=settings["resend_delay"]) - now).total_seconds()) + 1
            if wait > 0:
                return {
                    "ok": False,
                    "error": _("You can ask for a new code in %(seconds)s seconds.", seconds=wait),
                    "resend_in": wait,
                }
        if self.search_count([("phone", "=", normal), ("create_date", ">", hour_ago)]) >= settings["phone_limit"] or (
            ip and self.search_count([("ip", "=", ip), ("create_date", ">", hour_ago)]) >= settings["ip_limit"]
        ):
            _logger.info("Vesta OTP: rate limit for %s from %s", phone.mask(normal), ip)
            return {"ok": False, "error": _("Too many codes were asked for. Try again later.")}

        # only the latest code of a number is valid
        self.search([("phone", "=", normal), ("purpose", "=", purpose), ("state", "=", "pending")]).state = "dead"
        code = "".join(secrets.choice("0123456789") for _i in range(settings["code_length"]))
        otp = self.create(
            {
                "phone": normal,
                "purpose": purpose,
                "user_id": user.id if user else False,
                "website_id": website.id if website else False,
                "ip": ip,
                "session_hash": self._digest("session", session_id or ""),
                "challenge": secrets.token_urlsafe(24),
                "salt": secrets.token_hex(16),
                "expire_at": now + timedelta(seconds=settings["expiry"]),
            }
        )
        otp.code_hash = otp._digest("code", f"{otp.id}:{otp.salt}:{code}")
        results = otp._send_code(code, settings, website)
        otp.write(
            {
                "sms_state": results["sms"][0],
                "sms_info": results["sms"][1],
                "bale_state": results["bale"][0],
                "bale_info": results["bale"][1],
            }
        )
        sms_ok, bale_ok = results["sms"][0] in SENT, results["bale"][0] in SENT
        lang = self.env.lang or ""
        if not (sms_ok or bale_ok):
            otp.state = "dead"
            _logger.warning("Vesta OTP: no channel took the code for %s", phone.mask(normal))
            return {
                "ok": False,
                "error": _(
                    "The code could not be sent. Try again in a few minutes, or log in with your email and password."
                ),
            }
        answer = {
            "ok": True,
            "challenge": otp.challenge,
            "resend_in": settings["resend_delay"],
            "expires_in": settings["expiry"],
            "code_length": settings["code_length"],
            "phone_display": phone.display(normal, lang),
            "hint": "",
        }
        if settings["test_mode"]:
            answer["test_code"] = code
            answer["message"] = _("Test mode: nothing was sent. Your code is %(code)s.", code=code)
            return answer
        if sms_ok and bale_ok:
            answer["message"] = _("The code was sent by SMS and Bale.")
        elif sms_ok:
            answer["message"] = _("The code was sent by SMS.")
            if results["bale"][2] == bale.NOT_BALE_USER:
                answer["hint"] = _("This number has no Bale account; the code was sent by SMS.")
        else:
            answer["message"] = _("The code was sent on Bale.")
        return answer

    def _send_code(self, code, settings, website=None):
        """Send ``code`` by SMS and Bale at the same time (Bale in a thread, it does not touch the database).

        :return: ``{"sms": (state, info, error), "bale": (state, info, error)}``, never with the code in it
        """
        self.ensure_one()
        number = phone.mask(self.phone)
        bale_ready = self._bale_ready(settings)
        if settings["test_mode"]:
            _logger.info("Vesta OTP test mode: code %s for %s (nothing sent)", code, number)
            return {
                "sms": ("test", "test mode", None) if settings["sms_enabled"] else ("off", "", None),
                "bale": ("test", "test mode", None) if bale_ready else ("off", "", None),
            }

        results = {"sms": ("off", "", None), "bale": ("off", "", None)}
        thread = None
        if bale_ready:
            client = bale.SafirClient(settings["bale_api_key"], settings["bale_bot_id"])
            target_phone = self.phone

            def send_bale():
                try:
                    message_id = client.send_otp(target_phone, code)
                    results["bale"] = ("sent", f"message {message_id}", None)
                except bale.BaleError as error:
                    results["bale"] = ("failed", f"{error.code} {error.description}"[:200], error.code)
                except Exception as error:  # noqa: BLE001 - a thread must not die silently
                    _logger.exception("Vesta OTP: Bale failed for %s", number)
                    results["bale"] = ("failed", type(error).__name__, None)

            thread = threading.Thread(target=send_bale, name="vesta_otp_bale", daemon=True)
            thread.start()
        if settings["sms_enabled"]:
            results["sms"] = self._send_sms(code, settings, website)
        if thread:
            thread.join(bale.TIMEOUT + 1)
            if thread.is_alive():
                results["bale"] = ("failed", "timeout", None)
        for channel in ("sms", "bale"):
            if results[channel][0] == "failed":
                _logger.warning("Vesta OTP: %s failed for %s: %s", channel, number, results[channel][1])
        return results

    def _sms_text(self, code, website=None):
        """«Your login code for …: 123456», with the last line of the WebOTP / SMS Retriever format."""
        website = website or self.website_id
        name = (website and website.name) or self.env.company.name
        domain = self._sms_domain(website)
        text = self.env._("Your login code for %(website)s: %(code)s", website=name, code=code)
        return f"{text}\n\n@{domain} #{code}" if domain else text

    def _sms_domain(self, website=None):
        host = ""
        if request:
            host = request.httprequest.host or ""
        elif website and website.domain:
            host = website.domain
        else:
            host = self.env["ir.config_parameter"].sudo().get_str("web.base.url")
        host = host.split("://", 1)[-1].split("/", 1)[0]
        return host.rsplit(":", 1)[0] if host.count(":") == 1 else host

    def _send_sms(self, code, settings, website=None):
        """The fast template of sms.ir when one is set, else a plain SMS sent at once through Odoo."""
        self.ensure_one()
        mobile = phone.local(self.phone)
        if settings["sms_template_id"] and SmsApiSmsIr.is_configured(self.env):
            if not settings["sms_template_id"].isdigit():
                return ("failed", "template id is not a number", None)
            api_key = self.env["ir.config_parameter"].sudo().get_str(PARAM_API_KEY)
            try:
                data = SmsIrVerifyClient(api_key).send_verify(
                    mobile, settings["sms_template_id"], {settings["sms_template_param"]: code}
                )
            except smsir.SmsIrError as error:
                return ("failed", f"sms.ir verify {error.status}", error.status)
            return ("sent", f"sms.ir verify {(data or {}).get('messageId')}", None)

        sms = (
            self.env["sms.sms"]
            .sudo()
            .create({"number": phone.e164(self.phone), "body": self._sms_text(code, website), "sms_type": "alert"})
        )
        sms.with_context(vesta_otp_sms=True).send(unlink_sent=True, raise_exception=False)
        state, failure = sms.state, sms.failure_type
        sms.unlink()  # the body holds the code
        if state in ("pending", "sent"):
            return ("sent", "sms", None)
        return ("failed", f"sms {failure or 'error'}", failure)

    # ------------------------------------------------------------------
    # Checking
    # ------------------------------------------------------------------

    @api.model
    def _find_challenge(self, challenge, session_id=""):
        if not challenge or not isinstance(challenge, str):
            return self.browse()
        otp = self.search([("challenge", "=", challenge)], limit=1)
        if otp and not std_hmac.compare_digest(otp.session_hash or "", self._digest("session", session_id or "")):
            return self.browse()
        return otp

    @api.model
    def _check_code(self, challenge, code, session_id="", website=None, user=None):
        """Check the code typed for ``challenge``.

        :return: ``{"ok": True, "action": "login" | "signup" | "changed", "token"…}`` or ``{"ok": False, "error"…}``
        """
        _ = self.env._
        settings = self._otp_settings()
        otp = self._find_challenge(challenge, session_id)
        if not otp or otp.state != "pending":
            return {"ok": False, "error": _("This code is no longer valid. Ask for a new one."), "dead": True}
        otp = otp.try_lock_for_update()
        if not otp:
            return {"ok": False, "error": _("Please try again."), "dead": False}
        if otp.expire_at < fields.Datetime.now():
            otp.state = "dead"
            return {"ok": False, "error": _("The code has expired. Ask for a new one."), "dead": True}
        code = phone.ascii_digits(code or "").strip()
        if not (code.isdigit() and otp._code_matches(code)):
            otp.attempts += 1
            left = settings["max_attempts"] - otp.attempts
            if left <= 0:
                otp.state = "dead"
                _logger.info("Vesta OTP: code of %s locked after %s attempts", phone.mask(otp.phone), otp.attempts)
                return {"ok": False, "error": _("Too many wrong codes. Ask for a new one."), "dead": True}
            return {
                "ok": False,
                "error": _("Wrong code. %(count)s attempts left.", count=left),
                "attempts_left": left,
                "dead": False,
            }

        if otp.purpose == "change":
            return otp._apply_change(user)

        users = self._match_users(otp.phone, website)
        if len(users) > 1:
            otp.state = "used"
            return {
                "ok": False,
                "error": _("This number belongs to several accounts. Log in with your email and password."),
                "dead": True,
            }
        if users and users._is_internal() and not settings["allow_internal"]:
            otp.state = "used"
            return {
                "ok": False,
                "error": _("This account logs in with its email and password."),
                "dead": True,
            }
        if not users:
            if self.env["res.users"].sudo()._get_signup_invitation_scope() != "b2c":
                otp.state = "used"
                return {"ok": False, "error": _("No account was found with this mobile number."), "dead": True}
            token = otp._issue_token()
            return {"ok": True, "action": "signup", "token": token}
        otp.user_id = users
        return {"ok": True, "action": "login", "token": otp._issue_token()}

    def _issue_token(self):
        self.ensure_one()
        token = secrets.token_urlsafe(32)
        self.write(
            {
                "state": "verified",
                "token_hash": self._digest("token", token),
                "token_expire_at": fields.Datetime.now() + timedelta(seconds=TOKEN_LIFETIME),
            }
        )
        return token

    @api.model
    def _find_token(self, token, session_id=None):
        if not token or not isinstance(token, str):
            return self.browse()
        domain = Domain("token_hash", "=", self._digest("token", token)) & Domain("state", "=", "verified")
        domain &= Domain("purpose", "=", "login") & Domain("token_expire_at", ">", fields.Datetime.now())
        otp = self.search(domain, limit=1)
        if (
            otp
            and session_id is not None
            and not std_hmac.compare_digest(otp.session_hash or "", self._digest("session", session_id))
        ):
            return self.browse()
        return otp

    @api.model
    def _consume_token(self, token, user):
        """Use the token of a right code once, for ``user``; raise ``AccessDenied`` otherwise."""
        otp = self._find_token(token)
        if not otp or otp.user_id != user:
            raise AccessDenied()
        otp = otp.try_lock_for_update()
        if not otp or otp.state != "verified":
            raise AccessDenied()
        otp.state = "used"
        otp.user_id.partner_id._vesta_otp_set_verified(otp.phone)
        return otp

    # ------------------------------------------------------------------
    # Accounts
    # ------------------------------------------------------------------

    @api.model
    def _match_users(self, normal, website=None):
        """The account of a verified number: its verified mobile, a login equal to it, or the phone of its contact.

        The phone of the contact counts only when it was not typed on the website (``vesta_otp_phone_untrusted``):
        nobody can give an account the number of someone else.
        """
        users = self.env["res.users"].sudo().with_context(active_test=True)
        site = website.website_domain() if website else Domain.TRUE
        found = users.search(site & Domain("partner_id.vesta_otp_verified_mobile", "=", normal), order="id")
        if found:
            return found[:1]
        found = users.search(site & Domain("login", "in", phone.variants(normal)), order="id", limit=1)
        if found:
            return found
        found = users.search(
            site
            & Domain("partner_id.vesta_otp_mobile", "=", normal)
            & Domain("partner_id.vesta_otp_phone_untrusted", "=", False),
            order="id",
        )
        # a customer and a colleague with the same phone: the customer account is the one of the website
        return found.filtered("share") or found

    @api.model
    def _signup(self, challenge, token, name, session_id="", lang=None):
        """Create the portal user of a verified number that has no account."""
        _ = self.env._
        otp = self._find_challenge(challenge, session_id)
        if not otp or otp != self._find_token(token) or otp.user_id:
            return {"ok": False, "error": _("This code is no longer valid. Ask for a new one."), "dead": True}
        name = " ".join((name or "").split())
        if len(name) < 2:
            return {"ok": False, "error": _("Enter your full name.")}
        if self._match_users(otp.phone, otp.website_id):
            return {"ok": False, "error": _("This number already has an account. Log in again."), "dead": True}
        values = {
            "name": name[:128],
            "login": phone.local(otp.phone),
            "phone": phone.e164(otp.phone),
        }
        if lang and self.env["res.lang"]._get_data(code=lang):
            values["lang"] = lang
        try:
            with self.env.cr.savepoint():
                user = self.env["res.users"].sudo()._signup_create_user(values)
        except (SignupError, UserError, ValidationError, ValueError) as error:
            _logger.warning("Vesta OTP: sign-up of %s failed: %s", phone.mask(otp.phone), error)
            return {"ok": False, "error": _("The account could not be created. Try again, or contact us.")}
        user.partner_id._vesta_otp_set_verified(otp.phone)
        otp.user_id = user
        _logger.info("Vesta OTP: portal user %s created for %s", user.id, phone.mask(otp.phone))
        return {"ok": True, "action": "login", "token": token}

    def _apply_change(self, user):
        """A verified new mobile for the user who asked for it."""
        self.ensure_one()
        _ = self.env._
        self.state = "used"
        if not user or user != self.user_id:
            return {"ok": False, "error": _("This code is no longer valid. Ask for a new one."), "dead": True}
        taken = (
            self.env["res.users"]
            .sudo()
            .with_context(active_test=False)
            .search_count([("login", "in", phone.variants(self.phone)), ("id", "!=", user.id)], limit=1)
        )
        if taken:
            return {"ok": False, "error": _("This number belongs to another account."), "dead": True}
        old = user.partner_id.vesta_otp_verified_mobile or phone.normalize(user.partner_id.phone or "")
        values = {}
        if old and user.login in phone.variants(old):
            values["login"] = phone.local(self.phone)  # the old number must not open this account any more
        if values:
            user.sudo().write(values)
        user.partner_id.sudo().write({"phone": phone.e164(self.phone)})
        user.partner_id._vesta_otp_set_verified(self.phone)
        lang = self.env.lang or ""
        return {
            "ok": True,
            "action": "changed",
            "phone_display": phone.display(self.phone, lang),
            "message": _("Your mobile number is now %(phone)s.", phone=phone.display(self.phone, lang)),
        }

    # ------------------------------------------------------------------
    # Housekeeping
    # ------------------------------------------------------------------

    @api.model
    def _cron_purge(self):
        """Delete the codes of more than a day (the rate limits look at the last hour)."""
        old = self.search([("create_date", "<", fields.Datetime.now() - PURGE_AFTER)])
        old.unlink()
        return len(old)
