import re
import requests

def extract_tr_phone(text):
    """Metin içindeki Türkiye sabit veya mobil telefon numaralarını yakalar."""
    if not text:
        return ""
    
    patterns = [
        r'(?:(?:\+90|0090|0)\s*)?(?:[1-5]\d{2}|850|444)\s*(?:[0-9]\s*){7}',
        r'\b(?:0\s*)?[2-5]\d{2}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}\b',
        r'\b(?:0\s*)?5\d{2}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}\b'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            clean_digits = re.sub(r'\D', '', match.group(0))
            if len(clean_digits) >= 10:
                return clean_digits
    return ""

def find_company_phone_online(company_name, city, serpapi_key):
    """İlanda telefon yoksa, Google üzerinde firmanın santral/şirket numarasını arar."""
    if not serpapi_key or not company_name or len(company_name) < 3:
        return ""
    
    query = f'"{company_name}" {city} iletişim telefon santral'
    try:
        params = {
            "engine": "google",
            "q": query,
            "hl": "tr",
            "gl": "tr",
            "num": "3",
            "api_key": serpapi_key
        }
        res = requests.get("https://serpapi.com/search", params=params, timeout=6)
        if res.status_code == 200:
            data = res.json()
            
            # 1. Google Haritalar / Knowledge Panel Telefonu
            kg = data.get("knowledge_graph", {})
            if kg and "phone" in kg:
                phone = extract_tr_phone(kg.get("phone"))
                if phone:
                    return phone

            # 2. İlk 3 Arama Sonucu
            for result in data.get("organic_results", []):
                snippet_text = f"{result.get('title', '')} {result.get('snippet', '')}"
                phone = extract_tr_phone(snippet_text)
                if phone:
                    return phone
    except Exception:
        # Zaman aşımı veya ağ hatası olursa akışı durdurmadan devam et
        pass
        
    return ""
