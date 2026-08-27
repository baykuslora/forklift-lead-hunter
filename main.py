import os
from scraper import JobLeadScraper
from database import LeadDatabase
from exporter import export_leads_to_excel
from mailer import send_weekly_leads_email

def main():
    print("=== Forklift Lead Generation Pipeline Başlatıldı ===")
    
    # 1. Web sitelerini ve Google arama motorunu tara
    scraper = JobLeadScraper()
    raw_leads = scraper.run_all()
    print(f"[*] Bu taramada {len(raw_leads)} ilan yakalandı.")

    # 2. Yeni olanları veritabanına ekle (Mükerrerleri filtreler)
    db = LeadDatabase()
    db.filter_and_save(raw_leads, retention_days=45)

    # 3. Son 45 günün birikmiş TÜM tekil havuzunu al (Kümülatif Master Liste)
    master_leads = db.get_all_active_leads(retention_days=45)
    print(f"[*] Excel'e aktarılacak toplam kümülatif lead sayısı: {len(master_leads)}")

    if not master_leads:
        print("[!] Aktif lead bulunamadı.")
        return

    # 4. 4 Sütunlu Excel raporunu tüm havuzla oluştur
    excel_path = export_leads_to_excel(master_leads)

    # 5. Ece Hanım ve ekibe maili ilet
    send_weekly_leads_email(excel_path=excel_path, lead_count=len(master_leads))
    print("=== Pipeline Başarıyla Tamamlandı ===")

if __name__ == "__main__":
    main()
