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

def call_gemini_rest(prompt: str) -> str:
    """SDK bağımlılığı olmadan doğrudan Google REST API üzerinden çalışır."""
    if not GEMINI_API_KEY:
        return ""

    # Kullanılabilir güncel modeller sırayla denenir
    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-pro"]
    
    for model in models:
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
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            continue

    return ""

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
        print("[-] Gemini REST API yanıt vermedi.")
        return []

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
            if not city or city in ["TÜRKİYE", "TUMU"]:
                continue

            valid_leads.append({
                "company_name": company,
                "city": city,
                "direct_phone": format_phone_3322(raw_phone),
                "source_website": source_web if source_web else "WEB",
                "job_url": url
            })

        print(f"[✓] REST AI Analizi: {len(raw_search_results)} ham sonuçtan {len(valid_leads)} temiz kurumsal lead üretildi.")
        return valid_leads

    except Exception as e:
        print(f"[-] JSON parse hatası: {e}")
        return []
