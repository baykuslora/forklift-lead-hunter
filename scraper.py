import os
import requests
from ai_extractor import extract_leads_with_ai

class JobLeadScraper:
    def __init__(self):
        self.serpapi_key = os.getenv("SERPAPI_KEY", "").strip()

    def scrape_all_sources(self):
        if not self.serpapi_key:
            print("[-] SERPAPI_KEY bulunamadı!")
            return []

        print("[+] Tüm platformlar aranıyor (Kariyer.net, Eleman.net, İşinolsun, Indeed, LinkedIn, Secretcv)...")
        queries = [
            '("forklift operatörü" OR "forklift şoförü") site:kariyer.net',
            '("forklift operatörü" OR "reach truck") site:eleman.net',
            '("forklift operatörü") site:isinolsun.com',
            '("forklift operatörü" OR "reach truck operatörü") site:tr.indeed.com',
            '("forklift operatörü") site:tr.linkedin.com/jobs',
            '("forklift operatörü" OR "istif makinesi") site:secretcv.com'
        ]

        raw_results = []
        seen_links = set()

        for q in queries:
            try:
                params = {
                    "engine": "google",
                    "q": q,
                    "hl": "tr",
                    "gl": "tr",
                    "num": "20",
                    "api_key": self.serpapi_key
                }
                res = requests.get("https://serpapi.com/search", params=params, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    for r in data.get("organic_results", []):
                        link = r.get("link", "")
                        if link and link not in seen_links:
                            seen_links.add(link)
                            raw_results.append({
                                "title": r.get("title", ""),
                                "snippet": r.get("snippet", ""),
                                "link": link
                            })
            except Exception as e:
                print(f"[-] Arama sorgusu hatası: {e}")

        print(f"[*] Toplam {len(raw_results)} adet ham arama sonucu toplandı. Yapay zeka analizine gönderiliyor...")
        
        # Yapay zeka ile kurumsal firma ayrıştırma
        return extract_leads_with_ai(raw_results)

    def run_all(self):
        return self.scrape_all_sources()
