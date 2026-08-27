import os
from scraper import JobLeadScraper
from enricher import find_company_phone_online
from database import LeadDatabase
from exporter import export_leads_to_excel
from mailer import send_weekly_leads_email

def main():
    print("=== Forklift Lead Generation & Intelligence Pipeline Başlatıldı ===")
    serpapi_key = os.getenv("SERPAPI_KEY", "").strip()

    # 1. LinkedIn, Indeed, Kariyer.net, Eleman.net, Secretcv'den temiz tekil ilanları topla
    scraper = JobLeadScraper()
    raw_leads = scraper.run_all()

    # 2. İletişim Bilgilerini Zenginleştir
    print("[+] İletişim bilgisi eksik ilanlar için Google santral sorgusu yapılıyor...")
    enriched_leads = []
    for lead in raw_leads:
        phone = lead.get("direct_phone", "")
        company = lead.get("company_name", "")
        city = lead.get("city", "")

        if not phone and company and len(company) > 3:
            online_phone = find_company_phone_online(company, city, serpapi_key)
            lead["direct_phone"] = online_phone

        enriched_leads.append(lead)

    # 3. Mükerrer Filtresi ve Veritabanı Kaydı
    db = LeadDatabase()
    db.filter_and_save(enriched_leads, retention_days=45)

    # 4. Kümülatif Master Listeyi Al
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
