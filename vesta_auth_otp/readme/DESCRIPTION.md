Customers log in and sign up on the website with their mobile number and a one-time code. The code
goes out by SMS (through Vesta Marketing and sms.ir) and by Bale (Safir, the code service of Bale)
at the same time; the login page says where it went.

- A two-step card on the login and sign-up pages: the mobile number, then the code (with a resend
  countdown and «Edit number»); the email and password login stays one click away. A new number
  gets a portal account after one more field, the full name.
- The session is opened by Odoo's own login (a credential of type `vesta_otp`), so two-factor
  authentication still applies and the checkout comes back after the login.
- Codes of 4 to 6 digits made with `secrets`, stored only as an HMAC (database secret and a salt),
  valid 120 seconds, dead after 5 wrong attempts; resend after 60 seconds, limits per number and
  per IP address; the answers never tell whether an account exists.
- sms.ir: the fast «verify» template when its id is set, else a plain SMS sent at once through
  Odoo's SMS, with the WebOTP / SMS Retriever line (`@domain #code`) and `autocomplete="one-time-code"`
  so phones fill the code in.
- /my/account shows the verified mobile; a new number is verified with a code first.
- Test mode (on by default): nothing is sent, the code is shown on the page and in the server log.
- RTL first, Persian digits accepted, phone width, the dark theme of Vesta Shop.
