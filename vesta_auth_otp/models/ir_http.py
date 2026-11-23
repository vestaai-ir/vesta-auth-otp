# Copyright 2026 Vesta AI (https://vestaai.ir)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _get_translation_frontend_modules_name(cls):
        """Serve the web terms of this module (the login card) on the website."""
        return [*super()._get_translation_frontend_modules_name(), "vesta_auth_otp"]
