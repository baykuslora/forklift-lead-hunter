import os
import pandas as pd
from datetime import datetime
from ai_extractor import tr_upper, format_phone_3322

def export_leads_to_excel(leads, output_dir="reports"):
    os.makedirs(output_dir, exist_ok=True)
    today_str = datetime.now().strftime("%d.%m.%Y")
    filepath = os.path.join(output_dir, f"Forklift_Musteri_Adaylari_{today_str}.xlsx")

    formatted_rows = []
    for lead in leads:
        company = tr_upper(lead.get("company_name", ""))
        city = tr_upper(lead.get("city", ""))
        phone = format_phone_3322(lead.get("direct_phone", ""))
        source_site = tr_upper(lead.get("source_website", ""))
        link = str(lead.get("job_url", "")).strip()

        if company and len(company) >= 2 and city:
            formatted_rows.append({
                "FİRMA İSMİ": company,
                "KONUM": city,
                "İLETİŞİM BİLGİSİ": phone,
                "İLANIN ALINDIĞI WEBSİTESİ": source_site,
                "İLAN LİNKİ": link
            })

    columns = ["FİRMA İSMİ", "KONUM", "İLETİŞİM BİLGİSİ", "İLANIN ALINDIĞI WEBSİTESİ", "İLAN LİNKİ"]
    df = pd.DataFrame(formatted_rows, columns=columns)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Potansiyel Müşteriler")
        worksheet = writer.sheets["Potansiyel Müşteriler"]
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 4, 18)

    print(f"[✓] 5 Sütunlu Excel hazırlandı: {filepath}")
    return filepath
