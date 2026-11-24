# Copyright 2026 Vesta AI (https://vestaai.ir)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
# ruff: noqa: E501
"""Persian translation of Vesta Mobile Login.

Run after ``odoo i18n export vesta_auth_otp`` to rebuild ``i18n/fa.po``:

    python3 tools/fa_terms.py

Missing terms are printed and left empty, so nothing ships half-translated by surprise.
"""

import pathlib
import sys

import polib

Z = "‌"  # zero-width non-joiner

TERMS = {
    # module
    "Vesta Mobile Login": "ورود با موبایل وستا",
    "Customers log in and sign up on the website with their mobile number and a one-time code, sent by SMS (sms.ir) and Bale at the same time": f"ورود و ثبت{Z}نام مشتری{Z}ها در وب{Z}سایت با شماره{Z}ی موبایل و کد یک{Z}بارمصرف که هم{Z}زمان با پیامک (sms.ir) و بله ارسال می{Z}شود",
    # models and fields
    "Mobile Login Code": "کد ورود با موبایل",
    "Config Settings": "تنظیمات پیکربندی",
    "Contact": "مخاطب",
    "Create a Customer": "ایجاد مشتری",
    "HTTP Routing": "مسیریابی HTTP",
    "Outgoing SMS": "پیامک خروجی",
    "User": "کاربر",
    "Display Name": "نام نمایشی",
    "ID": "شناسه",
    "Created by": "ایجاد شده توسط",
    "Created on": "ایجاد شده در",
    "Last Updated by": f"آخرین به{Z}روزرسانی توسط",
    "Last Updated on": f"آخرین به{Z}روزرسانی در",
    "Mobile": "موبایل",
    "98 and the 10 digits of the mobile.": f"۹۸ و ۱۰ رقم شماره{Z}ی موبایل.",
    "Purpose": "کاربرد",
    "Login or sign-up": f"ورود یا ثبت{Z}نام",
    "Change of mobile": f"تغییر شماره{Z}ی موبایل",
    "Website": f"وب{Z}سایت",
    "IP Address": "نشانی IP",
    "Session Hash": f"درهم{Z}سازی نشست",
    "Challenge": f"شناسه{Z}ی درخواست",
    "Salt": "نمک",
    "Code Hash": f"درهم{Z}سازی کد",
    "Wrong Attempts": f"تلاش{Z}های نادرست",
    "Expires": "انقضا",
    "State": "وضعیت",
    "Waiting for the code": "در انتظار کد",
    "Code verified": "کد تأیید شد",
    "Used": "استفاده شد",
    "Dead": "باطل",
    "SMS Details": "جزئیات پیامک",
    "Bale Details": "جزئیات بله",
    "Sent": "ارسال شد",
    "Failed": "ناموفق",
    "Off": "خاموش",
    "Test mode": "حالت آزمایشی",
    "Token Hash": f"درهم{Z}سازی توکن",
    "Token Expire At": "انقضای توکن",
    "Normalized Mobile": "موبایل استاندارد",
    "The phone as 98 and 10 digits when it is an Iranian mobile, to find the account of a login code.": "تلفن به شکل ۹۸ و ۱۰ رقم، وقتی موبایل ایرانی باشد؛ برای پیدا کردن حسابِ یک کد ورود.",
    "Verified Mobile": "موبایل تأییدشده",
    "The mobile number this contact proved with a login code (98 and 10 digits).": f"شماره{Z}ی موبایلی که این مخاطب با کد ورود تأیید کرده است (۹۸ و ۱۰ رقم).",
    "Phone Typed on the Website": f"تلفن واردشده در وب{Z}سایت",
    "The phone was set on the website (checkout, portal): it does not open an account with a login code until it is verified.": f"این تلفن در وب{Z}سایت (تسویه{Z}حساب، پرتال) وارد شده است و تا تأیید نشود، با کد ورود حسابی را باز نمی{Z}کند.",
    # settings
    "Login with Mobile": "ورود با موبایل",
    "Customers log in and sign up on the website with their mobile number and a one-time code.": f"مشتری{Z}ها با شماره{Z}ی موبایل و کد یک{Z}بارمصرف وارد وب{Z}سایت می{Z}شوند یا ثبت{Z}نام می{Z}کنند.",
    "Customers log in and sign up with their mobile number and a one-time code sent by SMS and Bale at the same time. The password login stays available.": f"مشتری{Z}ها با شماره{Z}ی موبایل و کد یک{Z}بارمصرفی که هم{Z}زمان با پیامک و بله ارسال می{Z}شود وارد می{Z}شوند یا ثبت{Z}نام می{Z}کنند. ورود با رمز عبور همچنان در دسترس است.",
    "Colleagues Too": "همکاران هم",
    "Internal users may log in with a code too (two-factor authentication still applies). Off: only customers (portal users).": f"کاربران داخلی هم می{Z}توانند با کد وارد شوند (ورود دومرحله{Z}ای همچنان اعمال می{Z}شود). خاموش: فقط مشتری{Z}ها (کاربران پرتال).",
    "Test Mode": "حالت آزمایشی",
    "Nothing is sent: the code is shown on the login page and written in the server log. Turn it off once sms.ir or Bale is set up; never leave it on for real customers.": f"چیزی ارسال نمی{Z}شود: کد در صفحه{Z}ی ورود نمایش داده و در گزارش سرور نوشته می{Z}شود. پس از راه{Z}اندازی sms.ir یا بله خاموشش کنید؛ هرگز برای مشتری{Z}های واقعی روشن نگذارید.",
    '<i class="oi" data-icon="warning" aria-hidden="true"/>\n                            In test mode anyone can log in with any number: use it only to try the module.': f'<i class="oi" data-icon="warning" aria-hidden="true"/>\n                            در حالت آزمایشی هر کسی با هر شماره{Z}ای می{Z}تواند وارد شود: فقط برای آزمودن ماژول از آن استفاده کنید.',
    "Codes": "کدها",
    "Length and lifetime of the codes, and when a new code may be asked for.": f"طول و مدت اعتبار کدها، و این{Z}که کی می{Z}توان کد تازه خواست.",
    "Code Length": "طول کد",
    "Code Lifetime (seconds)": "مدت اعتبار کد (ثانیه)",
    "Resend After (seconds)": "ارسال دوباره پس از (ثانیه)",
    "Limits": f"محدودیت{Z}ها",
    "A code dies after too many wrong attempts; numbers and addresses that ask for too many codes wait.": f"کد پس از تلاش{Z}های نادرست زیاد باطل می{Z}شود؛ شماره{Z}ها و نشانی{Z}هایی که کد زیادی بخواهند باید صبر کنند.",
    "Wrong Attempts per Code": "تلاش نادرست برای هر کد",
    "Codes per Number per Hour": "کد برای هر شماره در ساعت",
    "Codes per IP Address per Hour": "کد برای هر نشانی IP در ساعت",
    "Send by SMS": "ارسال با پیامک",
    "Through the SMS of Vesta Marketing (sms.ir). With the id of an approved «verify» template the code goes out with the fast send of sms.ir; without it, as a plain SMS sent at once.": f"از راه پیامک وستا مارکتینگ (sms.ir). با شناسه{Z}ی یک قالب تأییدشده{Z}ی «ارسال سریع»، کد با ارسال سریع sms.ir می{Z}رود؛ بدون آن، به شکل پیامک ساده و فوری.",
    "sms.ir Template ID": f"شناسه{Z}ی قالب sms.ir",
    "Optional: the id of an approved «verify» template of sms.ir (fast send). Empty: a plain SMS.": f"اختیاری: شناسه{Z}ی یک قالب تأییدشده{Z}ی «ارسال سریع» در sms.ir. خالی: پیامک ساده.",
    "Template Parameter": "پارامتر قالب",
    "The name of the parameter of the template that receives the code (#Code# in the template: Code).": f"نام پارامتری از قالب که کد را می{Z}گیرد (#Code# در قالب: Code).",
    "Code": "Code",
    "Send a test SMS": "ارسال پیامک آزمایشی",
    "Send on Bale": "ارسال در بله",
    "Safir, the code service of Bale: Bale sends the code from its own verification bot to the Bale account of the number.": f"سفیر، سرویس کد بله: بله کد را از بات تأیید خودش به حساب بله{Z}ی همان شماره می{Z}فرستد.",
    "Safir API Key": "کلید API سفیر",
    "Bot ID": f"شناسه{Z}ی بات",
    "Send a test message on Bale": "ارسال پیام آزمایشی در بله",
    "Get the key and the bot ID in Bale Business": f"کلید و شناسه{Z}ی بات را از بله کسب{Z}وکار بگیرید",
    "Login Test Mobile": "موبایل آزمایشی ورود",
    "Test Mobile": "موبایل آزمایشی",
    "The number that receives the test SMS and the test Bale message.": f"شماره{Z}ای که پیامک آزمایشی و پیام آزمایشی بله را دریافت می{Z}کند.",
    "Login codes": "کدهای ورود",
    "Login Codes": "کدهای ورود",
    "Login with Mobile: delete old codes": "ورود با موبایل: حذف کدهای قدیمی",
    "Date": "تاریخ",
    "SMS Failed": "پیامک ناموفق",
    "Bale Failed": "بله ناموفق",
    "Logged In": "وارد شد",
    "No login code was asked for yet": "هنوز کد ورودی درخواست نشده است",
    "Every code asked for on the website is listed here for a day, with how it was sent. The codes themselves are never stored.": f"هر کدی که در وب{Z}سایت درخواست شود، همراه با چگونگی ارسالش، یک روز این{Z}جا می{Z}ماند. خود کدها هرگز ذخیره نمی{Z}شوند.",
    # settings: messages
    "The code has 4 to 6 digits.": "کد ۴ تا ۶ رقم دارد.",
    "A code lives 30 to 900 seconds.": "اعتبار کد ۳۰ تا ۹۰۰ ثانیه است.",
    "The resend delay is 0 to 600 seconds.": f"فاصله{Z}ی ارسال دوباره ۰ تا ۶۰۰ ثانیه است.",
    "The limits are at least 1.": f"محدودیت{Z}ها دست{Z}کم ۱ هستند.",
    "The bot ID of Bale is a number.": f"شناسه{Z}ی بات بله عدد است.",
    "The template ID of sms.ir is a number.": f"شناسه{Z}ی قالب sms.ir عدد است.",
    "Enter the test mobile (an Iranian mobile number) first.": f"اول موبایل آزمایشی (یک شماره{Z}ی موبایل ایرانی) را وارد کنید.",
    "Enter the Safir API key and the bot ID (a number) of Bale first.": f"اول کلید API سفیر و شناسه{Z}ی بات بله (عدد) را وارد کنید.",
    "Bale": "بله",
    "Bale (test mode)": "بله (حالت آزمایشی)",
    "SMS": "پیامک",
    "SMS (test mode)": "پیامک (حالت آزمایشی)",
    "Test mode: nothing was sent. The settings look right; Bale would get the code %(code)s for %(phone)s. Turn test mode off to send a real test message.": f"حالت آزمایشی: چیزی ارسال نشد. تنظیمات درست به نظر می{Z}رسد؛ بله کد %(code)s را برای %(phone)s می{Z}فرستاد. برای ارسال پیام آزمایشی واقعی، حالت آزمایشی را خاموش کنید.",
    "Test mode: nothing was sent. The SMS to %(phone)s would read: %(text)s": f"حالت آزمایشی: چیزی ارسال نشد. پیامک %(phone)s این می{Z}شد: %(text)s",
    "The test message was not sent: %(error)s": "پیام آزمایشی ارسال نشد: %(error)s",
    "The test SMS was not sent: %(error)s": "پیامک آزمایشی ارسال نشد: %(error)s",
    "Test code %(code)s sent to %(phone)s (message %(id)s).": "کد آزمایشی %(code)s به %(phone)s ارسال شد (پیام %(id)s).",
    "Test code %(code)s sent to %(phone)s.": "کد آزمایشی %(code)s به %(phone)s ارسال شد.",
    "Bale had an internal error; try again later.": "بله خطای داخلی داشت؛ بعداً دوباره امتحان کنید.",
    "Too many requests; try again in a minute.": f"درخواست{Z}ها زیاد است؛ یک دقیقه{Z}ی دیگر دوباره امتحان کنید.",
    "Bale rejected the request; check the bot ID.": f"بله درخواست را نپذیرفت؛ شناسه{Z}ی بات را بررسی کنید.",
    "The number is not valid for Bale.": "شماره برای بله معتبر نیست.",
    "This number has no Bale account.": "این شماره در بله حساب ندارد.",
    "The Safir account has no credit.": "حساب سفیر اعتبار ندارد.",
    "The Safir account reached its contact limit.": "حساب سفیر به سقف مخاطبانش رسیده است.",
    "Bale could not be reached, or the API key was rejected.": "به بله دسترسی نبود، یا کلید API پذیرفته نشد.",
    # login card
    '<i class="oi" data-icon="science" aria-hidden="true"/>\n                    <span>Test mode: nothing is sent, the code is shown here.</span>': f'<i class="oi" data-icon="science" aria-hidden="true"/>\n                    <span>حالت آزمایشی: چیزی ارسال نمی{Z}شود، کد همین{Z}جا نمایش داده می{Z}شود.</span>',
    "Log in or sign up": f"ورود یا ثبت{Z}نام",
    "Sign up with your mobile": f"ثبت{Z}نام با موبایل",
    "Change your mobile number": f"تغییر شماره{Z}ی موبایل",
    "Enter the new number; we send it a code to make sure it is yours.": f"شماره{Z}ی تازه را وارد کنید؛ برای اطمینان از این{Z}که مال شماست، به آن کد می{Z}فرستیم.",
    "Enter your mobile number; we send you a one-time code.": f"شماره{Z}ی موبایل خود را وارد کنید؛ یک کد یک{Z}بارمصرف برایتان می{Z}فرستیم.",
    "Mobile number": f"شماره{Z}ی موبایل",
    "<span>Get the code</span>": "<span>دریافت کد</span>",
    "Enter the code": "کد را وارد کنید",
    '<span>The code was sent to</span>\n                        <b class="o_vo_phone_display" dir="ltr"/>': '<span>کد به این شماره ارسال شد:</span>\n                        <b class="o_vo_phone_display" dir="ltr"/>',
    '<i class="oi" data-icon="edit" aria-hidden="true"/> Edit number': '<i class="oi" data-icon="edit" aria-hidden="true"/> ویرایش شماره',
    "One-time code": f"کد یک{Z}بارمصرف",
    "Confirm and log in": "تأیید و ورود",
    "Confirm the number": "تأیید شماره",
    '<span class="o_vo_wait">Send again in <span class="o_vo_timer" dir="ltr">0:59</span></span>': '<span class="o_vo_wait">ارسال دوباره تا <span class="o_vo_timer" dir="ltr">۰:۵۹</span></span>',
    '<i class="oi" data-icon="refresh" aria-hidden="true"/> Send the code again': f'<i class="oi" data-icon="refresh" aria-hidden="true"/> ارسال دوباره{Z}ی کد',
    "Create your account": "ساخت حساب کاربری",
    "This number has no account yet. Enter your name to finish.": "این شماره هنوز حساب ندارد. برای پایان، نام خود را وارد کنید.",
    "Full name": "نام و نام خانوادگی",
    "<span>Create the account and log in</span>": "<span>ساخت حساب و ورود</span>",
    '<i class="oi" data-icon="mail" aria-hidden="true"/> Log in with email and password': '<i class="oi" data-icon="mail" aria-hidden="true"/> ورود با ایمیل و رمز عبور',
    '<i class="oi" data-icon="mail" aria-hidden="true"/> Sign up with email': f'<i class="oi" data-icon="mail" aria-hidden="true"/> ثبت{Z}نام با ایمیل',
    "Already have an account?": "حساب دارید؟ وارد شوید",
    '<i class="oi" data-icon="mail" aria-hidden="true"/> <span>Log in with email</span>': '<i class="oi" data-icon="mail" aria-hidden="true"/> <span>ورود با ایمیل</span>',
    '<i class="oi" data-icon="mail" aria-hidden="true"/> <span>Sign up with email</span>': f'<i class="oi" data-icon="mail" aria-hidden="true"/> <span>ثبت{Z}نام با ایمیل</span>',
    "<span>or</span>": "<span>یا</span>",
    "No account yet? Your mobile number creates one.": f"حساب ندارید؟ با همین شماره ثبت{Z}نام می{Z}شوید.",
    "Log in with email": "ورود با ایمیل",
    "Enter your email and password.": "ایمیل و رمز عبور خود را وارد کنید.",
    "Sign up with email": f"ثبت{Z}نام با ایمیل",
    "Log in with mobile number": f"ورود با شماره{Z}ی موبایل",
    "Sign up with mobile number": f"ثبت{Z}نام با شماره{Z}ی موبایل",
    "Reset your password": "بازیابی رمز عبور",
    "Choose a new password.": "رمز عبور تازه را انتخاب کنید.",
    "Enter your email; we send you a link to choose a new password.": f"ایمیل خود را وارد کنید؛ پیوندی برای انتخاب رمز تازه برایتان می{Z}فرستیم.",
    '<i class="oi" data-icon="smartphone" aria-hidden="true"/> Sign up with mobile number': f'<i class="oi" data-icon="smartphone" aria-hidden="true"/> ثبت{Z}نام با شماره{Z}ی موبایل',
    # login: messages
    "Enter a valid mobile number, like 0912 345 6789.": f"یک شماره{Z}ی موبایل درست وارد کنید، مثل ۰۹۱۲ ۳۴۵ ۶۷۸۹.",
    "You can ask for a new code in %(seconds)s seconds.": f"%(seconds)s ثانیه{Z}ی دیگر می{Z}توانید کد تازه بخواهید.",
    "Too many codes were asked for. Try again later.": "کدهای زیادی درخواست شده است. کمی بعد دوباره امتحان کنید.",
    "The code could not be sent. Try again in a few minutes, or log in with your email and password.": f"ارسال کد ممکن نشد. چند دقیقه{Z}ی دیگر دوباره امتحان کنید، یا با ایمیل و رمز عبور وارد شوید.",
    "Test mode: nothing was sent. Your code is %(code)s.": "حالت آزمایشی: چیزی ارسال نشد. کد شما %(code)s است.",
    "The code was sent by SMS and Bale.": "کد به پیامک و بله ارسال شد.",
    "The code was sent by SMS.": "کد با پیامک ارسال شد.",
    "The code was sent on Bale.": "کد در بله ارسال شد.",
    "This number has no Bale account; the code was sent by SMS.": "شماره در بله حساب ندارد؛ کد با پیامک ارسال شد.",
    "Your login code for %(website)s: %(code)s": "کد ورود شما به %(website)s: %(code)s",
    "This code is no longer valid. Ask for a new one.": "این کد دیگر معتبر نیست. کد تازه بخواهید.",
    "Please try again.": "لطفاً دوباره امتحان کنید.",
    "The code has expired. Ask for a new one.": "کد منقضی شده است. کد تازه بخواهید.",
    "Too many wrong codes. Ask for a new one.": "کد نادرست زیاد وارد شد. کد تازه بخواهید.",
    "Wrong code. %(count)s attempts left.": f"کد نادرست است. %(count)s بار دیگر می{Z}توانید امتحان کنید.",
    "This number belongs to several accounts. Log in with your email and password.": "این شماره به چند حساب تعلق دارد. با ایمیل و رمز عبور وارد شوید.",
    "This account logs in with its email and password.": f"این حساب با ایمیل و رمز عبور وارد می{Z}شود.",
    "No account was found with this mobile number.": f"حسابی با این شماره{Z}ی موبایل پیدا نشد.",
    "Enter your full name.": "نام و نام خانوادگی خود را وارد کنید.",
    "This number already has an account. Log in again.": "این شماره حساب دارد. دوباره وارد شوید.",
    "The account could not be created. Try again, or contact us.": "ساخت حساب ممکن نشد. دوباره امتحان کنید یا با ما تماس بگیرید.",
    "This number belongs to another account.": "این شماره متعلق به حساب دیگری است.",
    "Your mobile number is now %(phone)s.": f"شماره{Z}ی موبایل شما اکنون %(phone)s است.",
    "Login with mobile is not enabled.": "ورود با موبایل فعال نیست.",
    "Log in first.": "اول وارد شوید.",
    "You are already logged in.": f"شما وارد شده{Z}اید.",
    "Unknown request.": "درخواست ناشناخته.",
    # /my/account
    "Login mobile": "موبایل ورود",
    '<span class="badge o_vo_badge_ok">\n                                        <i class="oi" data-icon="verified" aria-hidden="true"/> Verified\n                                    </span>': '<span class="badge o_vo_badge_ok">\n                                        <i class="oi" data-icon="verified" aria-hidden="true"/> تأییدشده\n                                    </span>',
    '<span class="o_vo_account_value">No verified mobile yet</span>': f'<span class="o_vo_account_value">هنوز موبایل تأییدشده{Z}ای ندارید</span>',
    "You log in on this website with this number and a one-time code.": f"با این شماره و یک کد یک{Z}بارمصرف وارد این وب{Z}سایت می{Z}شوید.",
    "Change": "تغییر",
    "Add a mobile": "افزودن موبایل",
}


def main():
    folder = pathlib.Path(__file__).resolve().parent.parent / "i18n"
    pot = polib.pofile(str(folder / "vesta_auth_otp.pot"))
    po = polib.POFile()
    po.metadata = dict(pot.metadata, Language="fa", **{"Plural-Forms": ""})
    missing = []
    for entry in pot:
        msgstr = TERMS.get(entry.msgid, "")
        if not msgstr:
            missing.append(entry.msgid)
        po.append(
            polib.POEntry(
                msgid=entry.msgid,
                msgstr=msgstr,
                occurrences=entry.occurrences,
                comment=entry.comment,
                flags=entry.flags,
            )
        )
    po.save(str(folder / "fa.po"))
    for msgid in missing:
        print("missing:", repr(msgid))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
