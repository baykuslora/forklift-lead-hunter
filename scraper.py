import re
import requests
from bs4 import BeautifulSoup
from enricher import extract_tr_phone

class JobLeadScraper:
    def __init__(self):
        self.raw_leads = []
        self.seen_signatures = set()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

    def _add_lead(self, source, company, title, city, link, text=""):
        company = (company or "Potansiyel Firma").strip()[:60]
        title = (title or "Forklift Operatörü").strip()[:60]
        city = (city or "İstanbul / Türkiye").strip()[:40]

        # Tekrarlayan ilanları bellekte ayıkla
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
            "job_url": link,
            "direct_phone": phone or "İlanda Yok"
        })

    def scrape_eleman_net(self):
        """Eleman.net kategori sayfalarından çoklu sayfa taraması yapar."""
        print("[+] Eleman.net taranıyor...")
        base_urls = [
            "https://www.eleman.net/forklift-operatoru-is-ilanlari",
            "https://www.eleman.net/reach-truck-operatoru-is-ilanlari"
        ]

        for base_url in base_urls:
            for page in range(1, 4):  # İlk 3 sayfa
                url = f"{base_url}?sayfa={page}" if page > 1 else base_url
                try:
                    res = requests.get(url, headers=self.headers, timeout=10)
                    if res.status_code != 200:
                        continue

                    soup = BeautifulSoup(res.text, "html.parser")
                    cards = soup.find_all(["div", "article"], class_=re.compile(r"item|card|listing|box", re.I))
                    
                    if not cards:
                        cards = soup.find_all("a", href=re.compile(r"/is-ilani/"))

                    for card in cards:
                        text = card.get_text(" ", strip=True)
                        if not text or len(text) < 15:
                            continue

                        link_tag = card if card.name == "a" else card.find("a", href=True)
                        link = link_tag.get("href", "") if link_tag else ""
                        if link and not link.startswith("http"):
                            link = f"https://www.eleman.net{link}"

                        lines = [line.strip() for line in text.split("  ") if len(line.strip()) > 1]
                        title = lines[0] if lines else "Forklift Operatörü"
                        company = lines[1] if len(lines) > 1 else "Belirtilmemiş Firma"
                        city = lines[2] if len(lines) > 2 else "Türkiye"

                        if any(k in text.lower() for k in ["forklift", "reach truck", "istif", "operatör"]):
                            self._add_lead("Eleman.net", company, title, city, link, text)

                except Exception as e:
                    print(f"[-] Eleman.net hata ({url}): {e}")

        print(f"[✓] Eleman.net tamamlandı. Güncel havuz: {len(self.raw_leads)} lead.")

    def scrape_isbul_net(self):
        """İşbul.net üzerinden forklift ilanlarını çeker (Hızlı ve engelsiz)."""
        print("[+] İşbul.net taranıyor...")
        search_urls = [
            "https://www.isbul.net/is-ilanlari?aranan_kelime=forklift",
            "https://www.isbul.net/forklift-operatoru-is-ilanlari"
        ]

        for target_url in search_urls:
            for page in range(1, 4):  # İlk 3 sayfa
                url = f"{target_url}&sayfa={page}" if "?" in target_url else f"{target_url}?sayfa={page}"
                try:
                    res = requests.get(url, headers=self.headers, timeout=10)
                    if res.status_code != 200:
                        continue

                    soup = BeautifulSoup(res.text, "html.parser")
                    cards = soup.find_all(["div", "li"], class_=re.compile(r"job|listing|ilan", re.I))

                    for card in cards:
                        text = card.get_text(" ", strip=True)
                        if not text or "forklift" not in text.lower():
                            continue

                        link_tag = card.find("a", href=True)
                        link = link_tag.get("href", "") if link_tag else ""
                        if link and not link.startswith("http"):
                            link = f"https://www.isbul.net{link}"

                        lines = [l.strip() for l in text.split("  ") if l.strip()]
                        title = lines[0] if lines else "Forklift Operatörü"
                        company = lines[1] if len(lines) > 1 else "Potansiyel Firma"
                        city = lines[2] if len(lines) > 2 else "İstanbul / Türkiye"

                        self._add_lead("İşbul.net", company, title, city, link, text)

                except Exception as e:
                    print(f"[-] İşbul.net hata ({url}): {e}")

        print(f"[✓] İşbul.net tamamlandı. Toplam ham havuz: {len(self.raw_leads)} lead.")

    def run_all(self):
        self.scrape_eleman_net()
        self.scrape_isbul_net()
        return self.raw_leads
