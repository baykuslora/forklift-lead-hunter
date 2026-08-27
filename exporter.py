import os
import re
import pandas as pd
from datetime import datetime

def tr_upper(text):
    """Türkçe karakterleri eksiksiz büyük harfe çevirir."""
    if not text or pd.isna(text):
        return ""
    text = str(text).strip()
    tr_map = {'i': 'İ', 'ı': 'I', 'ç': 'Ç', 'ş': 'Ş', 'ğ': 'Ğ', 'ü': 'Ü', 'ö': 'Ö'}
    for lower_c, upper_c in tr_map.items():
        text = text.replace(lower_c, upper_c)
    return text.upper()

def clean_city(raw_location):
    """Konumdan sadece il adını ayıklar ve büyük harf yapar."""
    if not raw_location or pd.isna(raw_location):
        return "TÜRKİYE"
    
    loc_upper = tr_upper(str(raw_location))
    
    if any(k in loc_upper for k in ["GEBZE", "ÇAYIROVA", "DİLOVASI", "DARICA"]):
        return "KOCAELİ"
    if any(k in loc_upper for k in ["ÇORLU", "ÇERKEZKÖY", "ERGENE"]):
        return "TEKİRDAĞ"

    cities = [
        "İSTANBUL", "KOCAELİ", "BURSA", "İZMİR", "ANKARA", 
        "SAKARYA", "TEKİRDAĞ", "MANİSA", "ADANA", "ANTALYA", 
        "KONYA", "GAZİANTEP", "ESKİŞEHİR", "KAYSERİ", "MERSİN",
        "DENİZLİ", "SAMSUN", "BALIKESİR", "AYDIN", "YALOVA"
    ]
    for city in cities:
        if city in loc_upper:
            return city
            
    cleaned = loc_upper.replace("/", "").replace("TÜRKİYE", "").strip()
    return cleaned if cleaned else "TÜRKİYE"

def format_phone_3322(phone_raw):
    """Telefonu parantezsiz XXX XXX XX XX formatına sokar, yoksa boş bırakır."""
    if not phone_raw or pd.isna(phone_raw) or "yok" in str(phone_raw).lower():
        return ""
    
    digits = re.sub(r'\D', '', str(phone_raw))
    if digits.startswith("90") and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
        
    if len(digits) == 10:
        return f"{digits[0:3]} {digits[3:6]} {digits[6:8]} {digits[8:10]}"
    return str(phone_raw).strip()

def export_leads_to_excel(leads, output_dir="reports"):
    os.makedirs(output_dir, exist_ok=True)
    today_str = datetime.now().strftime("%d.%m.%Y")
    filepath = os.path.join(output_dir, f"Jungheinrich_Leadler_{today_str}.xlsx")

    formatted_rows = []
    for lead in leads:
        company = tr_upper(lead.get("company_name", "FİRMA BELİRTİLMEMİŞ"))
        city = clean_city(lead.get("city", ""))
        phone = format_phone_3322(lead.get("direct_phone", ""))
        link = lead.get("job_url", "")

        formatted_rows.append({
            "FİRMA İSMİ": company,
            "KONUM": city,
            "İLETİŞİM BİLGİSİ": phone,
            "İLAN LİNKİ": link
        })

    # Tam olarak istenen 4 sütun
    df = pd.DataFrame(formatted_rows, columns=["FİRMA İSMİ", "KONUM", "İLETİŞİM BİLGİSİ", "İLAN LİNKİ"])

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Potansiyel Müşteriler")
        worksheet = writer.sheets["Potansiyel Müşteriler"]
        
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 4, 18)

    print(f"[✓] 4 Sütunlu Excel Hazırlandı: {filepath}")
    return filepath
