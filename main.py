import os
from scraper import JobLeadScraper
from enricher import find_company_phone_online
from database import LeadDatabase
from exporter import export_leads_to_excel
from mailer import send_weekly_leads_email

def main():
    print("=== Forklift Lead Generation & Intelligence Pipeline Başlatıldı ===")
    serpapi_key = os.getenv("SERPAPI_KEY", "").strip()

    # 1. LinkedIn, Indeed, Kariyer.net, Eleman.net'ten temiz ilanları topla
    scraper = JobLeadScraper()
    raw_leads = scraper.run_all()
    print(f"[*] Bu taramada {len(raw_leads)} adet saf firma/ilan yakalandı.")

    # 2. İletişim Bilgisi Zenginleştirme (İlanda telefon yoksa internetten bul)
    print("[+] İletişim bilgisi eksik firmalar için Google santral araması yapılıyor...")
    enriched_leads = []
    for lead in raw_leads:
        phone = lead.get("direct_phone", "")
        company = lead.get("company_name", "")
        city = lead.get("city", "")

        # İlanda telefon bulunamadıysa Google üzerinden araştır
        if not phone and company:
            online_phone = find_company_phone_online(company, city, serpapi_key)
            lead["direct_phone"] = online_phone

        enriched_leads.append(lead)

    # 3. Veritabanına kaydet (Son 45 günün mükerrerlerini engeller)
    db = LeadDatabase()
    db.filter_and_save(enriched_leads, retention_days=45)

    # 4. Kümülatif Master Listeyi Al (Tüm zenginleştirilmiş geçmiş havuz)
    master_leads = db.get_all_active_leads(retention_days=45)
    print(f"[*] Excel'e aktarılacak toplam net lead sayısı: {len(master_leads)}")

    if not master_leads:
        print("[!] Aktif lead bulunamadı.")
        return

    # 5. SharePoint Uyumlu 4 Sütunlu Excel Raporunu Üret
    excel_path = export_leads_to_excel(master_leads)

    # 6. E-posta ile Gönder
    send_weekly_leads_email(excel_path=excel_path, lead_count=len(master_leads))
    print("=== Pipeline Başarıyla Tamamlandı ===")

if __name__ == "__main__":
    main()
