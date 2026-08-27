import re
import requests

def extract_tr_phone(text):
    """Metin içindeki geçerli sabit ve mobil Türkiye telefon numaralarını yakalar."""
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
            clean_digits = re.sub(r'\D', '', match.group(0))
            if clean_digits.startswith("90") and len(clean_digits) >= 12:
                clean_digits = clean_digits[2:]
            elif clean_digits.startswith("0") and len(clean_digits) >= 11:
                clean_digits = clean_digits[1:]
            return clean_digits
    return ""

def find_company_phone_online(company_name, city, serpapi_key):
    """İlanda telefon yoksa firmanın kurumsal santral/iletişim numarasını Google'dan bulur."""
    if not serpapi_key or not company_name or len(company_name) < 3:
        return ""
    
    query = f'"{company_name}" {city} telefon OR iletişim OR santral'
    try:
        params = {
            "engine": "google",
            "q": query,
            "hl": "tr",
            "gl": "tr",
            "num": "3",
            "api_key": serpapi_key
        }
        res = requests.get("https://serpapi.com/search", params=params, timeout=8)
        if res.status_code == 200:
            data = res.json()
            
            kg = data.get("knowledge_graph", {})
            if kg and "phone" in kg:
                phone = extract_tr_phone(kg.get("phone"))
                if phone:
                    return phone

            for result in data.get("organic_results", []):
                snippet_text = f"{result.get('title', '')} {result.get('snippet', '')}"
                phone = extract_tr_phone(snippet_text)
                if phone:
                    return phone
    except Exception:
        pass
        
    return ""
