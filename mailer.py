import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

def send_weekly_leads_email(excel_paths=None, weekly_count=0, cumulative_count=0, *args, **kwargs):
    """
    Haftalık yeni lead'leri ve 30 günlük kümülatif master listeyi 
    iki ayrı Excel dosyası olarak tek bir e-postada ilgililere iletir.
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

    # Geriye dönük uyumluluk: Tek dosya string olarak gelirse listeye çevir
    if isinstance(excel_paths, str):
        excel_paths = [excel_paths]
    elif excel_paths is None:
        excel_paths = kwargs.get("excel_path", [])
        if isinstance(excel_paths, str):
            excel_paths = [excel_paths]

    date_str = datetime.now().strftime('%d.%m.%Y')
    subject = f"Haftalık Forklift Potansiyel Müşteri Raporu ({date_str}) - {weekly_count} Yeni Lead"
    
    body = f"""Merhaba,

Bu haftaki forklift potansiyel müşteri raporları ekte 2 ayrı Excel dosyası olarak bilginize sunulmuştur:

1. Bu Haftanın Yeni İlanları ({weekly_count} Firma):
   Sadece bu hafta ilk kez tespit edilen güncel müşteri adayları.

2. Son 30 Günün Kümülatif Havuzu ({cumulative_count} Firma):
   Son 30 gün boyunca toplanan, duplike (mükerrer) kayıtların elendiği aktif master müşteri listesi.

İyi çalışmalar dilerim."""

    msg = MIMEMultipart()
    msg['From'] = f"Jungheinrich Lead Bot <{smtp_user}>"
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # Listedeki tüm Excel dosyalarını e-postaya iliştir
    for path in excel_paths:
        if path and os.path.exists(path):
            with open(path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{os.path.basename(path)}"',
            )
            msg.attach(part)
        else:
            print(f"[-] Uyarı: Belirtilen ek dosya bulunamadı: {path}")

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipients, msg.as_string())
        server.quit()
        print(f"[✓] 2 Raporlu e-posta başarıyla gönderildi -> {', '.join(recipients)}")
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

    def send_report(self, excel_paths, weekly_count=0, cumulative_count=0):
        return send_weekly_leads_email(
            excel_paths=excel_paths, 
            weekly_count=weekly_count, 
            cumulative_count=cumulative_count
        )
