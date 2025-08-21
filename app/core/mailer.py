# app/core/mailer.py
import smtplib
import ssl
from email.message import EmailMessage
from typing import Iterable
from app.core.settings import settings

def send_email(to: str | Iterable[str], subject: str, html: str):
    if isinstance(to, str):
        recipients = [to]
    else:
        recipients = list(to)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = ", ".join(recipients)
    msg.set_content("HTML içerik desteklenmiyor.")
    msg.add_alternative(html, subtype="html")

    context = ssl.create_default_context()

    # SSL (465) mi yoksa STARTTLS (587) mi?
    if getattr(settings, "SMTP_USE_SSL", False):
        server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context)
    else:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        if getattr(settings, "SMTP_STARTTLS", True):
            server.starttls(context=context)

    try:
        # Kullanıcı adı verilmişse login dene; yoksa doğrudan gönder
        if getattr(settings, "SMTP_USER", ""):
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
    finally:
        server.quit()
