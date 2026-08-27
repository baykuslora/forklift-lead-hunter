import os
from scraper import JobLeadScraper
from enricher import enrich_company_details
from database import LeadDatabase
from exporter import export_leads_to_excel
from mailer import send_weekly_leads_email

def main():
    print("=== Forklift Lead Pipeline Başlatıldı ===")
    serpapi_key = os.getenv("SERPAPI_KEY", "").strip()

    # 1. Kariyer platformlarından ham ilanları topla ve AI ile filtrele
    scraper = JobLeadScraper()
    raw_leads = scraper.run_all()

    # 2. Eksik Konum ("BELİRTİLMEDİ") ve Eksik Telefon Numaralarını İnternetten Araştır
    print("[+] Eksik konum ve telefon bilgileri internetten (Google/Genel Merkez) araştırılıyor...")
    enriched_leads = []
    for lead in raw_leads:
        company = lead.get("company_name", "")
        city = lead.get("city", "")
        phone = lead.get("direct_phone", "")

        # Hem şehri hem telefonu internetten zenginleştir
        enriched_city, enriched_phone = enrich_company_details(company, city, phone, serpapi_key)
        
        lead["city"] = enriched_city
        lead["direct_phone"] = enriched_phone
        enriched_leads.append(lead)

    # 3. Mükerrer Filtresi ve 30 Günlük Veritabanı Kaydı
    db = LeadDatabase()
    db.filter_and_save(enriched_leads, retention_days=30)

    # 4. Son 30 Günün Aktif Listesini Al
    master_leads = db.get_all_active_leads(retention_days=30)
    print(f"[*] Excel'e aktarılacak kümülatif lead sayısı: {len(master_leads)}")

    if not master_leads:
        print("[!] Aktif lead bulunamadı.")
        return

    # 5. Excel'i Üret ve E-posta Gönder
    excel_path = export_leads_to_excel(master_leads)
    send_weekly_leads_email(excel_path=excel_path, lead_count=len(master_leads))
    print("=== Pipeline Başarıyla Tamamlandı ===")

if __name__ == "__main__":
    main()
