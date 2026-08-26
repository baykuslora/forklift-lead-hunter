import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
from enricher import extract_tr_phone

class JobLeadScraper:
    def __init__(self):
        self.raw_leads = []

    def scrape_eleman_net(self):
        print("[+] Eleman.net taranıyor...")
        url = "https://www.eleman.net/is-ilanlari/forklift-operatoru"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        try:
            res = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, "html.parser")
            job_cards = soup.select(".list-group-item, .job-item, .listing-card")
            for card in job_cards:
                title_elem = card.select_one("h2, .job-title, a.title")
                company_elem = card.select_one(".company-name, .company")
                city_elem = card.select_one(".city, .location")
                link_elem = card.select_one("a[href*='/is-ilani/']") or title_elem
                if title_elem and company_elem:
                    company = company_elem.text.strip()
                    title = title_elem.text.strip()
                    city = city_elem.text.strip() if city_elem else "Türkiye"
                    link = link_elem.get("href", "") if link_elem else ""
                    if link and not link.startswith("http"):
                        link = f"https://www.eleman.net{link}"
                    self.raw_leads.append({
                        "source": "Eleman.net",
                        "company_name": company,
                        "job_title": title,
                        "city": city,
                        "job_url": link,
                        "direct_phone": extract_tr_phone(card.text) or "İlanda Yok"
                    })
        except Exception as e:
            print(f"[-] Eleman.net hata: {e}")

    def scrape_isinolsun(self):
        print("[+] Isinolsun.com taranıyor...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto("https://isinolsun.com/is-ilanlari?q=forklift", timeout=45000)
                page.wait_for_timeout(3000)
                cards = page.query_selector_all("article, [data-testid='job-item']")
                for card in cards[:25]:
                    text = card.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if len(lines) >= 2:
                        company = lines[1]
                        self.raw_leads.append({
                            "source": "İşinolsun",
                            "company_name": company,
                            "job_title": lines[0],
                            "city": lines[2] if len(lines) > 2 else "Belirtilmemiş",
                            "job_url": "https://isinolsun.com",
                            "direct_phone": extract_tr_phone(text) or "İlanda Yok"
                        })
            except Exception as e:
                print(f"[-] Isinolsun hata: {e}")
            finally:
                browser.close()

    def run_all(self):
        self.scrape_eleman_net()
        self.scrape_isinolsun()
        return self.raw_leads