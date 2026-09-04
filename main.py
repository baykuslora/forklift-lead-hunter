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

    # 2. Eksik Konum ve Eksik Telefon Numaralarını İnternetten Araştır
    print("[+] Eksik konum ve telefon bilgileri internetten (Google/Genel Merkez) araştırılıyor...")
    enriched_leads = []
    for lead in raw_leads:
        company = lead.get("company_name", "")
        city = lead.get("city", "")
        phone = lead.get("direct_phone", "")

        enriched_city, enriched_phone = enrich_company_details(company, city, phone, serpapi_key)
        
        lead["city"] = enriched_city
        lead["direct_phone"] = enriched_phone
        enriched_leads.append(lead)

    # 3. Mükerrer Filtresi ve Veritabanı Kaydı (Sadece bu haftanın yeni lead'lerini yakalar)
    db = LeadDatabase()
    weekly_new_leads = db.filter_and_save(enriched_leads, retention_days=30)
    print(f"[*] Bu hafta ilk kez bulunan YENİ lead sayısı: {len(weekly_new_leads)}")

    # 4. Son 30 Günün Kümülatif Aktif Listesini Al
    cumulative_leads = db.get_all_active_leads(retention_days=30)
    print(f"[*] Son 30 günün aktif kümülatif lead sayısı: {len(cumulative_leads)}")

    if not cumulative_leads and not weekly_new_leads:
        print("[!] Gönderilecek aktif veya yeni lead bulunamadı, işlem sonlandırıldı.")
        return

    # 5. İki Ayrı Excel Dosyası Oluştur
    weekly_excel_path = export_leads_to_excel(
        weekly_new_leads, 
        filename_prefix="Haftalik_Yeni_Leadler", 
        sheet_name="Haftalık Yeni Fırsatlar"
    )
    
    cumulative_excel_path = export_leads_to_excel(
        cumulative_leads, 
        filename_prefix="Kumulatif_Master_Leadler_30Gun", 
        sheet_name="30 Günlük Master Havuz"
    )

    # 6. İki Dosyayı Tek Bir E-Posta İle Gönder
    reports_to_send = [weekly_excel_path, cumulative_excel_path]
    send_weekly_leads_email(
        excel_paths=reports_to_send,
        weekly_count=len(weekly_new_leads),
        cumulative_count=len(cumulative_leads)
    )

    print("=== Pipeline Başarıyla Tamamlandı ===")

if __name__ == "__main__":
    main()
