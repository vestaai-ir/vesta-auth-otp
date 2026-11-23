# Copyright 2026 Vesta AI (https://vestaai.ir)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Vesta Mobile Login",
    "summary": "Customers log in and sign up on the website with their mobile number and a one-time code,"
    " sent by SMS (sms.ir) and Bale at the same time",
    "version": "20.0.1.0.0",
    "category": "Website/Website",
    "website": "https://vestaai.ir/odoo/modules/vesta-auth-otp",
    "author": "Vesta AI",
    "license": "LGPL-3",
    "installable": True,
    "depends": ["auth_signup", "portal", "website", "vesta_marketing"],
    "data": [
        "security/ir.access.csv",
        "data/ir_cron_data.xml",
        "views/vesta_auth_otp_views.xml",
        "views/res_config_settings_views.xml",
        "views/login_templates.xml",
        "views/portal_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "vesta_auth_otp/static/src/scss/vesta_auth_otp.scss",
            "vesta_auth_otp/static/src/interactions/otp_login.js",
        ],
    },
    "images": ["static/description/banner.png"],
}
