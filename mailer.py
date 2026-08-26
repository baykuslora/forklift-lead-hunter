import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

def send_weekly_leads_email(excel_path: str, lead_count: int):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    recipient_emails = os.getenv("RECIPIENTS", "").split(",")

    if not smtp_user or not smtp_pass or not recipient_emails or not recipient_emails[0]:
        print("[-] E-posta ayarları eksik, gönderim atlandı.")
        return

    msg = MIMEMultipart()
    msg['From'] = f"Jungheinrich Lead Bot <{smtp_user}>"
    msg['To'] = ", ".join(recipient_emails)
    msg['Subject'] = f"Haftalık Forklift Potansiyel Müşteri Raporu ({datetime.now().strftime('%d.%m.%Y')}) - {lead_count} Yeni Lead"

    body = f"""Merhaba Satış Ekibi,\n\nBu hafta forklift ilanı açan {lead_count} adet yeni potansiyel firma tespit edilmiştir.\nDetaylı liste ekteki Excel dosyasındadır.\n\nİyi çalışmalar."""
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    with open(excel_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(excel_path)}")
        msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        print("[✓] E-posta başarıyla gönderildi.")
    except Exception as e:
        print(f"[-] E-posta gönderim hatası: {e}")