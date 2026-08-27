import os
import json
import re
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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

def extract_leads_with_ai(raw_search_results: list) -> list:
    """Ham arama sonuçlarını Gemini AI ile işleyip saf kurumsal ilanlara dönüştürür."""
    if not GEMINI_API_KEY:
        print("[-] GEMINI_API_KEY bulunamadı, AI çıkarma atlandı.")
        return []

    if not raw_search_results:
        return []

    # Model isimleri sırasıyla denenir
    candidate_models = [
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-pro-latest",
        "gemini-pro"
    ]

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

    response_text = None
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={"response_mime_type": "application/json"}
            )
            response = model.generate_content(prompt)
            if response and response.text:
                response_text = response.text
                print(f"[✓] Gemini modeli başarıyla çalıştı: {model_name}")
                break
        except Exception as err:
            print(f"[-] {model_name} denendi, hata: {err}")
            continue

    if not response_text:
        print("[-] Hiçbir Gemini modeli yanıt veremedi.")
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

        print(f"[✓] AI Analizi: {len(raw_search_results)} ham sonuçtan {len(valid_leads)} geçerli kurumsal lead üretildi.")
        return valid_leads

    except Exception as e:
        print(f"[-] JSON parse hatası: {e}")
        return []
