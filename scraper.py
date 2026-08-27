import os
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

    def scrape_google_jobs(self):
        """Kariyer.net, LinkedIn, Eleman.net ve Secretcv ilanlarını tek havuzda toplar."""
        if not self.serpapi_key:
            print("[-] SERPAPI_KEY bulunamadı, arama yapılamıyor.")
            return

        print("[+] Google Jobs motoru Türkiye geneli taranıyor...")
        
        # Farklı lokasyon ve anahtar kelimelerle zenginleştirilmiş sorgular
        queries = [
            "forklift operatörü iş ilanları İstanbul",
            "forklift şoförü Kocaeli Gebze",
            "reach truck operatörü iş ilanları",
            "depo forklift operatörü Türkiye"
        ]

        for q in queries:
            try:
                params = {
                    "engine": "google_jobs",
                    "q": q,
                    "hl": "tr",
                    "gl": "tr",
                    "api_key": self.serpapi_key
                }
                res = requests.get("https://serpapi.com/search", params=params, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    jobs = data.get("jobs_results", [])
                    for j in jobs:
                        title = j.get("title", "Forklift Operatörü")
                        company = j.get("company_name", "Potansiyel Firma")
                        location = j.get("location", "Türkiye")
                        desc = j.get("description", "")
                        
                        link = ""
                        apply_options = j.get("apply_options", [])
                        if apply_options:
                            link = apply_options[0].get("link", "")
                        if not link:
                            link = j.get("share_link", "https://www.google.com")

                        self._add_lead("Google Jobs Havuzu", company, title, location, link, f"{desc} {company}")
            except Exception as e:
                print(f"[-] Hata ({q}): {e}")

        print(f"[✓] Tarama tamamlandı. Toplam bulunan lead: {len(self.raw_leads)}")

    def run_all(self):
        self.scrape_google_jobs()
        return self.raw_leads
