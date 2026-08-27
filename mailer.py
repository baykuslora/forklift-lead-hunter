import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime

class LeadMailer:
    def __init__(self, smtp_server, smtp_port, user, password, recipients):
        self.smtp_server = smtp_server
        self.smtp_port = int(smtp_port) if smtp_port else 587
        self.user = user
        self.password = password
        self.recipients = [r.strip() for r in recipients.split(",") if r.strip()]

    def send_report(self, excel_path, lead_count):
        if not self.user or not self.password or not self.recipients:
            print("[-] E-posta ayarları eksik, gönderim atlandı.")
            return

        subject = f"Haftalık Forklift Potansiyel Müşteri Raporu ({datetime.now().strftime('%d.%m.%Y')}) - {lead_count} Yeni Lead"
        
        body = f"""Merhaba Ece Hanım,

Bu hafta forklift ilanı açan {lead_count} adet yeni potansiyel firma tespit edilmiştir.
Detaylı liste ekteki Excel dosyasındadır.

İyi çalışmalar."""

        msg = MIMEMultipart()
        msg['From'] = f"Jungheinrich Lead Bot <{self.user}>"
        msg['To'] = ", ".join(self.recipients)
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        if excel_path and os.path.exists(excel_path):
            with open(excel_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(excel_path)}',
            )
            msg.attach(part)

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.user, self.password)
            server.sendmail(self.user, self.recipients, msg.as_string())
            server.quit()
            print("[✓] E-posta başarıyla gönderildi.")
        except Exception as e:
            print(f"[-] E-posta gönderim hatası: {e}")
