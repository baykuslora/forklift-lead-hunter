import re
import requests

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

def extract_tr_phone(text):
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

def find_company_phone_online(company_name, city, serpapi_key):
    if not serpapi_key or not company_name or len(company_name) < 3:
        return ""
    
    query = f'"{company_name}" {city} santral OR telefon OR iletişim'
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
