import os
import json
import re
import requests
from bs4 import BeautifulSoup
from enricher import extract_tr_phone

class JobLeadScraper:
    def __init__(self):
        self.raw_leads = []
        self.seen_signatures = set()
        self.serpapi_key = os.getenv("SERPAPI_KEY", "").strip()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

    def _add_lead(self, source, company, title, city, link, text=""):
        company = (company or "Potansiyel Firma").strip()[:60]
        title = (title or "Forklift Operatörü").strip()[:60]
        city = (city or "İstanbul / Türkiye").strip()[:40]

        # Mükerrerleri bellekte engelle
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

    def scrape_serpapi_google_jobs(self):
        """Google Jobs (Kariyer.net, Eleman.net, LinkedIn ortak havuzu) taraması yapar."""
        if not self.serpapi_key:
            print("[-] SERPAPI_KEY bulunamadı, Google Jobs atlanıyor.")
            return

        print("[+] Google Jobs (SerpApi) havuzu taranıyor...")
        queries = ["forklift operatörü Türkiye", "reach truck operatörü", "depo forklift"]
        
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

                        self._add_lead("Google Jobs", company, title, location, link, f"{desc} {company}")
            except Exception as e:
                print(f"[-] Google Jobs hata ({q}): {e}")

        print(f"[✓] Google Jobs tamamlandı. Güncel havuz: {len(self.raw_leads)} lead.")

    def scrape_eleman_net(self):
        """Eleman.net arama listelerini ve yapısal veri bloklarını tarar."""
        print("[+] Eleman.net taranıyor...")
        urls = [
            "https://www.eleman.net/is-ilanlari?kelime=forklift",
            "https://www.eleman.net/forklift-operatoru-is-ilanlari"
        ]

        for url in urls:
            try:
                res = requests.get(url, headers=self.headers, timeout=12)
                if res.status_code != 200:
                    continue

                soup = BeautifulSoup(res.text, "html.parser")

                # 1. JSON-LD Yapısal Verilerini Ayrıştır
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, list):
                            items = data
                        elif isinstance(data, dict):
                            items = data.get("itemListElement", [data])
                        else:
                            items = []

                        for item in items:
                            job = item.get("item", item) if isinstance(item, dict) else {}
                            if job.get("@type") == "JobPosting":
                                title = job.get("title", "Forklift Operatörü")
                                comp = job.get("hiringOrganization", {}).get("name", "Potansiyel Firma")
                                loc = job.get("jobLocation", {}).get("address", {}).get("addressLocality", "Türkiye")
                                link = job.get("url", "https://www.eleman.net")
                                desc = job.get("description", "")
                                self._add_lead("Eleman.net", comp, title, loc, link, desc)
                    except Exception:
                        continue

                # 2. HTML İlan Kartlarını Ayrıştır
                cards = soup.select(".search-list-item, .job-item, [class*='search-item']")
                for card in cards:
                    text = card.get_text(" ", strip=True)
                    if "forklift" not in text.lower():
                        continue

                    link_elem = card.find("a", href=True)
                    link = link_elem["href"] if link_elem else ""
                    if link and not link.startswith("http"):
                        link = f"https://www.eleman.net{link}"

                    title_elem = card.find(["h2", "h3", "span"], class_=re.compile(r"title|name|header", re.I))
                    title = title_elem.get_text(strip=True) if title_elem else "Forklift Operatörü"

                    comp_elem = card.find(["div", "span", "p"], class_=re.compile(r"company|firma", re.I))
                    company = comp_elem.get_text(strip=True) if comp_elem else "Potansiyel Firma"

                    self._add_lead("Eleman.net", company, title, "Türkiye", link, text)

            except Exception as e:
                print(f"[-] Eleman.net hata ({url}): {e}")

        print(f"[✓] Eleman.net tamamlandı. Güncel havuz: {len(self.raw_leads)} lead.")

    def run_all(self):
        self.scrape_serpapi_google_jobs()
        self.scrape_eleman_net()
        return self.raw_leads
