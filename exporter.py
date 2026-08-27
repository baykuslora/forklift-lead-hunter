import os
import re
import pandas as pd
from datetime import datetime

def tr_upper(text):
    """Türkçe karakterleri hatasız büyük harfe çevirir."""
    if not text or pd.isna(text):
        return ""
    text = str(text)
    tr_map = {'i': 'İ', 'ı': 'I', 'ç': 'Ç', 'ş': 'Ş', 'ğ': 'Ğ', 'ü': 'Ü', 'ö': 'Ö'}
    for lower_c, upper_c in tr_map.items():
        text = text.replace(lower_c, upper_c)
    return text.upper().strip()

def clean_city(raw_location):
    if not raw_location or pd.isna(raw_location):
        return "TÜRKİYE"
    loc_upper = tr_upper(str(raw_location))
    
    if any(k in loc_upper for k in ["GEBZE", "ÇAYIROVA", "DİLOVASI", "DARICA"]): return "KOCAELİ"
    if any(k in loc_upper for k in ["ÇORLU", "ÇERKEZKÖY", "ERGENE"]): return "TEKİRDAĞ"

    cities = ["İSTANBUL", "KOCAELİ", "BURSA", "İZMİR", "ANKARA", "SAKARYA", "TEKİRDAĞ", "MANİSA", "ADANA", "ANTALYA", "KONYA", "GAZİANTEP", "ESKİŞEHİR", "KAYSERİ", "MERSİN", "DENİZLİ", "SAMSUN", "BALIKESİR", "AYDIN", "YALOVA", "BOLU", "DÜZCE", "BİLECİK"]
    for city in cities:
        if city in loc_upper:
            return city
    
    cleaned = loc_upper.replace("/", "").replace("TÜRKİYE", "").strip()
    return cleaned if cleaned else "TÜRKİYE"

def format_phone_3322(phone_raw):
    """Telefon yoksa BOŞ bırakır, varsa 3-3-2-2 formatına sokar."""
    if not phone_raw or pd.isna(phone_raw) or "yok" in str(phone_raw).lower():
        return "" # SharePoint temizliği için boş bırakılır
    
    digits = re.sub(r'\D', '', str(phone_raw))
    if digits.startswith("90") and len(digits) == 12: digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11: digits = digits[1:]
    
    if len(digits) == 10:
        return f"{digits[0:3]} {digits[3:6]} {digits[6:8]} {digits[8:10]}"
    return str(phone_raw).strip()

def clean_company(company_raw):
    """Jenerik çöp firma isimlerini temizleyip boş döndürür."""
    comp = tr_upper(company_raw)
    bad_words = ["POTANSİYEL", "GÜNCEL İŞ", "FIRSAT", "İLAN", "ARANIYOR", "ELEMAN"]
    if any(b in comp for b in bad_words):
        return ""
    return comp

def export_leads_to_excel(leads, output_dir="reports"):
    os.makedirs(output_dir, exist_ok=True)
    today_str = datetime.now().strftime("%d.%m.%Y")
    filepath = os.path.join(output_dir, f"Jungheinrich_Leadler_{today_str}.xlsx")

    formatted_rows = []
    for lead in leads:
        company = clean_company(lead.get("company_name", ""))
        city = clean_city(lead.get("city", ""))
        phone = format_phone_3322(lead.get("direct_phone", ""))
        link = lead.get("job_url", "")

        formatted_rows.append({
            "FİRMA İSMİ": company,
            "KONUM": city,
            "AKTİVİTE": "",          # SharePoint eşleşmesi için boş
            "FIRSAT": "",            # SharePoint eşleşmesi için boş
            "İLETİŞİM BİLGİSİ": phone,
            "İLAN LİNKİ": link       # Kontrol edebilmeniz için en sonda
        })

    df = pd.DataFrame(formatted_rows, columns=["FİRMA İSMİ", "KONUM", "AKTİVİTE", "FIRSAT", "İLETİŞİM BİLGİSİ", "İLAN LİNKİ"])

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Potansiyel Müşteriler")
        worksheet = writer.sheets["Potansiyel Müşteriler"]
        
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 4, 15)

    return filepath
