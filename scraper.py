import re
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from enricher import extract_tr_phone

class JobLeadScraper:
    def __init__(self):
        self.raw_leads = []
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }

    def scrape_eleman_net(self):
        """Eleman.net üzerinden forklift ilanlarını çeker."""
        print("[+] Eleman.net taranıyor...")
        url = "https://www.eleman.net/is-ilanlari?kelime=forklift"
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Güncel Eleman.net ilan listeleme etiketleri
            job_rows = soup.select("div.search-list-item, div.job-item, a[class*='listing'], div[class*='list-item']")
            if not job_rows:
                # Alternatif: Sayfadaki linkler üzerinden yakala
                job_rows = soup.find_all("a", href=re.compile(r"/is-ilani/|/ilan/"))

            for card in job_rows[:35]:
                text = card.get_text(" ", strip=True)
                if not text or "forklift" not in text.lower():
                    continue

                link = card.get("href", "")
                if link and not link.startswith("http"):
                    link = f"https://www.eleman.net{link}"

                # Metinden firma ve pozisyon tahmin etme
                lines = [line.strip() for line in text.split("  ") if line.strip()]
                company = lines[1] if len(lines) > 1 else lines[0]
                title = lines[0] if lines else "Forklift Operatörü"

                self.raw_leads.append({
                    "source": "Eleman.net",
                    "company_name": company[:60],
                    "job_title": title[:60],
                    "city": "İstanbul / Türkiye",
                    "job_url": link or "https://www.eleman.net",
                    "direct_phone": extract_tr_phone(text) or "İlanda Yok"
                })
            print(f"[✓] Eleman.net'ten {len(self.raw_leads)} ilan yakalandı.")
        except Exception as e:
            print(f"[-] Eleman.net hata: {e}")

    def scrape_isinolsun(self):
        """İşinolsun web sitesinden dinamik veri çeker (Hızlı DOM modu)."""
        print("[+] Isinolsun.com taranıyor...")
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            context = browser.new_context(
                user_agent=self.headers["User-Agent"],
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            try:
                # Networkidle yerine domcontentloaded ile takılmaları önle
                page.goto(
                    "https://isinolsun.com/is-ilanlari?q=forklift",
                    wait_until="domcontentloaded",
                    timeout=20000
                )
                page.wait_for_timeout(3000)

                cards = page.query_selector_all("article, [data-testid='job-item'], div[class*='jobCard']")
                for card in cards[:30]:
                    text = card.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if len(lines) >= 2:
                        title = lines[0]
                        company = lines[1]
                        city = lines[2] if len(lines) > 2 else "Türkiye"
                        link_elem = card.query_selector("a")
                        link = link_elem.get_attribute("href") if link_elem else ""
                        if link and not link.startswith("http"):
                            link = f"https://isinolsun.com{link}"

                        self.raw_leads.append({
                            "source": "İşinolsun",
                            "company_name": company[:60],
                            "job_title": title[:60],
                            "city": city[:40],
                            "job_url": link or "https://isinolsun.com",
                            "direct_phone": extract_tr_phone(text) or "İlanda Yok"
                        })
                print(f"[✓] Toplam lead sayısı (İşinolsun dahil): {len(self.raw_leads)}")
            except Exception as e:
                print(f"[-] Isinolsun hata: {e}")
            finally:
                browser.close()

    def run_all(self):
        self.scrape_eleman_net()
        self.scrape_isinolsun()
        return self.raw_leads
