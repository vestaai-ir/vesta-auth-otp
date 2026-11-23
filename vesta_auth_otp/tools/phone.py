# Copyright 2026 Vesta AI (https://vestaai.ir)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""Iranian mobile numbers: one normal form for matching, sending and storing."""

from odoo.addons.vesta_marketing.tools.smsir import iran_mobile

_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_ASCII_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize(number):
    """``98XXXXXXXXXX`` (98 and the 10 digits of the mobile), or ``None`` for anything else.

    Accepts ``09…``, ``9…``, ``+98…``, ``0098…`` and ``98…``, with spaces or dashes and Persian or Arabic digits.
    """
    if not isinstance(number, str):
        return None
    local = iran_mobile(number)
    return "98" + local[1:] if local else None


def local(normal):
    """``09XXXXXXXXX`` of a normalized number (the way people type it)."""
    return "0" + normal[2:] if normal else ""


def e164(normal):
    """``+98XXXXXXXXXX`` of a normalized number (the way Odoo stores phone numbers)."""
    return "+" + normal if normal else ""


def variants(normal):
    """The ways a normalized number may be written as a login."""
    if not normal:
        return []
    return [normal, local(normal), e164(normal), normal[2:], "00" + normal]


def display(normal, lang=None):
    """``0912 123 4567``, in Persian digits for Persian."""
    if not normal:
        return ""
    number = local(normal)
    text = f"{number[:4]} {number[4:7]} {number[7:]}"
    if lang and lang.startswith("fa"):
        text = text.translate(_PERSIAN_DIGITS)
    return text


def mask(normal):
    """``98912***4567``, for the logs."""
    if not normal:
        return "-"
    return normal[:5] + "***" + normal[-4:]


def ascii_digits(text):
    """Persian and Arabic digits of ``text`` as ASCII digits."""
    return (text or "").translate(_ASCII_DIGITS)
