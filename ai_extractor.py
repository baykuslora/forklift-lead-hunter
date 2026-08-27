import os
import json
import re
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

def tr_upper(text):
    if not text:
        return ""
    text = str(text).strip()
    tr_map = {'i': 'İ', 'ı': 'I', 'ç': 'Ç', 'ş': 'Ş', 'ğ': 'Ğ', 'ü': 'Ü', 'ö': 'Ö'}
    for lower_c, upper_c in tr_map.items():
        text = text.replace(lower_c, upper_c)
    return text.upper()

def format_phone_3322(phone_raw):
    if not phone_raw:
        return ""
    digits = re.sub(r'\D', '', str(phone_raw))
    if digits.startswith("90") and len(digits) >= 12:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) >= 11:
        digits = digits[1:]
        
    if len(digits) == 10 and digits[0] in ['2', '3', '4', '5', '8']:
        return f"{digits[0:3]} {digits[3:6]} {digits[6:8]} {digits[8:10]}"
    if len(digits) == 7 and digits.startswith("444"):
        return f"{digits[0:3]} {digits[3]} {digits[4:7]}"
    return ""

def get_active_gemini_models():
    """Çalışan hızlı modeli ilk sıraya alarak pipeline süresini kısaltır."""
    priority_models = ["gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-1.5-flash"]
    if not GEMINI_API_KEY:
        return priority_models
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            models_data = resp.json().get("models", [])
            active_names = [
                m.get("name", "").replace("models/", "") 
                for m in models_data 
                if "generateContent" in m.get("supportedGenerationMethods", [])
            ]
            sorted_models = [m for m in priority_models if m in active_names]
            for m in active_names:
                if m not in sorted_models and "flash" in m.lower() and "image" not in m.lower() and "tts" not in m.lower():
                    sorted_models.append(m)
            if sorted_models:
                return sorted_models
    except Exception:
        pass
    return priority_models

def call_gemini_rest(prompt: str) -> str:
    """Google Gemini REST API üzerinden JSON yanıtı alır."""
    if not GEMINI_API_KEY:
        print("[-] GEMINI_API_KEY tanımlı değil!")
        return ""

    candidate_models = get_active_gemini_models()
    
    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                print(f"[✓] Gemini API ({model}) ile başarıyla yanıt alındı.")
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            continue

    return ""

def fallback_parser(raw_search_results: list) -> list:
    """Yapay zeka yanıt veremezse devreye giren emniyet motoru."""
    print("[*] Emniyet motoru devreye girdi, ilanlar doğrudan ayrıştırılıyor...")
    leads = []
    
    junk_words = [
        "FORKLİFT OPERATÖRÜ", "REACH TRUCK", "İSTİF MAKİNESİ", "İŞ İLANLARI", "İŞ İLANI", 
        "GÜNCEL İŞ", "ARANIYOR", "MAAŞLARI", "NEDİR", "CV", "ÖZGEÇMİŞ", "ELEMAN.NET", 
        "KARİYER.NET", "İŞİN OLSUN", "INDEED", "LINKEDIN"
    ]
    
    for item in raw_search_results:
        title = item.get("title", "")
        link = item.get("link", "")
        snippet = item.get("snippet", "")
        
        clean_title = re.sub(r'\s*\|\s*(Kariyer\.net|LinkedIn|Eleman\.net|Indeed|Secretcv|İşinolsun).*$', '', title, flags=re.I)
        clean_title = re.sub(r'\s*-\s*(Kariyer\.net|LinkedIn|Eleman\.net|Indeed|Secretcv|İşinolsun).*$', '', clean_title, flags=re.I)
        
        parts = [p.strip() for p in re.split(r'\s*[-–|•:]\s*', clean_title) if p.strip()]
        
        company = ""
        for p in parts:
            p_up = tr_upper(p)
            if not any(j in p_up for j in junk_words) and len(p_up) >= 3:
                company = p_up
                break
                
        if company and len(company) >= 3:
            city = "İSTANBUL"
            for c in ["KOCAELİ", "BURSA", "İZMİR", "ANKARA", "TEKİRDAĞ", "SAKARYA", "MANİSA"]:
                if c in tr_upper(title + " " + snippet):
                    city = c
                    break
                    
            source_site = "WEB"
            if "kariyer.net" in link: source_site = "KARİYER.NET"
            elif "eleman.net" in link: source_site = "ELEMAN.NET"
            elif "isinolsun" in link: source_site = "İŞİN OLSUN"
            elif "linkedin" in link: source_site = "LINKEDIN"
            elif "indeed" in link: source_site = "INDEED"

            leads.append({
                "company_name": company,
                "city": city,
                "direct_phone": "",
                "source_website": source_site,
                "job_url": link
            })
            
    return leads

