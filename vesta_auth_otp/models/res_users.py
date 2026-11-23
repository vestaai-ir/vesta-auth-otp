# Copyright 2026 Vesta AI (https://vestaai.ir)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import models
from odoo.exceptions import AccessDenied
from odoo.http import request

CREDENTIAL_TYPE = "vesta_otp"


class ResUsers(models.Model):
    _inherit = "res.users"

    def _login(self, credential, user_agent_env):
        """``{"type": "vesta_otp", "otp_token": …}``: the token of a right login code gives the login."""
        if credential.get("type") == CREDENTIAL_TYPE:
            session_id = request.session.sid if request else None
            otp = self.env["vesta.auth.otp"].sudo()._find_token(credential.get("otp_token"), session_id)
            if not otp.user_id:
                raise AccessDenied()
            credential["login"] = otp.user_id.login
        return super()._login(credential, user_agent_env=user_agent_env)

    def _check_credentials(self, credential, env):
        if credential["type"] == CREDENTIAL_TYPE:
            self.env["vesta.auth.otp"].sudo()._consume_token(credential.get("otp_token"), self.env.user)
            # "default": two-factor authentication (TOTP, e-mail codes) still applies
            return {"uid": self.env.user.id, "auth_method": CREDENTIAL_TYPE, "mfa": "default"}
        return super()._check_credentials(credential, env)
