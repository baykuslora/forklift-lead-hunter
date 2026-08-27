import os
import re
import requests
from enricher import extract_tr_phone

TURKISH_CITIES = [
    "İSTANBUL", "KOCAELİ", "BURSA", "İZMİR", "ANKARA", "SAKARYA", 
    "TEKİRDAĞ", "MANİSA", "ADANA", "ANTALYA", "KONYA", "GAZİANTEP", 
    "ESKİŞEHİR", "KAYSERİ", "MERSİN", "DENİZLİ", "SAMSUN", "BALIKESİR", 
    "AYDIN", "YALOVA", "BOLU", "DÜZCE", "BİLECİK", "KÜTAHYA", "ÇANAKKALE"
]

JOB_TITLE_KEYWORDS = [
    "forklift", "reach truck", "reachtruck", "istif", "operatör", "operatörü", 
    "şoför", "şoförü", "sürücü", "depo", "sevkiyat", "eleman", "elemanı", 
    "görevlisi", "personel", "iş ilanı", "ilanı", "iş fırsatı", "hiring", 
    "kariyer.net", "eleman.net", "isinolsun", "secretcv", "linkedin", "indeed"
]

class JobLeadScraper:
    def __init__(self):
        self.raw_leads = []
        self.seen_signatures = set()
        self.serpapi_key = os.getenv("SERPAPI_KEY", "").strip()

    def _extract_city(self, text):
        t_upper = text.upper()
        if any(k in t_upper for k in ["GEBZE", "ÇAYIROVA", "DİLOVASI", "DARICA", "KÖRFEZ"]):
            return "KOCAELİ"
        if any(k in t_upper for k in ["ÇORLU", "ÇERKEZKÖY", "ERGENE"]):
            return "TEKİRDAĞ"
        if any(k in t_upper for k in ["TUZLA", "ÜMRANİYE", "PENDİK", "ESENYURT", "HADIMKÖY", "BAŞAKŞEHİR"]):
            return "İSTANBUL"

        for city in TURKISH_CITIES:
            if city in t_upper:
                return city
        return "TÜRKİYE"

    def _extract_clean_company(self, raw_title, snippet):
        """Başlık ve özet metinden pozisyon/site adlarını atarak saf şirket adını bulur."""
        # Başlığı ayraçlardan böl
        parts = [p.strip() for p in re.split(r'[-–|:•/]', raw_title) if p.strip()]
        candidate_companies = []

        for p in parts:
            p_lower = p.lower()
            # İçinde pozisyon adı veya site adı geçmeyen parçayı firma adı kabul et
            has_job_word = any(kw in p_lower for kw in JOB_TITLE_KEYWORDS)
            if not has_job_word and len(p.split()) <= 6 and len(p) > 2:
                candidate_companies.append(p)

        if candidate_companies:
            # En uygun firma adını seç ve temizle
            best_cand = candidate_companies[0]
            # "A.Ş", "Ltd. Şti", "Sanayi", "Ticaret" gibi ekleri koru
            return best_cand.strip()

        # LinkedIn özel formatı: "Firma Adı hiring Forklift..."
        m_linkedin = re.search(r'^(.*?)\s+hiring\s+', raw_title, re.I)
        if m_linkedin:
            return m_linkedin.group(1).strip()

        return ""

    def scrape_all_sources(self):
        if not self.serpapi_key:
            print("[-] SERPAPI_KEY bulunamadı!")
            return

        print("[+] LinkedIn, Indeed, Kariyer.net, Eleman.net taranıyor...")

        # Tüm büyük portalları ve sanayi odaklı bölgeleri kapsayan net sorgular
        queries = [
            'forklift operatörü (site:tr.linkedin.com/jobs OR site:tr.indeed.com)',
            'forklift operatörü iş ilanları (site:kariyer.net OR site:eleman.net OR site:isinolsun.com)',
            'reach truck operatörü (site:tr.linkedin.com/jobs OR site:kariyer.net OR site:tr.indeed.com)',
            'forklift şoförü İstanbul Kocaeli Gebze (site:kariyer.net OR site:eleman.net OR site:tr.indeed.com)',
            'depo forklift operatörü İzmir Bursa Ankara (site:kariyer.net OR site:eleman.net)',
            'istif makinesi operatörü depo sevkiyat (site:kariyer.net OR site:eleman.net OR site:tr.indeed.com)'
        ]

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
                res = requests.get("https://serpapi.com/search", params=params, timeout=18)
                if res.status_code == 200:
                    data = res.json()
                    for r in data.get("organic_results", []):
                        raw_title = r.get("title", "")
                        snippet = r.get("snippet", "")
                        link = r.get("link", "")

                        full_text = f"{raw_title} {snippet}"
                        company = self._extract_clean_company(raw_title, snippet)
                        city = self._extract_city(full_text)
                        phone = extract_tr_phone(full_text)

                        # Firma adı bulunamadıysa veya anlamsızsa listeye alma
                        if not company or len(company) < 2 or city == "TÜRKİYE":
                            continue

                        signature = f"{company.lower()}_{city.lower()}"
                        if signature in self.seen_signatures:
                            continue

                        self.seen_signatures.add(signature)
                        self.raw_leads.append({
                            "company_name": company,
                            "city": city,
                            "direct_phone": phone,
                            "job_url": link
                        })
            except Exception as e:
                print(f"[-] Arama hatası ({q[:25]}...): {e}")

        print(f"[✓] Temizlenen toplam nitelikli ilan: {len(self.raw_leads)}")

    def run_all(self):
        self.scrape_all_sources()
        return self.raw_leads
