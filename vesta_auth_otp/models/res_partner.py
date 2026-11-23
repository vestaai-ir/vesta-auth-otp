# Copyright 2026 Vesta AI (https://vestaai.ir)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models

from ..tools import phone


class ResPartner(models.Model):
    _inherit = "res.partner"

    vesta_otp_mobile = fields.Char(
        "Normalized Mobile",
        compute="_compute_vesta_otp_mobile",
        store=True,
        index="btree_not_null",
        help="The phone as 98 and 10 digits when it is an Iranian mobile, to find the account of a login code.",
    )
    vesta_otp_verified_mobile = fields.Char(
        "Verified Mobile",
        copy=False,
        readonly=True,
        index="btree_not_null",
        help="The mobile number this contact proved with a login code (98 and 10 digits).",
    )
    vesta_otp_phone_untrusted = fields.Boolean(
        "Phone Typed on the Website",
        copy=False,
        readonly=True,
        help="The phone was set on the website (checkout, portal): it does not open an account with a login code"
        " until it is verified.",
    )

    @api.depends("phone")
    def _compute_vesta_otp_mobile(self):
        for partner in self:
            partner.vesta_otp_mobile = phone.normalize(partner.phone or "")

    @api.model
    def _vesta_otp_trusted_writer(self):
        """Phones set by colleagues (or the system) are trusted; phones typed by visitors or customers are not."""
        return self.env.user._is_internal()

    @api.model_create_multi
    def create(self, vals_list):
        if not self._vesta_otp_trusted_writer():
            for vals in vals_list:
                if vals.get("phone") and "vesta_otp_phone_untrusted" not in vals:
                    vals["vesta_otp_phone_untrusted"] = True
        return super().create(vals_list)

    def write(self, vals):
        if "phone" in vals and "vesta_otp_phone_untrusted" not in vals:
            vals = dict(vals, vesta_otp_phone_untrusted=bool(vals["phone"]) and not self._vesta_otp_trusted_writer())
        return super().write(vals)

    def _vesta_otp_set_verified(self, normal):
        """``normal`` is the proven mobile of this contact, and of no other one."""
        self.ensure_one()
        partners = self.sudo()
        partners.search([("vesta_otp_verified_mobile", "=", normal), ("id", "!=", self.id)]).write(
            {"vesta_otp_verified_mobile": False}
        )
        values = {"vesta_otp_verified_mobile": normal}
        if partners.vesta_otp_mobile == normal:
            values["vesta_otp_phone_untrusted"] = False
        partners.write(values)

    def _vesta_otp_mobile_display(self):
        self.ensure_one()
        return phone.display(self.sudo().vesta_otp_verified_mobile, self.env.lang)
