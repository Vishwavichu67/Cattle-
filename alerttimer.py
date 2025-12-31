import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================
# EMAIL CONFIG
# =========================
EMAIL_FROM = "vsnproject2025@gmail.com"
EMAIL_PASS = "rdqh aljy jhab xmvr"
EMAIL_TO = "nishanthalagarasan2005@gmail.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# =========================
# COOLDOWN CONTROL
# =========================
EMAIL_COOLDOWN = 5   # seconds
LAST_EMAIL_TIME = 0

# =========================
# SEND EMAIL
# =========================
def send_email_alert(subject, body):
    global LAST_EMAIL_TIME

    now = time.time()
    if now - LAST_EMAIL_TIME < EMAIL_COOLDOWN:
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        LAST_EMAIL_TIME = now
        print("📧 Alert email sent")

    except Exception as e:
        print("❌ Email error:", e)
