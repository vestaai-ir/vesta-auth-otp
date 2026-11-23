# Copyright 2026 Vesta AI (https://vestaai.ir)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import http
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.web.controllers.home import CREDENTIAL_PARAMS
from odoo.http import request

from ..models.res_users import CREDENTIAL_TYPE

# the login form posts the one-time token of a right code
if "otp_token" not in CREDENTIAL_PARAMS:
    CREDENTIAL_PARAMS.append("otp_token")


def _otp_model():
    return request.env["vesta.auth.otp"].sudo()


def _disabled():
    return {"ok": False, "error": request.env._("Login with mobile is not enabled."), "dead": True}


def _client_ip():
    return request.httprequest.remote_addr or ""


class VestaAuthOtpHome(AuthSignupHome):
    """The login and sign-up pages offer the mobile number first."""

    def _vesta_otp_values(self, mode):
        otp_model = _otp_model()
        settings = otp_model._otp_settings()
        if not settings["enabled"]:
            return None
        return {
            "mode": mode,
            "test_mode": settings["test_mode"],
            "code_length": settings["code_length"],
            "signup_enabled": request.env["res.users"].sudo()._get_signup_invitation_scope() == "b2c",
        }

    @http.route()
    def web_login(self, *args, **kw):
        response = super().web_login(*args, **kw)
        qcontext = getattr(response, "qcontext", None)
        if qcontext is not None and response.is_qweb:
            otp = self._vesta_otp_values("login")
            qcontext["vesta_otp"] = otp
            if otp:
                failed_code = request.httprequest.method == "POST" and request.params.get("type") == CREDENTIAL_TYPE
                if failed_code:
                    qcontext["error"] = None
                    otp["error"] = request.env._("This code is no longer valid. Ask for a new one.")
                # the password form first after a wrong password, or with a login in the link
                otp["start"] = "password" if (qcontext.get("error") or qcontext.get("login")) else "otp"
        return response

    @http.route()
    def web_auth_signup(self, *args, **kw):
        response = super().web_auth_signup(*args, **kw)
        qcontext = getattr(response, "qcontext", None)
        if qcontext is not None and response.is_qweb:
            otp = self._vesta_otp_values("signup")
            if otp and otp["signup_enabled"]:
                otp["start"] = "password" if (qcontext.get("error") or qcontext.get("login")) else "otp"
                qcontext["vesta_otp"] = otp
        return response


class VestaAuthOtpController(http.Controller):
    @http.route("/vesta_otp/send", type="jsonrpc", auth="public", website=True, methods=["POST"], sitemap=False)
    def vesta_otp_send(self, phone=None, purpose="login", **kw):
        otp_model = _otp_model()
        if not otp_model._otp_enabled():
            return _disabled()
        user = None
        if purpose == "change":
            if request.env.user._is_public():
                return {"ok": False, "error": request.env._("Log in first."), "dead": True}
            user = request.env.user
        elif purpose != "login":
            return {"ok": False, "error": request.env._("Unknown request."), "dead": True}
        elif not request.env.user._is_public():
            return {"ok": False, "error": request.env._("You are already logged in."), "dead": True}
        return otp_model._request_code(
            phone,
            purpose=purpose,
            ip=_client_ip(),
            session_id=request.session.sid,
            website=request.env.website,
            user=user,
        )

    @http.route("/vesta_otp/verify", type="jsonrpc", auth="public", website=True, methods=["POST"], sitemap=False)
    def vesta_otp_verify(self, challenge=None, code=None, **kw):
        otp_model = _otp_model()
        if not otp_model._otp_enabled():
            return _disabled()
        user = None if request.env.user._is_public() else request.env.user
        return otp_model._check_code(
            challenge, code, session_id=request.session.sid, website=request.env.website, user=user
        )

    @http.route("/vesta_otp/signup", type="jsonrpc", auth="public", website=True, methods=["POST"], sitemap=False)
    def vesta_otp_signup(self, challenge=None, token=None, name=None, **kw):
        otp_model = _otp_model()
        if not otp_model._otp_enabled():
            return _disabled()
        if request.env["res.users"].sudo()._get_signup_invitation_scope() != "b2c":
            return {"ok": False, "error": request.env._("No account was found with this mobile number."), "dead": True}
        return otp_model._signup(challenge, token, name, session_id=request.session.sid, lang=request.env.lang)
