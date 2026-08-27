import os
import re
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ai_extractor import call_gemini_rest, tr_upper

# Kariyer ve ilan sitelerinin çağrı merkezi numaraları (Kara Liste)
BLACKLIST_PHONES = [
    "2122492987", "2122492988", "2128868100", "2123462002", 
    "3123790304", "8502903173", "8502220101", "2165930441"
]

TURKISH_81_CITIES = [
    "ADANA", "ADIYAMAN", "AFYONKARAHİSAR", "AĞRI", "AMASYA", "ANKARA", "ANTALYA", "ARTVİN", "AYDIN", 
    "BALIKESİR", "BİLECİK", "BİNGÖL", "BİTLİS", "BOLU", "BURDUR", "BURSA", "ÇANAKKALE", "ÇANKIRI", 
    "ÇORUM", "DENİZLİ", "DİYARBAKIR", "EDİRNE", "ELAZIĞ", "ERZİNCAN", "ERZURUM", "ESKİŞEHİR", 
    "GAZİANTEP", "GİRESUN", "GÜMÜŞHANE", "HAKKARİ", "HATAY", "ISPARTA", "MERSİN", "İSTANBUL", 
    "İZMİR", "KARS", "KASTAMONU", "KAYSERİ", "KIRKLARELİ", "KIRŞEHİR", "KOCAELİ", "KONYA", 
    "KÜTAHYA", "MALATYA", "MANİSA", "KAHRAMANMARAŞ", "MARDİN", "MUĞLA", "MUŞ", "NEVŞEHİR", 
    "NİĞDE", "ORDU", "RİZE", "SAKARYA", "SAMSUN", "SİİRT", "SİNOP", "SİVAS", "TEKİRDAĞ", "TOKAT", "TRABZON", "TUNCELİ", 
    "ŞANLIURFA", "UŞAK", "VAN", "YOZGAT", "ZONGULDAK", "AKSARAY", "BAYBURT", 
    "KARAMAN", "KIRIKKALE", "BATMAN", "ŞIRNAK", "BARTIN", "ARDAHAN", "IĞDIR", 
    "YALOVA", "KARABÜK", "KİLİS", "OSMANİYE", "DÜZCE"
]

DISTRICT_MAP = {
    "GEBZE": "KOCAELİ", "ÇAYIROVA": "KOCAELİ", "DİLOVASI": "KOCAELİ", "DARICA": "KOCAELİ", 
    "KÖRFEZ": "KOCAELİ", "İZMİT": "KOCAELİ", "GÖLCÜK": "KOCAELİ", "KARTEPE": "KOCAELİ", "BAŞİSKELE": "KOCAELİ",
    "ÇORLU": "TEKİRDAĞ", "ÇERKEZKÖY": "TEKİRDAĞ", "ERGENE": "TEKİRDAĞ", "KAPAKLI": "TEKİRDAĞ", "MURATLI": "TEKİRDAĞ",
    "TUZLA": "İSTANBUL", "PENDİK": "İSTANBUL", "KARTAL": "İSTANBUL", "ÜMRANİYE": "İSTANBUL", 
    "SANCAKTEPE": "İSTANBUL", "SULTANBEYLİ": "İSTANBUL", "MALTEPE": "İSTANBUL", "KADIKÖY": "İSTANBUL", 
    "ESENYURT": "İSTANBUL", "HADIMKÖY": "İSTANBUL", "BÜYÜKÇEKMECE": "İSTANBUL", "KÜÇÜKÇEKMECE": "İSTANBUL", 
    "BAŞAKŞEHİR": "İSTANBUL", "ARNAVUTKÖY": "İSTANBUL", "AVCILAR": "İSTANBUL", "BEYLİKDÜZÜ": "İSTANBUL", "SİLİVRİ": "İSTANBUL",
    "NİLÜFER": "BURSA", "OSMANGAZİ": "BURSA", "YILDIRIM": "BURSA", "İNEGÖL": "BURSA", "GEMLİK": "BURSA",
    "ALİAĞA": "İZMİR", "TORBALI": "İZMİR", "KEMALPAŞA": "İZMİR", "ÇİĞLİ": "İZMİR", "BORNOVA": "İZMİR", "MENEMEN": "İZMİR", "GAZİEMİR": "İZMİR",
    "SİNCAN": "ANKARA", "KAZAN": "ANKARA", "KAHRAMANKAZAN": "ANKARA", "ETİMESGUT": "ANKARA", "OSTİM": "ANKARA", "İVEDİK": "ANKARA", "YENİMAHALLE": "ANKARA",
    "HENDEK": "SAKARYA", "ARİFİYE": "SAKARYA", "ERENLER": "SAKARYA", "SERDİVAN": "SAKARYA", "AKYAZI": "SAKARYA"
}

