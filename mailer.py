import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime

def send_weekly_leads_email(excel_path=None, lead_count=0, *args, **kwargs):
    """
    Haftalık forklift potansiyel müşteri listesini e-posta ile iletir.
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipients_raw = os.getenv("RECIPIENTS", "")

    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]

    if not smtp_user or not smtp_password or not recipients:
        print("[-] E-posta ayarları eksik (SMTP_USER, SMTP_PASSWORD veya RECIPIENTS), gönderim atlandı.")
        return False

    date_str = datetime.now().strftime('%d.%m.%Y')
    subject = f"Haftalık Forklift Potansiyel Müşteri Raporu ({date_str}) - {lead_count} Yeni Lead"
    
    body = f"""Merhaba Ece Hanım,

Bu hafta forklift ilanı açan {lead_count} adet yeni potansiyel firma tespit edilmiştir.
Detaylı liste ekteki Excel dosyasındadır.

İyi çalışmalar."""

    msg = MIMEMultipart()
    msg['From'] = f"Jungheinrich Lead Bot <{smtp_user}>"
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # Excel dosyasını ekle
    if excel_path and os.path.exists(excel_path):
        with open(excel_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{os.path.basename(excel_path)}"',
        )
        msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipients, msg.as_string())
        server.quit()
        print(f"[✓] E-posta başarıyla gönderildi -> {', '.join(recipients)}")
        return True
    except Exception as e:
        print(f"[-] E-posta gönderim hatası: {e}")
        return False

class LeadMailer:
    def __init__(self, smtp_server=None, smtp_port=587, user=None, password=None, recipients=None):
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(smtp_port) if smtp_port else 587
        self.user = user or os.getenv("SMTP_USER")
        self.password = password or os.getenv("SMTP_PASSWORD")
        self.recipients = recipients or os.getenv("RECIPIENTS")

    def send_report(self, excel_path, lead_count):
        return send_weekly_leads_email(excel_path=excel_path, lead_count=lead_count)
