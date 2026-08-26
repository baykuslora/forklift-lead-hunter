import os
import re
import requests
from urllib.parse import quote_plus

def clean_company_name(name: str) -> str:
    noise_words = ["a.ş.", "a.ş", "as", "ltd.", "ltd", "şti.", "şti", "san.", "tic.", "sanayi", "ticaret", "ve"]
    words = name.lower().split()
    cleaned = [w for w in words if w not in noise_words]
    return " ".join(cleaned) if cleaned else name

def extract_tr_phone(text: str) -> str:
    if not text:
        return ""
    pattern = r'(?:\+?90|0)?\s*(?:\(?[1-9]\d{2}\)?)\s*\d{3}\s*\d{2}\s*\d{2}'
    matches = re.findall(pattern, text)
    if matches:
        clean_num = re.sub(r'\D', '', matches[0])
        if clean_num.startswith('90'):
            clean_num = clean_num[2:]
        if clean_num.startswith('0'):
            clean_num = clean_num[1:]
        return f"0 ({clean_num[:3]}) {clean_num[3:6]} {clean_num[6:8]} {clean_num[8:]}"
    return ""

def enrich_company_phone(company_name: str, city: str = "") -> dict:
    search_query = f"{clean_company_name(company_name)} {city} iletişim telefon"
    serpapi_key = os.getenv("SERPAPI_KEY")
    
    if serpapi_key:
        try:
            url = f"https://serpapi.com/search.json?q={quote_plus(search_query)}&hl=tr&gl=tr&api_key={serpapi_key}"
            res = requests.get(url, timeout=10).json()
            if "knowledge_graph" in res and "phone" in res["knowledge_graph"]:
                return {"phone": res["knowledge_graph"]["phone"], "source": "Google KG"}
            for result in res.get("organic_results", [])[:3]:
                snippet = result.get("snippet", "")
                found_phone = extract_tr_phone(snippet)
                if found_phone:
                    return {"phone": found_phone, "source": "Google Snippet"}
        except Exception as e:
            print(f"SerpAPI Hatası ({company_name}): {e}")

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        ddg_url = f"https://html.duckduckgo.com/html/?q={quote_plus(search_query)}"
        resp = requests.get(ddg_url, headers=headers, timeout=8)
        found_phone = extract_tr_phone(resp.text)
        if found_phone:
            return {"phone": found_phone, "source": "DuckDuckGo"}
    except Exception:
        pass

    return {"phone": "Bulunamadı (Manuel Ara)", "source": "Yok"}