session = requests.Session()
retries = Retry(total=2, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

def format_phone_3322(phone_raw):
    """Telefonu parantezsiz 3-3-2-2 (XXX XXX XX XX) formatına dönüştürür."""
    if not phone_raw:
        return ""
    digits = re.sub(r'\D', '', str(phone_raw))
    
    for bl in BLACKLIST_PHONES:
        if bl in digits:
            return ""

    if digits.startswith("90") and len(digits) >= 12:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) >= 11:
        digits = digits[1:]
        
    if len(digits) == 10 and digits[0] in ['2', '3', '4', '5', '8']:
        return f"{digits[0:3]} {digits[3:6]} {digits[6:8]} {digits[8:10]}"
    if len(digits) == 7 and digits.startswith("444"):
        return f"{digits[0:3]} {digits[3:5]} {digits[5:7]}"
    return ""

def extract_tr_phone(text):
    """Metin içindeki 444, 0850 ve sabit/mobil Türkiye telefon numaralarını filtreleyerek yakalar."""
    if not text:
        return ""
        
    m_444 = re.search(r'\b(444\s*[0-9]\s*[0-9]{2}\s*[0-9]{2}|444\s*[0-9]{4})\b', text)
    if m_444:
        formatted = format_phone_3322(m_444.group(0))
        if formatted:
            return formatted

    patterns = [
        r'(?:(?:\+?90|0)\s*)?([2-5]\d{2})[\s.-]*(\d{3})[\s.-]*(\d{2})[\s.-]*(\d{2})',
        r'(?:(?:\+?90|0)\s*)?(850)[\s.-]*(\d{3})[\s.-]*(\d{2})[\s.-]*(\d{2})'
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            formatted = format_phone_3322(match.group(0))
            if formatted:
                return formatted
    return ""

def find_city_in_text(text):
    text_upper = tr_upper(text)
    for dist, prov in DISTRICT_MAP.items():
        if re.search(r'\b' + re.escape(dist) + r'\b', text_upper):
            return prov
    for city in TURKISH_81_CITIES:
        if re.search(r'\b' + re.escape(city) + r'\b', text_upper):
            return city
    return ""

def enrich_company_details(company_name: str, current_city: str, current_phone: str, serpapi_key: str) -> tuple:
    """Şirketin kurumsal telefonunu ve merkez lokasyonunu Google Business ve web üzerinden arar."""
    if current_phone:
        current_phone = format_phone_3322(current_phone)

    need_city = (not current_city) or (current_city == "BELİRTİLMEDİ")
    need_phone = not current_phone

    if not need_city and not need_phone:
        return current_city, current_phone

    final_city = current_city
    final_phone = current_phone

    if not serpapi_key or not company_name or len(company_name) < 3:
        if need_city:
            final_city = "İSTANBUL"
        return final_city, final_phone

    # Doğrudan Google Haritalar / İşletme Kartını tetikleyen sorgu formatı
    if current_city and current_city != "BELİRTİLMEDİ":
        query = f'{company_name} {current_city} telefon'
    else:
        query = f'{company_name} türkiye merkez iletişim telefon'

    try:
        params = {
            "engine": "google",
            "q": query,
            "hl": "tr",
            "gl": "tr",
            "num": "5",
            "api_key": serpapi_key
        }
        res = session.get("https://serpapi.com/search", params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            
            # 1. Google Knowledge Graph (Bilgi Kartı)
            kg = data.get("knowledge_graph", {})
            if kg:
                if need_phone and "phone" in kg:
                    p = extract_tr_phone(kg.get("phone"))
                    if p:
                        final_phone = p
                        need_phone = False
                
                if need_city and "address" in kg:
                    c = find_city_in_text(kg.get("address"))
                    if c:
                        final_city = c
                        need_city = False

            # 2. Google Local Results / Harita İşletme Kartı (Alpla Plastik Konya vb.)
            local_results = data.get("local_results", {})
            places = local_results.get("places", []) if isinstance(local_results, dict) else data.get("local_results", [])
            if isinstance(places, list):
                for place in places:
                    if need_phone and "phone" in place:
                        p = extract_tr_phone(place.get("phone"))
                        if p:
                            final_phone = p
                            need_phone = False
                    if need_city and "address" in place:
                        c = find_city_in_text(place.get("address"))
                        if c:
                            final_city = c
                            need_city = False

            # 3. Organik Web Arama Sonuçları Snippet Taraması
            for r in data.get("organic_results", []):
                snippet_text = f"{r.get('title', '')} {r.get('snippet', '')}"

                if need_phone and not final_phone:
                    p = extract_tr_phone(snippet_text)
                    if p:
                        final_phone = p
                        need_phone = False

                if need_city and (final_city == "BELİRTİLMEDİ" or not final_city):
                    c = find_city_in_text(snippet_text)
                    if c:
                        final_city = c
                        need_city = False
                        
    except Exception as e:
        print(f"[-] Zenginleştirme hatası ({company_name}): {e}")

    if not final_city or final_city == "BELİRTİLMEDİ":
        final_city = "İSTANBUL"

    return final_city, final_phone
