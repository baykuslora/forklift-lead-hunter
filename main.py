import os
from datetime import datetime
from dotenv import load_dotenv
from database import init_db, is_lead_recent, save_lead
from scraper import JobLeadScraper
from enricher import enrich_company_phone
from exporter import export_leads_to_excel
from mailer import send_weekly_leads_email

load_dotenv()

def main():
    print("=== Forklift Lead Generation Pipeline Başlatıldı ===")
    init_db()

    scraper = JobLeadScraper()
    raw_leads = scraper.run_all()
    print(f"[*] Toplam {len(raw_leads)} ham ilan bulundu.")

    fresh_leads = []
    for lead in raw_leads:
        company = lead["company_name"]
        city = lead["city"]
        if not is_lead_recent(company, city, days_threshold=30):
            fresh_leads.append(lead)

    print(f"[*] Yeni lead sayısı: {len(fresh_leads)}")
    if not fresh_leads:
        print("[!] Bu hafta yeni lead bulunamadı.")
        return

    for idx, lead in enumerate(fresh_leads, 1):
        if lead["direct_phone"] == "İlanda Yok":
            enrichment_res = enrich_company_phone(lead["company_name"], lead["city"])
            lead["enriched_phone"] = enrichment_res["phone"]
        else:
            lead["enriched_phone"] = lead["direct_phone"]
        save_lead(lead)

    date_str = datetime.now().strftime("%Y-%m-%d")
    output_filename = f"Jungheinrich_Leadler_{date_str}.xlsx"
    excel_path = export_leads_to_excel(fresh_leads, output_filename)

    if excel_path:
        send_weekly_leads_email(excel_path, len(fresh_leads))

    print("=== Pipeline Başarıyla Tamamlandı ===")

if __name__ == "__main__":
    main()