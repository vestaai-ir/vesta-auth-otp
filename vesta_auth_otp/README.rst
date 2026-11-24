==================
Vesta Mobile Login
==================

|badge1| |badge2|

.. |badge1| image:: https://img.shields.io/badge/Odoo-20.0-714B67
.. |badge2| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html

Customers log in and sign up on the website with their mobile number and a one-time code. The code
goes out by SMS (through Vesta Marketing and sms.ir) and by Bale (Safir, the code service of Bale)
at the same time; the login page says where it went.

- A two-step card on the login and sign-up pages: the mobile number, then the code (with a resend
  countdown and «Edit number»); the email and password login stays one click away. A new number
  gets a portal account after one more field, the full name.
- The session is opened by Odoo's own login (a credential of type ``vesta_otp``), so two-factor
  authentication still applies and the checkout comes back after the login.
- Codes of 4 to 6 digits made with ``secrets``, stored only as an HMAC (database secret and a salt),
  valid 120 seconds, dead after 5 wrong attempts; resend after 60 seconds, limits per number and
  per IP address; the answers never tell whether an account exists.
- sms.ir: the fast «verify» template when its id is set, else a plain SMS sent at once through
  Odoo's SMS, with the WebOTP / SMS Retriever line (``@domain #code``) and ``autocomplete="one-time-code"``
  so phones fill the code in.
- /my/account shows the verified mobile; a new number is verified with a code first.
- Test mode (on by default): nothing is sent, the code is shown on the page and in the server log.
- RTL first, Persian digits accepted, phone width, the dark theme of Vesta Shop.

Configuration
=============

*Website > Configuration > Settings > Login with Mobile*:

- **Login with Mobile** turns the card on (off by default). **Colleagues Too** lets internal users
  log in with a code as well.
- **Test Mode** (on by default): nothing is sent, the code is shown on the login page. In test mode
  anyone can log in with any number: turn it off before customers use the website.
- **Codes** and **Limits**: length (4–6), lifetime, resend delay, wrong attempts per code, codes per
  number and per IP address per hour.
- **Send by SMS**: needs the sms.ir key and line of Vesta Marketing (*Settings > Vesta Marketing*).
  With the id of an approved «verify» template of sms.ir (one parameter, e.g. ``#Code#``) the code
  goes out with the fast send; without it, as a plain SMS.
- **Send on Bale**: the Safir API key and the bot id from Bale Business (https://business.bale.ai).
- **Test Mobile** and the two test buttons check the SMS and Bale settings (nothing is sent in test
  mode). *Login Codes* lists the codes of the last day and how they were sent.
- Sign-up with a new number follows *Customer Account*: free sign-up (b2c) creates a portal user,
  on invitation (b2b) an unknown number gets «No account was found».


Usage
=====

The login page (``/web/login``, the «Log in | Sign up» button of Vesta Shop, the «Sign in» button of
the checkout) opens on the mobile card: the customer types the number (Persian digits work), gets
the code by SMS and Bale, types it (or the phone fills it in) and is logged in; a new number asks
for the full name and creates the account. «Log in with email» shows Odoo's form.

The account of a number is the one whose verified mobile it is, or whose login it is, or whose
contact has it as phone when a colleague typed it (a phone typed on the website counts only once
verified).


Changelog
=========

20.0.1.1.0
----------

- The login, sign-up and password reset pages are one card in the middle of the screen: the mark of the website,
  a centred title, grey fields and dark buttons, «or» between two lines, «Log in with email» and the mobile login
  next to the other ways to log in (passkey…); nothing else of the website.
- Odoo's «Choose a user» link stays in the email form instead of the mobile number label.

20.0.1.0.0
----------

- First version: login and sign-up with a mobile number and a one-time code sent by SMS (sms.ir)
  and Bale at the same time, test mode, limits, verified mobile on /my/account.


Credits
=======

- `Vesta AI <https://vestaai.ir>`_
