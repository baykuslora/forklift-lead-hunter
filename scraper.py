import os
import re
import requests
from enricher import extract_tr_phone

class JobLeadScraper:
    def __init__(self):
        self.raw_leads = []
        self.seen_signatures = set()
        self.serpapi_key = os.getenv("SERPAPI_KEY", "").strip()

    def _add_lead(self, source, company, title, city, link, text=""):
        company = (company or "Firma Belirtilmemiş").strip()[:60]
        title = (title or "Forklift Operatörü").strip()[:60]
        city = (city or "Türkiye").strip()[:40]

        signature = f"{company.lower()}_{city.lower()}"
        if signature in self.seen_signatures:
            return

        self.seen_signatures.add(signature)
        phone = extract_tr_phone(text) if text else ""

        self.raw_leads.append({
            "source": source,
            "company_name": company,
            "job_title": title,
            "city": city,
            "job_url": link or "https://www.google.com",
            "direct_phone": phone or ""
        })

    def scrape_serpapi_jobs(self):
        if not self.serpapi_key:
            print("[-] SERPAPI_KEY bulunamadı!")
            return

        print("[+] Türkiye geneli sanayi ve lojistik ilan havuzu taranıyor...")

        google_queries = [
            'forklift operatörü İstanbul (site:eleman.net OR site:kariyer.net OR site:isinolsun.com OR site:secretcv.com)',
            'forklift şoförü Kocaeli Gebze (site:eleman.net OR site:kariyer.net OR site:isinolsun.com OR site:secretcv.com)',
            'forklift operatörü Bursa İzmir Ankara (site:eleman.net OR site:kariyer.net OR site:isinolsun.com)',
            'reach truck operatörü (site:eleman.net OR site:kariyer.net OR site:isinolsun.com OR site:secretcv.com)',
            'depo forklift operatörü (site:eleman.net OR site:kariyer.net OR site:isinolsun.com)',
            'istif makinesi operatörü depo elemanı (site:eleman.net OR site:kariyer.net OR site:isinolsun.com)'
        ]

        for q in google_queries:
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
                    results = data.get("organic_results", [])
                    for r in results:
                        raw_title = r.get("title", "")
                        snippet = r.get("snippet", "")
                        link = r.get("link", "")

                        # Gerçek firma adını başlıktan çekme
                        parts = [p.strip() for p in re.split(r'[-–|:]', raw_title) if p.strip()]
                        company = ""
                        for p in parts:
                            p_clean = re.sub(r'(is-ilani|iş ilanı|eleman\.net|kariyer\.net|isinolsun|secretcv|arayanlar|iş ilanları)', '', p, flags=re.I).strip()
                            if len(p_clean) > 2 and not any(w in p_clean.lower() for w in ["forklift", "operatör", "şoför", "reach truck", "istif", "eleman"]):
                                company = p_clean
                                break
                        
                        if not company and len(parts) > 1:
                            company = parts[1]

                        # İl tespiti
                        city = "Türkiye"
                        for c in ["İstanbul", "Kocaeli", "Gebze", "Bursa", "İzmir", "Ankara", "Tekirdağ", "Manisa", "Sakarya"]:
                            if c.lower() in (raw_title + " " + snippet).lower():
                                city = c
                                break

                        self._add_lead("Web İlan Havuzu", company, "Forklift Operatörü", city, link, f"{raw_title} {snippet}")
            except Exception as e:
                print(f"[-] Arama hatası: {e}")

        print(f"[✓] Tarama tamamlandı. Toplam toplanan tekil lead: {len(self.raw_leads)}")

    def run_all(self):
        self.scrape_serpapi_jobs()
        return self.raw_leads
