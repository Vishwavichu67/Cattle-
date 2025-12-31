
import smtplib
from email.mime.text import MIMEText
import requests

EMAIL_FROM = "vsnproject2025@gmail.com"
EMAIL_PASS = "rdqh aljy jhab xmvr"
EMAIL_TO = "nishanthalagarasan2005@gmail.com"

def send_email_alert(subject, message):
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_FROM, EMAIL_PASS)
    server.send_message(msg)
    server.quit()

FAST2SMS_API = "FAST2SMS_API_KEY"
MOBILE_NO = "9XXXXXXXXX"

def send_sms_alert(message):
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "authorization": FAST2SMS_API,
        "message": message,
        "route": "q",
        "numbers": MOBILE_NO
    }
    requests.post(url, data=payload)
