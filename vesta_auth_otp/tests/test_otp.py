# Copyright 2026 Vesta AI (https://vestaai.ir)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import uuid
from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessDenied
from odoo.tests import TransactionCase, new_test_user, tagged

from ..models.vesta_auth_otp import PARAM
from ..tools import bale, phone
from .common import BALE_BOT, BALE_KEY, SMSIR_KEY, SMSIR_LINE, FakeResponse, OtpMockMixin

NUMBER = "989121234567"


@tagged("post_install", "-at_install")
class TestOtpCodes(OtpMockMixin, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._otp_setup_settings(cls.env)
        cls.otp = cls.env["vesta.auth.otp"].sudo()
        cls.website = cls.env["website"].browse(1)

    def setUp(self):
        super().setUp()
        self._otp_reset_mocks()

    def send(self, number="۰۹۱۲ ۱۲۳ ۴۵۶۷", ip="10.0.0.1", session="s1", **kwargs):
        with self.mock_channels():
            return self.otp._request_code(number, ip=ip, session_id=session, website=self.website, **kwargs)

    def check(self, answer, code, session="s1", **kwargs):
        return self.otp._check_code(answer["challenge"], code, session_id=session, website=self.website, **kwargs)

    # ------------------------------------------------------------------

    def test_phone_normalize(self):
        for raw in (
            "09121234567",
            "9121234567",
            "+989121234567",
            "+98 912 123 4567",
            "00989121234567",
            "989121234567",
            "۰۹۱۲۱۲۳۴۵۶۷",
            "٠٩١٢١٢٣٤٥٦٧",
            "0912-123-4567",
        ):
            self.assertEqual(phone.normalize(raw), NUMBER, raw)
        for raw in ("", "12345", "02112345678", "+44 7911 123456", None, "0912123456"):
            self.assertIsNone(phone.normalize(raw), raw)
        self.assertEqual(phone.display(NUMBER, "fa_IR"), "۰۹۱۲ ۱۲۳ ۴۵۶۷")
        self.assertEqual(phone.local(NUMBER), "09121234567")

    def test_send_both_channels_payloads(self):
        answer = self.send()
        self.assertTrue(answer["ok"])
        self.assertEqual(answer["message"], "The code was sent by SMS and Bale.")
        self.assertNotIn("test_code", answer)

        # Bale: exactly the body of Safir, the number normalized
        self.assertEqual(len(self.bale_calls), 1)
        call = self.bale_calls[0]
        self.assertEqual(call["url"], "https://safir.bale.ai/api/v3/send_message")
        self.assertEqual(call["headers"], {"api-access-key": BALE_KEY, "Content-Type": "application/json"})
        self.assertEqual(call["timeout"], 10)
        code = self.bale_code()
        self.assertRegex(code, r"^\d{6}$")
        payload = dict(call["payload"])
        request_id = payload.pop("request_id")
        uuid.UUID(request_id)  # a uuid4 per send
        self.assertEqual(
            payload,
            {"bot_id": int(BALE_BOT), "phone_number": NUMBER, "message_data": {"otp_message": {"otp": code}}},
        )

        # SMS: a plain SMS through Odoo's sms.sms and sms.ir, at once, with the WebOTP line
        self.assertEqual(len(self.smsir_calls), 1)
        sms = self.smsir_calls[0]
        self.assertEqual(sms["path"], "/send/bulk")
        self.assertEqual(sms["headers"]["X-API-KEY"], SMSIR_KEY)
        self.assertEqual(sms["timeout"], 8)
        self.assertEqual(sms["payload"]["mobiles"], ["09121234567"])
        self.assertEqual(sms["payload"]["lineNumber"], int(SMSIR_LINE))
        text = sms["payload"]["messageText"]
        self.assertIn(f"Your login code for {self.website.name}: {code}", text)
        self.assertRegex(text.splitlines()[-1], rf"^@[\w.\-]+ #{code}$")
        self.assertFalse(self.env["sms.sms"].sudo().search([("body", "ilike", code)]), "the SMS with the code is gone")

        record = self.otp.search([("challenge", "=", answer["challenge"])])
        self.assertEqual((record.sms_state, record.bale_state, record.phone), ("sent", "sent", NUMBER))
        self.assertNotIn(code, (record.code_hash or "") + (record.sms_info or "") + (record.bale_info or ""))
        self.assertEqual(len(record.code_hash), 64)

    def test_send_verify_template(self):
        self.env["ir.config_parameter"].sudo().set_str(PARAM + "sms_template_id", "123456")
        answer = self.send()
        self.assertTrue(answer["ok"])
        code = self.bale_code()
        self.assertEqual(len(self.smsir_calls), 1)
        self.assertEqual(self.smsir_calls[0]["path"], "/send/verify")
        self.assertEqual(
            self.smsir_calls[0]["payload"],
            {"mobile": "09121234567", "templateId": 123456, "parameters": [{"name": "Code", "value": code}]},
        )

    def test_bale_not_user_sms_still_ok(self):
        self.bale_answer = lambda payload: FakeResponse(
            {"error_data": [{"phone_number": NUMBER, "code": 17, "description": "NotBaleUser"}]}
        )
        answer = self.send()
        self.assertTrue(answer["ok"])
        self.assertEqual(answer["message"], "The code was sent by SMS.")
        self.assertEqual(answer["hint"], "This number has no Bale account; the code was sent by SMS.")
        record = self.otp.search([("challenge", "=", answer["challenge"])])
        self.assertEqual((record.sms_state, record.bale_state), ("sent", "failed"))
        self.assertIn("17", record.bale_info)

    def test_bale_only_and_errors(self):
        # sms.ir out of credit: Bale alone
        self.smsir_answer = lambda method, path, payload: FakeResponse({"status": 102, "message": "credit"}, 400)
        answer = self.send()
        self.assertTrue(answer["ok"])
        self.assertEqual(answer["message"], "The code was sent on Bale.")
        # both down: nothing sent, the code dies
        self.env["ir.config_parameter"].sudo().set_int(PARAM + "resend_delay", 0)
        self.bale_answer = lambda payload: FakeResponse(
            {"error_data": [{"code": 20, "description": "PaymentRequired"}]}
        )
        answer = self.send()
        self.assertFalse(answer["ok"])
        self.assertIn("could not be sent", answer["error"])
        self.assertEqual(self.otp.search([("phone", "=", NUMBER)], limit=1).state, "dead")

    def test_bale_client_errors(self):
        client = bale.SafirClient(BALE_KEY, BALE_BOT)
        self._otp_reset_mocks()
        for body, status, code in (
            ({"error_data": [{"code": 3, "description": "RateLimitExceeded"}]}, 200, bale.RATE_LIMIT),
            ({"error_data": [{"code": 8}]}, 400, bale.INVALID_PHONE),
            ({}, 500, bale.NETWORK_ERROR),
            ("not json", 502, bale.NETWORK_ERROR),
        ):
            self.bale_answer = lambda payload, body=body, status=status: FakeResponse(body, status)
            with self.mock_channels(), self.assertRaises(bale.BaleError) as error:
                client.send_otp(NUMBER, "123456")
            self.assertEqual(error.exception.code, code)
        self.bale_answer = lambda payload: FakeResponse({"message_id": "m-9"})
        with self.mock_channels():
            self.assertEqual(client.send_otp(NUMBER, "123456"), "m-9")
        ids = {call["payload"]["request_id"] for call in self.bale_calls}
        self.assertEqual(len(ids), len(self.bale_calls), "one request id per send")

    def test_invalid_number(self):
        answer = self.send("12345")
        self.assertFalse(answer["ok"])
        self.assertFalse(self.smsir_calls or self.bale_calls)

    def test_wrong_attempts_lock(self):
        answer = self.send()
        code = self.bale_code()
        wrong = "000000" if code != "000000" else "111111"
        for left in (4, 3, 2, 1):
            result = self.check(answer, wrong)
            self.assertFalse(result["ok"])
            self.assertEqual(result["attempts_left"], left)
        result = self.check(answer, wrong)
        self.assertTrue(result["dead"])
        self.assertIn("Too many wrong codes", result["error"])
        # the right code is useless now
        self.assertFalse(self.check(answer, code)["ok"])

    def test_expiry(self):
        answer = self.send()
        record = self.otp.search([("challenge", "=", answer["challenge"])])
        record.expire_at = fields.Datetime.now() - timedelta(seconds=1)
        result = self.check(answer, self.bale_code())
        self.assertFalse(result["ok"])
        self.assertIn("expired", result["error"])
        self.assertEqual(record.state, "dead")

    def test_session_bound(self):
        answer = self.send()
        result = self.check(answer, self.bale_code(), session="another-browser")
        self.assertFalse(result["ok"])

    def test_resend_delay_and_rate_limits(self):
        self.assertTrue(self.send()["ok"])
        again = self.send()
        self.assertFalse(again["ok"])
        self.assertTrue(0 < again["resend_in"] <= 61)
        params = self.env["ir.config_parameter"].sudo()
        params.set_int(PARAM + "resend_delay", 0)
        params.set_int(PARAM + "phone_limit", 3)
        self.assertTrue(self.send()["ok"])
        self.assertTrue(self.send()["ok"])
        limited = self.send()
        self.assertFalse(limited["ok"])
        self.assertIn("Too many codes", limited["error"])
        # per IP address
        params.set_int(PARAM + "ip_limit", 3)
        self.assertTrue(self.send("09351112233", ip="10.0.0.9")["ok"])
        self.assertFalse(self.send("09351112244", ip="10.0.0.1")["ok"], "10.0.0.1 has 3 codes already")
        self.assertTrue(self.send("09351112255", ip="10.0.0.2")["ok"])

    def test_only_latest_code_is_valid(self):
        self.env["ir.config_parameter"].sudo().set_int(PARAM + "resend_delay", 0)
        first = self.send()
        first_code = self.bale_code()
        second = self.send()
        self.assertFalse(self.check(first, first_code)["ok"])
        self.assertTrue(self.check(second, self.bale_code())["ok"])

    def test_generic_answer(self):
        """The answer to «send» is the same with and without an account."""
        new_test_user(self.env, login="09121234567", groups="base.group_portal", name="Has Account")
        with_account = self.send()
        without_account = self.send("09127654321")
        keys = ("ok", "message", "hint", "resend_in", "expires_in", "code_length")
        self.assertEqual({k: with_account[k] for k in keys}, {k: without_account[k] for k in keys})

    def test_login_token(self):
        user = new_test_user(self.env, login="customer@example.com", groups="base.group_portal", name="Customer")
        user.partner_id.phone = "+98 912 123 4567"  # set by a colleague: trusted
        answer = self.send()
        result = self.check(answer, self.bale_code())
        self.assertEqual(result["action"], "login")
        otp = self.otp._find_token(result["token"])
        self.assertEqual(otp.user_id, user)
        # the token logs in once, and only that user
        other = new_test_user(self.env, login="other@example.com", groups="base.group_portal")
        with self.assertRaises(AccessDenied):
            self.otp._consume_token(result["token"], other)
        self.otp._consume_token(result["token"], user)
        self.assertEqual(user.partner_id.vesta_otp_verified_mobile, NUMBER)
        with self.assertRaises(AccessDenied):
            self.otp._consume_token(result["token"], user)
        info = {"uid": user.id}
        with self.assertRaises(AccessDenied):
            user.with_user(user)._check_credentials({"type": "vesta_otp", "otp_token": "bogus"}, info)

    def test_untrusted_phone_does_not_open_account(self):
        user = new_test_user(self.env, login="victim@example.com", groups="base.group_portal", name="Someone")
        # the customer typed the number of someone else on the website
        user.partner_id.with_user(user).sudo().write({"phone": "09121234567"})
        self.assertTrue(user.partner_id.vesta_otp_phone_untrusted)
        result = self.check(self.send(), self.bale_code())
        self.assertEqual(result["action"], "signup", "the number is not linked to that account")

    def test_internal_users(self):
        user = new_test_user(self.env, login="09121234567", groups="base.group_user", name="Colleague")
        result = self.check(self.send(), self.bale_code())
        self.assertFalse(result["ok"])
        self.env["ir.config_parameter"].sudo().set_int(PARAM + "resend_delay", 0)
        self.env["ir.config_parameter"].sudo().set_bool(PARAM + "allow_internal", True)
        result = self.check(self.send(), self.bale_code())
        self.assertEqual(result["action"], "login")
        self.assertEqual(self.otp._find_token(result["token"]).user_id, user)

    def test_signup_and_disabled_signup(self):
        self.website.auth_signup_uninvited = "b2c"
        answer = self.send()
        result = self.check(answer, self.bale_code())
        self.assertEqual(result["action"], "signup")
        self.assertFalse(self.otp._signup(answer["challenge"], result["token"], " ", session_id="s1")["ok"])
        done = self.otp.with_context(website_id=self.website.id)._signup(
            answer["challenge"], result["token"], "  Sara   Ahmadi ", session_id="s1"
        )
        self.assertTrue(done["ok"])
        user = self.otp._find_token(done["token"]).user_id
        self.assertEqual(user.name, "Sara Ahmadi")
        self.assertEqual(user.login, "09121234567")
        self.assertTrue(user.share)
        self.assertTrue(user._is_portal())
        self.assertEqual(user.partner_id.vesta_otp_verified_mobile, NUMBER)
        self.assertEqual(user.partner_id.phone, "+989121234567")

        self.website.auth_signup_uninvited = "b2b"
        self.env["ir.config_parameter"].sudo().set_int(PARAM + "resend_delay", 0)
        answer = self.send("09127654321")
        result = self.check(answer, self.bale_code())
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "No account was found with this mobile number.")

    def test_change_mobile(self):
        user = new_test_user(self.env, login="09120000001", groups="base.group_portal", name="Mover")
        user.partner_id._vesta_otp_set_verified("989120000001")
        answer = self.send(purpose="change", user=user)
        self.assertTrue(answer["ok"])
        result = self.check(answer, self.bale_code(), user=user)
        self.assertEqual(result["action"], "changed")
        self.assertEqual(user.partner_id.vesta_otp_verified_mobile, NUMBER)
        self.assertEqual(user.login, "09121234567", "the old number no longer opens the account")
        self.assertEqual(user.partner_id.phone, "+989121234567")

    def test_change_mobile_taken(self):
        new_test_user(self.env, login="09121234567", groups="base.group_portal", name="Owner")
        user = new_test_user(self.env, login="mover@example.com", groups="base.group_portal", name="Mover")
        answer = self.send(purpose="change", user=user)
        result = self.check(answer, self.bale_code(), user=user)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "This number belongs to another account.")

    def test_test_mode_never_calls_network(self):
        self.env["ir.config_parameter"].sudo().set_bool(PARAM + "test_mode", True)
        self.env["ir.config_parameter"].sudo().set_str(PARAM + "sms_template_id", "123456")
        with self.no_network():
            answer = self.otp._request_code("09121234567", ip="10.0.0.1", session_id="s1", website=self.website)
            self.assertTrue(answer["ok"])
            self.assertRegex(answer["test_code"], r"^\d{6}$")
            self.assertIn(answer["test_code"], answer["message"])
            self.assertEqual(self.check(answer, answer["test_code"])["action"], "signup")
            # the test buttons of the settings do not go out either
            settings = self.env["res.config.settings"].create(
                {
                    "vesta_otp_test_mode": True,
                    "vesta_otp_bale_api_key": BALE_KEY,
                    "vesta_otp_bale_bot_id": BALE_BOT,
                    "vesta_otp_test_mobile": "09121234567",
                }
            )
            for action in (settings.action_vesta_otp_bale_test(), settings.action_vesta_otp_sms_test()):
                self.assertEqual(action["params"]["type"], "info")
                self.assertIn("Test mode", action["params"]["message"])
        self.assertEqual(self.network_calls, [])
        record = self.otp.search([("challenge", "=", answer["challenge"])])
        self.assertEqual((record.sms_state, record.bale_state), ("test", "test"))
        self.assertFalse(self.env["sms.sms"].sudo().search([("body", "ilike", answer["test_code"])]))

    def test_code_length_setting(self):
        self.env["ir.config_parameter"].sudo().set_int(PARAM + "code_length", 4)
        answer = self.send()
        self.assertEqual(answer["code_length"], 4)
        self.assertRegex(self.bale_code(), r"^\d{4}$")
        self.assertTrue(self.check(answer, phone.ascii_digits("") + self.bale_code())["ok"])

    def test_persian_digits_code(self):
        answer = self.send()
        persian = self.bale_code().translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
        self.assertTrue(self.check(answer, persian)["ok"])

    def test_purge(self):
        answer = self.send()
        record = self.otp.search([("challenge", "=", answer["challenge"])])
        self.env.cr.execute(
            "UPDATE vesta_auth_otp SET create_date = now() - interval '2 days' WHERE id = %s", [record.id]
        )
        record.invalidate_recordset()
        self.assertEqual(self.otp._cron_purge(), 1)
        self.assertFalse(record.exists())
