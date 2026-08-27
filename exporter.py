import os
import re
import pandas as pd
from datetime import datetime

def tr_upper(text):
    if not text or pd.isna(text):
        return ""
    text = str(text).strip()
    tr_map = {'i': 'İ', 'ı': 'I', 'ç': 'Ç', 'ş': 'Ş', 'ğ': 'Ğ', 'ü': 'Ü', 'ö': 'Ö'}
    for lower_c, upper_c in tr_map.items():
        text = text.replace(lower_c, upper_c)
    return text.upper()

def format_phone_3322(phone_raw):
    """Telefonu parantezsiz tam olarak XXX XXX XX XX formatına dönüştürür."""
    if not phone_raw or pd.isna(phone_raw):
        return ""
    
    digits = re.sub(r'\D', '', str(phone_raw))
    if digits.startswith("90") and len(digits) >= 12:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) >= 11:
        digits = digits[1:]
        
    if len(digits) == 10:
        return f"{digits[0:3]} {digits[3:6]} {digits[6:8]} {digits[8:10]}"
    
    if len(digits) == 7 and digits.startswith("444"):
        return f"{digits[0:3]} {digits[3]} {digits[4:7]}"
        
    return ""

def export_leads_to_excel(leads, output_dir="reports"):
    os.makedirs(output_dir, exist_ok=True)
    today_str = datetime.now().strftime("%d.%m.%Y")
    filepath = os.path.join(output_dir, f"Jungheinrich_Leadler_{today_str}.xlsx")

    formatted_rows = []
    for lead in leads:
        company = tr_upper(lead.get("company_name", ""))
        city = tr_upper(lead.get("city", ""))
        phone = format_phone_3322(lead.get("direct_phone", ""))
        link = lead.get("job_url", "")

        # Yalnızca firma adı ve konumu net olan satırları listeye al
        if company and len(company) >= 2 and city and city != "TÜRKİYE":
            formatted_rows.append({
                "FİRMA İSMİ": company,
                "KONUM": city,
                "İLETİŞİM BİLGİSİ": phone,
                "İLAN LİNKİ": link
            })

    # Tam 4 Sütun
    df = pd.DataFrame(formatted_rows, columns=["FİRMA İSMİ", "KONUM", "İLETİŞİM BİLGİSİ", "İLAN LİNKİ"])

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Potansiyel Müşteriler")
        worksheet = writer.sheets["Potansiyel Müşteriler"]
        
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 4, 18)

    print(f"[✓] SharePoint standartlarında Excel hazırlandı: {filepath}")
    return filepath
