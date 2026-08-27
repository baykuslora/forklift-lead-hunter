import os
import re
import json
import requests
from ai_extractor import call_gemini_rest, tr_upper, format_phone_3322

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

def extract_tr_phone(text):
    """Metin içindeki Türkiye telefon numaralarını yakalar."""
    if not text:
        return ""
    patterns = [
        r'(?:(?:\+?90|0)\s*)?([2-5]\d{2})[\s.-]*(\d{3})[\s.-]*(\d{2})[\s.-]*(\d{2})',
        r'(?:(?:\+?90|0)\s*)?(850)[\s.-]*(\d{3})[\s.-]*(\d{2})[\s.-]*(\d{2})',
        r'\b(444)[\s.-]*(\d{1})[\s.-]*(\d{3})\b'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return format_phone_3322(match.group(0))
    return ""

def find_city_in_text(text):
    """Metin içinden il veya sanayi ilçesi tespiti yapar."""
    text_upper = tr_upper(text)
    for dist, prov in DISTRICT_MAP.items():
        if re.search(r'\b' + re.escape(dist) + r'\b', text_upper):
            return prov
    for city in TURKISH_81_CITIES:
        if re.search(r'\b' + re.escape(city) + r'\b', text_upper):
            return city
    return ""

def enrich_company_details(company_name: str, current_city: str, current_phone: str, serpapi_key: str) -> tuple:
    """
    Şirketin eksik lokasyonunu (merkez şehri) ve eksik telefon numarasını internetten araştırır.
    """
    need_city = (not current_city) or (current_city == "BELİRTİLMEDİ")
    need_phone = not current_phone

    # Zaten iki bilgi de tamsa aramaya gerek yok
    if not need_city and not need_phone:
        return current_city, current_phone

    if not serpapi_key or not company_name or len(company_name) < 3:
        return current_city, current_phone

    query = f'"{company_name}" türkiye merkez genel müdürlük iletişim telefon'
    final_city = current_city
    final_phone = current_phone

    try:
        params = {
            "engine": "google",
            "q": query,
            "hl": "tr",
            "gl": "tr",
            "num": "4",
            "api_key": serpapi_key
        }
        res = requests.get("https://serpapi.com/search", params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            
            # 1. Google Harita / Knowledge Graph Kontrolü
            kg = data.get("knowledge_graph", {})
            if kg:
                if need_phone and "phone" in kg:
                    final_phone = extract_tr_phone(kg.get("phone"))
                    if final_phone:
                        need_phone = False
                
                if need_city and "address" in kg:
                    found_c = find_city_in_text(kg.get("address"))
                    if found_c:
                        final_city = found_c
                        need_city = False

            # 2. Arama Sonuçları Metin Taraması
            snippets_combined = []
            for r in data.get("organic_results", []):
                snippet_text = f"{r.get('title', '')} {r.get('snippet', '')}"
                snippets_combined.append(snippet_text)

                if need_phone and not final_phone:
                    phone_cand = extract_tr_phone(snippet_text)
                    if phone_cand:
                        final_phone = phone_cand
                        need_phone = False

                if need_city and (final_city == "BELİRTİLMEDİ" or not final_city):
                    city_cand = find_city_in_text(snippet_text)
                    if city_cand:
                        final_city = city_cand
                        need_city = False

            # 3. Bilgiler hala eksikse Gemini AI ile arama metnini analiz et
            if (need_city and (final_city == "BELİRTİLMEDİ" or not final_city)) or (need_phone and not final_phone):
                ai_prompt = f"""
Firma: {company_name}
Aşağıdaki Google arama metinlerini incele:
{json.dumps(snippets_combined, ensure_ascii=False)}

GÖREV:
Bu firmanın Türkiye'deki merkezinin bulunduğu ŞEHİR (Türkiye ili) ve İLETİŞİM NUMARASINI (sabit hat veya santral) tespit et.
Sadece JSON döndür:
{{"city": "İSTANBUL", "phone": "0212 123 45 67"}}
Bulamadığın alan için null yaz.
"""
                ai_resp = call_gemini_rest(ai_prompt)
                if ai_resp:
                    try:
                        parsed = json.loads(ai_resp)
                        if need_city and parsed.get("city"):
                            ai_city = find_city_in_text(parsed.get("city"))
                            if ai_city:
                                final_city = ai_city
                        if need_phone and parsed.get("phone"):
                            ai_ph = extract_tr_phone(parsed.get("phone"))
                            if ai_ph:
                                final_phone = ai_ph
                    except Exception:
                        pass

    except Exception as e:
        print(f"[-] Zenginleştirme hatası ({company_name}): {e}")

    # Şehir hala bulunamadıysa en azından varsayılan sanayi merkezi olarak İSTANBUL atanır
    if not final_city or final_city == "BELİRTİLMEDİ":
        final_city = "İSTANBUL"

    return final_city, final_phone
