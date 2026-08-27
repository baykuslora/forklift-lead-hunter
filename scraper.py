import os
import re
import json
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from enricher import extract_tr_phone

TURKISH_81_CITIES = [
    "ADANA", "ADIYAMAN", "AFYONKARAHİSAR", "AĞRI", "AMASYA", "ANKARA", "ANTALYA", "ARTVİN", "AYDIN", 
    "BALIKESİR", "BİLECİK", "BİNGÖL", "BİTLİS", "BOLU", "BURDUR", "BURSA", "ÇANAKKALE", "ÇANKIRI", 
    "ÇORUM", "DENİZLİ", "DİYARBAKIR", "EDİRNE", "ELAZIĞ", "ERZİNCAN", "ERZURUM", "ESKİŞEHİR", 
    "GAZİANTEP", "GİRESUN", "GÜMÜŞHANE", "HAKKARİ", "HATAY", "ISPARTA", "MERSİN", "İSTANBUL", 
    "İZMİR", "KARS", "KASTAMONU", "KAYSERİ", "KIRKLARELİ", "KIRŞEHİR", "KOCAELİ", "KONYA", 
    "KÜTAHYA", "MALATYA", "MANİSA", "KAHRAMANMARAŞ", "MARDİN", "MUĞLA", "MUŞ", "NEVŞEHİR", 
    "NİĞDE", "ORDU", "RİZE", "SAKARYA", "SAMSUN", "SİİRT", "SİNOP", "SİVAS", "TEKİRDAĞ", "TOKAT", "TRABZON", "TUNCELİ", 
    "ŞANLIURFA", "UŞAK", "VAN", "YOZGAT", "ZONGULDAK", "AKSARAY", "BAYBURT", 
    "KARAMAN", "KIRIKKALE", "BATMAN", "ŞIRNAK", "BARTIN", "ARDAHAN", "IĞDIR", 
    "YALOVA", "KARABÜK", "KİLİS", "OSMANİYE", "DÜZCE"
]

DISTRICT_MAP = {
    "GEBZE": "KOCAELİ", "ÇAYIROVA": "KOCAELİ", "DİLOVASI": "KOCAELİ", "DARICA": "KOCAELİ", 
    "KÖRFEZ": "KOCAELİ", "İZMİT": "KOCAELİ", "GÖLCÜK": "KOCAELİ", "KARTEPE": "KOCAELİ", "BAŞİSKELE": "KOCAELİ",
    "ÇORLU": "TEKİRDAĞ", "ÇERKEZKÖY": "TEKİRDAĞ", "ERGENE": "TEKİRDAĞ", "KAPAKLI": "TEKİRDAĞ", "MURATLI": "TEKİRDAĞ",
    "TUZLA": "İSTANBUL", "PENDİK": "İSTANBUL", "KARTAL": "İSTANBUL", "ÜMRANİYE": "İSTANBUL", 
    "SANCAKTEPE": "İSTANBUL", "SULTANBEYLİ": "İSTANBUL", "MALTEPE": "İSTANBUL", "KADIKÖY": "İSTANBUL", 
    "ESENYURT": "İSTANBUL", "HADIMKÖY": "İSTANBUL", "BÜYÜKÇEKMECE": "İSTANBUL", "KÜÇÜKÇEKMECE": "İSTANBUL", 
    "BAŞAKŞEHİR": "İSTANBUL", "ARNAVUTKÖY": "İSTANBUL", "AVCILAR": "İSTANBUL", "BEYLİKDÜZÜ": "İSTANBUL", "SİLİVRİ": "İSTANBUL",
    "NİLÜFER": "BURSA", "OSMANGAZİ": "BURSA", "YILDIRIM": "BURSA", "İNEGÖL": "BURSA", "GEMLİK": "BURSA",
    "ALİAĞA": "İZMİR", "TORBALI": "İZMİR", "KEMALPAŞA": "İZMİR", "ÇİĞLİ": "İZMİR", "BORNOVA": "İZMİR", "MENEMEN": "İZMİR", "GAZİEMİR": "İZMİR",
    "SİNCAN": "ANKARA", "KAZAN": "ANKARA", "KAHRAMANKAZAN": "ANKARA", "ETİMESGUT": "ANKARA", "OSTİM": "ANKARA", "İVEDİK": "ANKARA", "YENİMAHALLE": "ANKARA",
    "HENDEK": "SAKARYA", "ARİFİYE": "SAKARYA", "ERENLER": "SAKARYA", "SERDİVAN": "SAKARYA", "AKYAZI": "SAKARYA"
}

# Şirket adı olamayacak kara liste kalıpları
BLACKLIST_COMPANIES = [
    "GÜNCEL İŞ FIRSATLARI", "İŞ FIRSATLARI", "İŞ İLANI", "İŞ İLANLARI", "KADIN", "ERKEK", 
    "ENGELLİ", "ACİL", "TAM ZAMANLI", "POTANSİYEL FİRMA", "ORTALAMA MAAŞ BİLGİLERİ", 
    "FORKLİFT OPERATÖRÜ", "REACH TRUCK OPERATÖRÜ", "DEPO ELEMANI", "ŞOFÖR", "SEO UZMANI", 
    "GENEL BAŞVURU", "SECRET CV", "ELEMAN.NET", "KARİYER.NET", "İŞİN OLSUN", "İNDEED"
]

def tr_upper(text):
    if not text:
        return ""
    text = str(text).strip()
    tr_map = {'i': 'İ', 'ı': 'I', 'ç': 'Ç', 'ş': 'Ş', 'ğ': 'Ğ', 'ü': 'Ü', 'ö': 'Ö'}
    for lower_c, upper_c in tr_map.items():
        text = text.replace(lower_c, upper_c)
    return text.upper()

