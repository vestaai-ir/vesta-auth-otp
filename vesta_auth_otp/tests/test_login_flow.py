# Copyright 2026 Vesta AI (https://vestaai.ir)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import re

from odoo.http.session import session_store
from odoo.tests import HttpCase, new_test_user, tagged

from ..models.vesta_auth_otp import PARAM
from .common import OtpMockMixin


@tagged("post_install", "-at_install")
class TestOtpLoginFlow(OtpMockMixin, HttpCase):
    """The browser side: /vesta_otp/* then the form post to /web/login opens a real session."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._otp_setup_settings(cls.env)
        cls.website = cls.env["website"].browse(1)
        cls.website.auth_signup_uninvited = "b2c"

    def setUp(self):
        super().setUp()
        self._otp_reset_mocks()

    def csrf(self, url="/web/login"):
        page = self.url_open(url)
        self.assertEqual(page.status_code, 200)
        return re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1), page.text

    def rpc(self, route, **params):
        with self.mock_channels():
            return self.make_jsonrpc_request(route, params)

    def session_uid(self):
        """The user of the session of the test browser (None: public)."""
        return session_store().get(self.opener.cookies.get("session_id") or "", keep_sid=True).uid

    def login_with_code(self, number, redirect="", name=None):
        csrf, _page = self.csrf("/web/login?redirect=" + redirect if redirect else "/web/login")
        sent = self.rpc("/vesta_otp/send", phone=number)
        self.assertTrue(sent["ok"], sent)
        verified = self.rpc("/vesta_otp/verify", challenge=sent["challenge"], code=self.bale_code())
        self.assertTrue(verified["ok"], verified)
        if verified["action"] == "signup":
            self.assertTrue(name, "a name is asked for a new account")
            verified = self.rpc("/vesta_otp/signup", challenge=sent["challenge"], token=verified["token"], name=name)
            self.assertTrue(verified["ok"], verified)
        response = self.url_open(
            "/web/login",
            data={
                "csrf_token": csrf,
                "type": "vesta_otp",
                "otp_token": verified["token"],
                "password": "",
                "redirect": redirect,
            },
            allow_redirects=False,
        )
        return response

    def test_login_page_shows_card(self):
        _csrf, page = self.csrf()
        self.assertIn("o_vesta_otp o_vo_active", page)
        self.assertIn('autocomplete="one-time-code"', page)
        self.assertIn('name="otp_token"', page)
        # disabled: the usual page
        self.env["ir.config_parameter"].sudo().set_bool(PARAM + "enabled", False)
        _csrf, page = self.csrf()
        self.assertNotIn("o_vesta_otp", page)
        self.assertIn("oe_login_form", page)

    def test_login_existing_user_opens_session(self):
        user = new_test_user(self.env, login="buyer@example.com", groups="base.group_portal", name="Buyer")
        user.partner_id.phone = "09121234567"
        self.assertFalse(self.session_uid())
        response = self.login_with_code("۰۹۱۲۱۲۳۴۵۶۷", redirect="/shop/checkout")
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.headers["Location"].endswith("/shop/checkout"))
        self.assertEqual(self.session_uid(), user.id)
        self.assertEqual(user.partner_id.vesta_otp_verified_mobile, "989121234567")
        # the same token cannot log in twice
        self.url_open("/web/session/logout", data={"csrf_token": self.csrf()[0]})
        self.assertFalse(self.session_uid())

    def test_signup_creates_portal_user(self):
        response = self.login_with_code("09359876543", name="Reza Karimi")
        self.assertEqual(response.status_code, 303)
        user = self.env["res.users"].search([("login", "=", "09359876543")])
        self.assertTrue(user)
        self.assertTrue(user._is_portal())
        self.assertEqual(user.name, "Reza Karimi")
        self.assertEqual(self.session_uid(), user.id)

    def test_used_token_is_refused(self):
        user = new_test_user(self.env, login="09121112233", groups="base.group_portal", name="Again")
        csrf, _page = self.csrf()
        sent = self.rpc("/vesta_otp/send", phone="09121112233")
        verified = self.rpc("/vesta_otp/verify", challenge=sent["challenge"], code=self.bale_code())
        data = {"csrf_token": csrf, "type": "vesta_otp", "otp_token": verified["token"], "password": ""}
        self.url_open("/web/login", data=data, allow_redirects=False)
        self.assertEqual(self.session_uid(), user.id)
        self.url_open("/web/session/logout", data={"csrf_token": self.csrf()[0]})
        csrf, _page = self.csrf()
        data["csrf_token"] = csrf
        response = self.url_open("/web/login", data=data)
        self.assertEqual(response.status_code, 200)
        # the card shows its error (in the language of the website), the password form none
        self.assertRegex(response.text, r'class="o_vo_error alert alert-danger\s*"')
        self.assertNotIn("Wrong login/password", response.text)
        self.assertFalse(self.session_uid())

    def test_two_factor_still_applies(self):
        if "totp_secret" not in self.env["res.users"]._fields:
            self.skipTest("auth_totp is not installed")
        user = new_test_user(self.env, login="09121119999", groups="base.group_portal", name="Careful")
        self.env.cr.execute("UPDATE res_users SET totp_secret = %s WHERE id = %s", ["JBSWY3DPEHPK3PXP", user.id])
        user.invalidate_recordset()
        response = self.login_with_code("09121119999")
        self.assertEqual(response.status_code, 303)
        self.assertIn("/web/login/totp", response.headers["Location"])
        self.assertFalse(self.session_uid(), "the second factor is still asked for")

    def test_change_mobile_from_portal(self):
        user = new_test_user(self.env, login="portal-otp", password="portal-otp-pass", groups="base.group_portal")
        self.authenticate("portal-otp", "portal-otp-pass")
        page = self.url_open("/my/account")
        self.assertIn("o_vo_account", page.text)
        sent = self.rpc("/vesta_otp/send", phone="09127770000", purpose="change")
        self.assertTrue(sent["ok"], sent)
        result = self.rpc("/vesta_otp/verify", challenge=sent["challenge"], code=self.bale_code())
        self.assertEqual(result["action"], "changed")
        self.assertEqual(user.partner_id.vesta_otp_verified_mobile, "989127770000")

    def test_test_mode_page_and_no_network(self):
        self.env["ir.config_parameter"].sudo().set_bool(PARAM + "test_mode", True)
        _csrf, page = self.csrf()
        self.assertIn("o_vo_test_badge", page)
        with self.no_network():
            sent = self.make_jsonrpc_request("/vesta_otp/send", {"phone": "09121234567"})
            self.assertTrue(sent["ok"])
            result = self.make_jsonrpc_request(
                "/vesta_otp/verify", {"challenge": sent["challenge"], "code": sent["test_code"]}
            )
        self.assertTrue(result["ok"])
        self.assertEqual(self.network_calls, [])
