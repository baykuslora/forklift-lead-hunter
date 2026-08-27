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
        company = (company or "Potansiyel Firma").strip()[:60]
        title = (title or "Forklift Operatörü").strip()[:60]
        city = (city or "Türkiye").strip()[:40]

        # Temizlik ve mükerrer engelleme
        signature = f"{company.lower()}_{title.lower()}"
        if signature in self.seen_signatures or len(company) < 2:
            return

        self.seen_signatures.add(signature)
        phone = extract_tr_phone(text) if text else "İlanda Yok"

        self.raw_leads.append({
            "source": source,
            "company_name": company,
            "job_title": title,
            "city": city,
            "job_url": link or "https://www.google.com",
            "direct_phone": phone or "İlanda Yok"
        })

    def scrape_serpapi_jobs(self):
        """Türkiye genelindeki ilanları hedefli hızlı arama motoru ile çeker (Sıfır bekleme)."""
        if not self.serpapi_key:
            print("[-] SERPAPI_KEY bulunamadı!")
            return

        print("[+] Türkiye geneli sanayi ve lojistik ilan havuzu taranıyor...")

        # Tüm büyük iş sitelerini ve sanayi bölgelerini kapsayan 6 hızlı sorgu
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
                    print(f"[+] '{q[:30]}...' -> {len(results)} ilan yakalandı.")
                    for r in results:
                        raw_title = r.get("title", "")
                        snippet = r.get("snippet", "")
                        link = r.get("link", "")

                        # Başlıktan firma adını ayıkla
                        parts = [p.strip() for p in re.split(r'[-–|]', raw_title) if p.strip()]
                        title = parts[0] if parts else "Forklift Operatörü"
                        company = "Potansiyel Firma"
                        if len(parts) > 1:
                            for p in parts[1:]:
                                if not any(site in p.lower() for site in ["eleman", "kariyer", "isinolsun", "secretcv", "ilan", "iş ilanları"]):
                                    company = p
                                    break

                        # Lokasyon yakalama
                        city = "Türkiye"
                        for c in ["İstanbul", "Kocaeli", "Gebze", "Bursa", "İzmir", "Ankara", "Tekirdağ", "Manisa", "Sakarya"]:
                            if c.lower() in (raw_title + " " + snippet).lower():
                                city = c
                                break

                        self._add_lead("Web İlan Havuzu", company, title, city, link, f"{raw_title} {snippet}")
            except Exception as e:
                print(f"[-] Arama hatası: {e}")

        print(f"[✓] Tarama tamamlandı. Toplam toplanan tekil lead: {len(self.raw_leads)}")

    def run_all(self):
        self.scrape_serpapi_jobs()
        return self.raw_leads
