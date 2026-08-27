import re
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from enricher import extract_tr_phone

class JobLeadScraper:
    def __init__(self):
        self.raw_leads = []
        self.seen_signatures = set()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }
        self.keywords = ["forklift", "forklift-operatoru", "reach-truck", "depo-forklift"]

    def _add_lead(self, source, company, title, city, link, text=""):
        company = (company or "Belirtilmemiş Firma").strip()[:60]
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
            "job_url": link or "https://www.eleman.net",
            "direct_phone": phone or "İlanda Yok"
        })

    def scrape_eleman_net(self):
        """Eleman.net üzerinden birden fazla sayfa ve terim tarar."""
        print("[+] Eleman.net çoklu sayfa taraması başlatıldı...")
        
        search_terms = ["forklift", "forklift operatoru", "reach truck"]
        for term in search_terms:
            for page in range(1, 4):  # İlk 3 sayfa
                url = f"https://www.eleman.net/is-ilanlari?kelime={requests.utils.quote(term)}&sayfa={page}"
                try:
                    res = requests.get(url, headers=self.headers, timeout=12)
                    if res.status_code != 200:
                        continue

                    soup = BeautifulSoup(res.text, "html.parser")
                    
                    # Eleman.net ilan kutucukları
                    job_cards = soup.select("div[class*='job'], div[class*='listing'], a[href*='/is-ilani/'], a[href*='/ilan/']")
                    
                    for card in job_cards:
                        text = card.get_text(" ", strip=True)
                        if not text or "forklift" not in text.lower() and "reach" not in text.lower():
                            continue

                        link = card.get("href", "")
                        if link and not link.startswith("http"):
                            link = f"https://www.eleman.net{link}"

                        lines = [line.strip() for line in text.split("  ") if line.strip()]
                        title = lines[0] if lines else "Forklift Operatörü"
                        company = lines[1] if len(lines) > 1 else "Potansiyel Firma"

                        self._add_lead("Eleman.net", company, title, "Türkiye", link, text)
                except Exception as e:
                    print(f"[-] Eleman.net hata ({term} - s.{page}): {e}")

        print(f"[✓] Eleman.net tamamlandı. Güncel havuz: {len(self.raw_leads)} lead.")

    def scrape_isinolsun(self):
        """İşinolsun web sitesinden hızlandırılmış (Asset-blocked) Playwright ile veri çeker."""
        print("[+] Isinolsun.com optimize tarama başlatıldı...")
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-gpu"]
            )
            context = browser.new_context(
                user_agent=self.headers["User-Agent"],
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()

            # Resim, CSS ve fontları engelleyerek sayfayı 1-2 saniyede aç
            def block_heavy_assets(route):
                if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
                    route.abort()
                else:
                    route.continue_()

            page.route("**/*", block_heavy_assets)

            queries = ["forklift", "reach-truck"]
            for q in queries:
                try:
                    target_url = f"https://isinolsun.com/is-ilanlari?q={q}"
                    page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
                    page.wait_for_timeout(2500)

                    # Sayfayı 2 kez hafifçe kaydır (Lazy load ilanları tetikle)
                    page.mouse.wheel(0, 1500)
                    page.wait_for_timeout(1500)

                    cards = page.query_selector_all("article, [data-testid='job-item'], div[class*='jobCard'], a[href*='/is-ilani/']")
                    for card in cards:
                        text = card.inner_text()
                        if not text:
                            continue
                        
                        lines = [l.strip() for l in text.split("\n") if l.strip()]
                        title = lines[0] if lines else "Forklift Operatörü"
                        company = lines[1] if len(lines) > 1 else "Belirtilmemiş Firma"
                        city = lines[2] if len(lines) > 2 else "Türkiye"

                        link_elem = card.query_selector("a") or card
                        link = link_elem.get_attribute("href") if link_elem else ""
                        if link and not link.startswith("http"):
                            link = f"https://isinolsun.com{link}"

                        self._add_lead("İşinolsun", company, title, city, link, text)
                except Exception as e:
                    print(f"[-] Isinolsun hata ({q}): {e}")

            browser.close()
        print(f"[✓] İşinolsun tamamlandı. Toplam ham havuz: {len(self.raw_leads)} lead.")

    def run_all(self):
        self.scrape_eleman_net()
        self.scrape_isinolsun()
        return self.raw_leads