def extract_leads_with_ai(raw_search_results: list) -> list:
    if not raw_search_results:
        return []

    prompt = f"""
Sen B2B satış odaklı bir veri analiz uzmanısın.
Aşağıda Google/SerpApi üzerinden toplanan forklift, istif makinesi ve reach truck iş ilanı arama sonuçları yer alıyor.

GÖREV:
Her bir arama sonucunu incele ve JSON formatında bir liste döndür:
1. "is_valid_forklift_job": SADECE forklift operatörü, reach truck şoförü veya istif makinesi operatörü arayan GERÇEK İŞ İLANLARI için true yap. İş arayan kişilerin CV/özgeçmiş sayfaları, genel kategori sayfaları, maaş rehberleri veya SEO makaleleri için kesinlikle FALSE yap.
2. "company_name": İlanı açan ŞİRKETİN RESMİ ADINI çıkar. Kesinlikle "Forklift Operatörü", "Reach Truck", "SEO Uzmanı", "İş İlanları" gibi pozisyon adlarını veya şahıs adlarını şirket adı olarak alma. Şirket adı net değilse veya bulunamıyorsa null yap.
3. "city": İlanın ait olduğu Türkiye ilini tespit et (Örn: Gebze, Çayırova -> KOCAELİ, Çorlu -> TEKİRDAĞ, Tuzla -> İSTANBUL).
4. "phone": İlan açıklamasında geçen sabit/cep telefon numarasını çıkar, yoksa null yap.
5. "source_website": İlanın alındığı ana platform adı (KARİYER.NET, ELEMAN.NET, İŞİN OLSUN, LINKEDIN, INDEED, SECRETCV).
6. "job_url": Verilen linki aynen koru.

JSON Şeması:
[
  {{
    "is_valid_forklift_job": true,
    "company_name": "ŞİRKET ADI",
    "city": "ŞEHİR",
    "phone": "05321234567",
    "source_website": "ELEMAN.NET",
    "job_url": "https://..."
  }}
]

İşlenecek Arama Sonuçları:
{json.dumps(raw_search_results, ensure_ascii=False, indent=2)}
"""

    response_text = call_gemini_rest(prompt)
    
    if not response_text:
        return fallback_parser(raw_search_results)

    try:
        parsed_data = json.loads(response_text)
        valid_leads = []
        for item in parsed_data:
            if not item.get("is_valid_forklift_job"):
                continue
            
            company = tr_upper(item.get("company_name"))
            city = tr_upper(item.get("city"))
            raw_phone = item.get("phone")
            source_web = tr_upper(item.get("source_website"))
            url = item.get("job_url", "")

            if not company or len(company) < 3 or company in ["FORKLİFT OPERATÖRÜ", "İŞ İLANI", "POTANSİYEL FİRMA"]:
                continue

            valid_leads.append({
                "company_name": company,
                "city": city if city else "BELİRTİLMEDİ",
                "direct_phone": format_phone_3322(raw_phone),
                "source_website": source_web if source_web else "WEB",
                "job_url": url
            })

        print(f"[✓] AI Analizi: {len(raw_search_results)} ham sonuçtan {len(valid_leads)} net kurumsal lead çıkarıldı.")
        return valid_leads if valid_leads else fallback_parser(raw_search_results)

    except Exception as e:
        print(f"[-] JSON parse hatası: {e}")
        return fallback_parser(raw_search_results)
