import os
import re
from urllib.parse import urlparse
import requests
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

    def _is_invalid_page(self, url):
        url_lower = url.lower()
        bad_patterns = [
            r'/is-ilanlari(/|$|\?)',
            r'/q-.*-is-ilanlari',
            r'/pozisyonlar/',
            r'/jobs/search',
            r'/jobs/kategori',
            r'/arama',
            r'search\?',
            r'/tag/',
            r'/nedir',
            r'/maas',
            r'/cv/',
            r'/ozgecmis'
        ]
        return any(re.search(p, url_lower) for p in bad_patterns)

    def _extract_source_website(self, url):
        domain = urlparse(url).netloc.lower()
        domain = re.sub(r'^www\.', '', domain)
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

    def _extract_clean_company(self, raw_title, snippet, url):
        if self._is_invalid_page(url):
            return ""

        clean_title = raw_title
        clean_title = re.sub(r'\s*\|\s*(Kariyer\.net|LinkedIn|Eleman\.net|Indeed|Secretcv|İşinolsun|24saatteis).*$', '', clean_title, flags=re.I)
        clean_title = re.sub(r'\s*-\s*(Kariyer\.net|LinkedIn|Eleman\.net|Indeed|Secretcv|İşinolsun|24saatteis).*$', '', clean_title, flags=re.I)

        # LinkedIn: "Firma Adı hiring Forklift..."
        m_linkedin = re.search(r'^(.*?)\s+(?:hiring|is hiring)\s+(.*)$', clean_title, flags=re.I)
        if m_linkedin:
            return tr_upper(m_linkedin.group(1).strip())

        parts = [p.strip() for p in re.split(r'\s*[-–|•:]\s*', clean_title) if p.strip()]
        job_keywords = [
            "forklift", "reach truck", "reachtruck", "istif", "operatör", "operatörü", 
            "şoför", "şoförü", "sürücü", "depo", "eleman", "elemanı", "görevlisi", 
            "personel", "sevkiyat", "yükleme", "boşaltma", "lojistik", "paketleme",
            "makine operatörü", "iş ilanı", "iş ilanları", "aranıyor", "acil"
        ]

        candidate_parts = []
        for p in parts:
            p_clean = p.strip()
            p_upper = tr_upper(p_clean)

            if re.search(r'\d{1,2}\s+(OCAK|ŞUBAT|MART|NİSAN|MAYIS|HAZİRAN|TEMMUZ|AĞUSTOS|EYLÜL|EKİM|KASIM|ARALIK)', p_upper):
                continue
            if p_upper in ["GÜNCEL İŞ FIRSATLARI", "İŞ FIRSATLARI", "İŞ İLANI", "İŞ İLANLARI", "KADIN", "ERKEK", "ENGELLİ", "ACİL", "TAM ZAMANLI", "POTANSİYEL FİRMA"]:
                continue
            if p_upper in TURKISH_81_CITIES or p_upper in DISTRICT_MAP or p_upper in ["TÜRKİYE", "MARMARA"]:
                continue

            p_lower = p_clean.lower()
            job_word_count = sum(1 for jw in job_keywords if jw in p_lower)

            has_corp_suffix = any(s in p_upper for s in ["A.Ş", "AŞ", "LTD", "ŞTİ", "SANAYİ", "SAN.", "TİC.", "TİCARET", "HOLDİNG", "GROUP", "GRUP", "LOJİSTİK", "FABRİKA"])
            
            if has_corp_suffix:
                clean_p = p_clean
                for jw in ["Forklift Operatörü İş İlanı", "Forklift Operatörü", "Reach Truck Operatörü", "İş İlanı", "İş İlanları", "Forklift Şoförü"]:
                    clean_p = re.sub(re.escape(jw), '', clean_p, flags=re.I).strip(' -–:')
                if len(clean_p) >= 2:
                    candidate_parts.append((clean_p, 10))
            elif job_word_count == 0 and len(p_clean) >= 2 and len(p_clean.split()) <= 6:
                candidate_parts.append((p_clean, 5))

        if candidate_parts:
            candidate_parts.sort(key=lambda x: x[1], reverse=True)
            return tr_upper(candidate_parts[0][0])

        return ""

    def scrape_all_sources(self):
        if not self.serpapi_key:
            print("[-] SERPAPI_KEY bulunamadı!")
            return

        print("[+] İş ilanları taranıyor...")
        queries = [
            '("forklift operatörü" OR "reach truck operatörü") site:kariyer.net inurl:is-ilani -inurl:pozisyonlar',
            '("forklift operatörü" OR "reach truck") site:tr.linkedin.com inurl:"/jobs/view"',
            '("forklift operatörü" OR "forklift şoförü") site:eleman.net inurl:is-ilani',
            '("forklift operatörü" OR "reach truck") site:tr.indeed.com inurl:viewjob',
            '("forklift operatörü") site:isinolsun.com inurl:is-ilani'
        ]

        for q in queries:
            try:
                params = {
                    "engine": "google",
                    "q": q,
                    "hl": "tr",
                    "gl": "tr",
                    "num": "25",
                    "api_key": self.serpapi_key
                }
                res = requests.get("https://serpapi.com/search", params=params, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    for r in data.get("organic_results", []):
                        raw_title = r.get("title", "")
                        snippet = r.get("snippet", "")
                        link = r.get("link", "")

                        full_text = f"{raw_title} {snippet}"
                        company = self._extract_clean_company(raw_title, snippet, link)
                        city = self._extract_city(full_text)
                        phone = extract_tr_phone(full_text)
                        source_site = self._extract_source_website(link)

                        if not company or len(company) < 2 or not city:
                            continue

                        signature = f"{company.lower()}_{city.lower()}"
                        if signature in self.seen_signatures:
                            continue

                        self.seen_signatures.add(signature)
                        self.raw_leads.append({
                            "company_name": company,
                            "city": city,
                            "direct_phone": phone,
                            "source_website": source_site,
                            "job_url": link
                        })
            except Exception as e:
                print(f"[-] Arama sorgusu hatası: {e}")

        print(f"[✓] Temiz tekil ilan sayısı: {len(self.raw_leads)}")

    def run_all(self):
        self.scrape_all_sources()
        return self.raw_leads
