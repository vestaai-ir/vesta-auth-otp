*Website > Configuration > Settings > Login with Mobile*:

- **Login with Mobile** turns the card on (off by default). **Colleagues Too** lets internal users
  log in with a code as well.
- **Test Mode** (on by default): nothing is sent, the code is shown on the login page. In test mode
  anyone can log in with any number: turn it off before customers use the website.
- **Codes** and **Limits**: length (4–6), lifetime, resend delay, wrong attempts per code, codes per
  number and per IP address per hour.
- **Send by SMS**: needs the sms.ir key and line of Vesta Marketing (*Settings > Vesta Marketing*).
  With the id of an approved «verify» template of sms.ir (one parameter, e.g. `#Code#`) the code
  goes out with the fast send; without it, as a plain SMS.
- **Send on Bale**: the Safir API key and the bot id from Bale Business (https://business.bale.ai).
- **Test Mobile** and the two test buttons check the SMS and Bale settings (nothing is sent in test
  mode). *Login Codes* lists the codes of the last day and how they were sent.
- Sign-up with a new number follows *Customer Account*: free sign-up (b2c) creates a portal user,
  on invitation (b2b) an unknown number gets «No account was found».
