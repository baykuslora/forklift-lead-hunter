import os
import re
import requests
from enricher import extract_tr_phone

class JobLeadScraper:
    def __init__(self):
        self.raw_leads = []
        self.seen_signatures = set()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
            "Origin": "https://isinolsun.com",
            "Referer": "https://isinolsun.com/"
        })

    def _add_lead(self, source, company, title, city, link, text=""):
        company = (company or "Potansiyel Firma").strip()[:70]
        title = (title or "Forklift Operatörü").strip()[:70]
        city = (city or "İstanbul / Türkiye").strip()[:40]

        # Mükerrerleri bellekte engelle
        signature = f"{company.lower()}_{title.lower()}_{city.lower()}"
        if signature in self.seen_signatures:
            return

        self.seen_signatures.add(signature)
        phone = extract_tr_phone(text) if text else "İlanda Yok"

        self.raw_leads.append({
            "source": source,
            "company_name": company,
            "job_title": title,
            "city": city,
            "job_url": link or "https://isinolsun.com",
            "direct_phone": phone or "İlanda Yok"
        })

    def scrape_isinolsun_api(self):
        """İşinolsun mobil ve web arka plan API'si üzerinden veri çeker (WAF engeline takılmaz)."""
        print("[+] İşinolsun API taranıyor...")
        keywords = ["forklift", "reach truck", "istif", "depo operatör"]
        
        for kw in keywords:
            try:
                api_url = f"https://api.isinolsun.com/api/v1/job-postings/search?query={requests.utils.quote(kw)}&limit=30&page=1"
                res = self.session.get(api_url, timeout=12)
                
                if res.status_code == 200:
                    data = res.json()
                    items = data.get("items", []) or data.get("data", []) or data.get("jobPostings", [])
                    
                    for item in items:
                        title = item.get("title") or item.get("jobTitle") or "Forklift Operatörü"
                        company_info = item.get("company", {})
                        company = company_info.get("name") if isinstance(company_info, dict) else str(company_info or "Potansiyel Firma")
                        
                        location_info = item.get("location", {})
                        city = location_info.get("cityName") if isinstance(location_info, dict) else "Türkiye"
                        
                        slug = item.get("slug") or item.get("id", "")
                        job_url = f"https://isinolsun.com/is-ilani/{slug}" if slug else "https://isinolsun.com"
                        
                        desc = item.get("description", "") or item.get("summary", "")
                        full_text = f"{title} {company} {desc}"

                        self._add_lead("İşinolsun", company, title, city, job_url, full_text)
                else:
                    print(f"[-] İşinolsun API yanıt kodu ({kw}): {res.status_code}")
            except Exception as e:
                print(f"[-] İşinolsun API hatası ({kw}): {e}")

        print(f"[✓] İşinolsun API tamamlandı. Toplam havuz: {len(self.raw_leads)} lead.")

    def scrape_eleman_net_api(self):
        """Eleman.net arama servisini browser-mimic başlıklarla sorgular."""
        print("[+] Eleman.net taranıyor...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.eleman.net/"
        }
        
        terms = ["forklift", "reach truck"]
        for term in terms:
            for page in range(1, 4):
                try:
                    url = f"https://www.eleman.net/is-ilanlari?kelime={requests.utils.quote(term)}&sayfa={page}"
                    res = requests.get(url, headers=headers, timeout=12)
                    if res.status_code == 200:
                        # Sayfa içi JSON veya açık veri yapılarını yakala
                        json_matches = re.findall(r'"jobPosting":(\{.*?\})', res.text)
                        for raw_json in json_matches:
                            try:
                                import json
                                j = json.loads(raw_json)
                                title = j.get("title", "Forklift Operatörü")
                                comp = j.get("hiringOrganization", {}).get("name", "Potansiyel Firma")
                                loc = j.get("jobLocation", {}).get("address", {}).get("addressLocality", "Türkiye")
                                link = j.get("url", "https://www.eleman.net")
                                self._add_lead("Eleman.net", comp, title, loc, link, res.text)
                            except Exception:
                                continue

                        # HTML Regex Ayrıştırma (WAF geçişi için hafif parser)
                        cards = re.findall(r'<a[^>]+href="(/is-ilani/[^"]+)"[^>]*>(.*?)</a>', res.text, re.DOTALL)
                        for href, inner in cards:
                            clean_text = re.sub(r'<[^>]+>', ' ', inner).strip()
                            if "forklift" in clean_text.lower() or "reach" in clean_text.lower():
                                full_link = f"https://www.eleman.net{href}"
                                self._add_lead("Eleman.net", "Potansiyel Firma", clean_text[:50], "Türkiye", full_link, clean_text)
                except Exception as e:
                    print(f"[-] Eleman.net hata ({term} s.{page}): {e}")

        print(f"[✓] Eleman.net tamamlandı. Toplam havuz: {len(self.raw_leads)} lead.")

    def run_all(self):
        self.scrape_isinolsun_api()
        self.scrape_eleman_net_api()
        return self.raw_leads