class JobLeadScraper:
    def __init__(self):
        self.raw_leads = []
        self.seen_signatures = set()
        self.serpapi_key = os.getenv("SERPAPI_KEY", "").strip()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9"
        })

    def _extract_source_website(self, url):
        domain = urlparse(url).netloc.lower().replace("www.", "")
        if "kariyer.net" in domain:
            return "KARİYER.NET"
        elif "eleman.net" in domain:
            return "ELEMAN.NET"
        elif "linkedin.com" in domain:
            return "LINKEDIN"
        elif "indeed.com" in domain:
            return "INDEED"
        elif "isinolsun.com" in domain:
            return "İŞİN OLSUN"
        elif "secretcv.com" in domain:
            return "SECRETCV"
        return tr_upper(domain)

    def _extract_city(self, full_text):
        text_upper = tr_upper(full_text)
        for dist, prov in DISTRICT_MAP.items():
            if re.search(r'\b' + re.escape(dist) + r'\b', text_upper):
                return prov
        for city in TURKISH_81_CITIES:
            if re.search(r'\b' + re.escape(city) + r'\b', text_upper):
                return city
        return ""

    def _fetch_real_company_from_page(self, url):
        """İlan sayfasına gidip resmi JSON-LD JobPosting etiketini okur."""
        try:
            resp = self.session.get(url, timeout=5)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, "html.parser")
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                if not script.string:
                    continue
                data = json.loads(script.string)
                items = data if isinstance(data, list) else [data]
                
                for item in items:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        org = item.get("hiringOrganization", {})
                        comp = org.get("name") if isinstance(org, dict) else str(org)
                        
                        city = ""
                        loc = item.get("jobLocation", {})
                        if isinstance(loc, dict):
                            addr = loc.get("address", {})
                            if isinstance(addr, dict):
                                city = addr.get("addressRegion") or addr.get("addressLocality") or ""
                        
                        desc = item.get("description", "") + " " + resp.text
                        phone = extract_tr_phone(desc)
                        
                        if comp and len(comp.strip()) >= 2:
                            return {
                                "company_name": tr_upper(comp),
                                "city": self._extract_city(city or resp.text),
                                "direct_phone": phone
                            }
        except Exception:
            pass
        return None

    def _fallback_extract_company(self, title):
        clean_title = re.sub(r'\s*\|\s*(Kariyer\.net|LinkedIn|Eleman\.net|Indeed|Secretcv|İşinolsun).*$', '', title, flags=re.I)
        parts = [p.strip() for p in re.split(r'\s*[-–|•:]\s*', clean_title) if p.strip()]
        
        job_words = ["forklift", "reach truck", "reachtruck", "istif", "operatör", "şoför", "depo", "eleman", "aranıyor"]
        for p in parts:
            p_upper = tr_upper(p)
            if any(b in p_upper for b in BLACKLIST_COMPANIES) or p_upper in TURKISH_81_CITIES:
                continue
            if not any(jw in p.lower() for jw in job_words) and 2 <= len(p) <= 45:
                return p_upper
        return ""

    def scrape_all_sources(self):
        if not self.serpapi_key:
            print("[-] SERPAPI_KEY eksik!")
            return

        print("[+] Gerçek iş ilanları taranıyor...")
        queries = [
            '("forklift operatörü" OR "reach truck operatörü") site:kariyer.net inurl:is-ilani',
            '("forklift operatörü" OR "reach truck") site:eleman.net inurl:is-ilani',
            '("forklift operatörü") site:isinolsun.com inurl:is-ilani',
            '("forklift operatörü" OR "reach truck") site:secretcv.com inurl:ilan'
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
                res = requests.get("https://serpapi.com/search", params=params, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    for r in data.get("organic_results", []):
                        link = r.get("link", "")
                        raw_title = r.get("title", "")
                        snippet = r.get("snippet", "")
                        
                        # 1. Önce resmi web sayfasından JSON-LD ile çek
                        page_data = self._fetch_real_company_from_page(link)
                        
                        if page_data:
                            company = page_data["company_name"]
                            city = page_data["city"] or self._extract_city(raw_title + " " + snippet)
                            phone = page_data["direct_phone"] or extract_tr_phone(snippet)
                        else:
                            # 2. Sayfa engellerse başlık üzerinden ayıkla
                            company = self._fallback_extract_company(raw_title)
                            city = self._extract_city(raw_title + " " + snippet)
                            phone = extract_tr_phone(snippet)

                        # Filtreler: Kara liste ve geçersiz isimleri engelle
                        if not company or any(b in company for b in BLACKLIST_COMPANIES) or not city:
                            continue

                        # Kişi isimlerini (genelde 2 kelime ve unvansız olanlar) engelle
                        if len(company.split()) == 2 and not any(s in company for s in ["A.Ş", "LTD", "ŞTİ", "SAN", "TİC", "GROUP", "LOJİSTİK"]):
                            continue

                        sig = f"{company}_{city}"
                        if sig in self.seen_signatures:
                            continue

                        self.seen_signatures.add(sig)
                        self.raw_leads.append({
                            "company_name": company,
                            "city": city,
                            "direct_phone": phone,
                            "source_website": self._extract_source_website(link),
                            "job_url": link
                        })
            except Exception as e:
                print(f"[-] Arama hatası: {e}")

        print(f"[✓] Toplam {len(self.raw_leads)} adet onaylı kurumsal lead çıkarıldı.")

    def run_all(self):
        self.scrape_all_sources()
        return self.raw_leads
