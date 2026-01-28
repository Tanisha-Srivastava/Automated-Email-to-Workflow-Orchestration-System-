import smtplib
from email.message import EmailMessage

GMAIL_USER = "surabhi.r052@gmail.com"
GMAIL_APP_PASSWORD = "aidhhcutynhtcluc"  # 16-char app password

def send_email(to, subject, body):
    msg = EmailMessage()
    msg["From"] = GMAIL_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
