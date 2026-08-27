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

JUNK_WORDS = [
    "GÜNCEL İŞ FIRSATLARI", "İŞ FIRSATLARI", "İŞ İLANI", "İŞ İLANLARI", "KADIN", "ERKEK", 
    "ENGELLİ", "ACİL", "TAM ZAMANLI", "YARI ZAMANLI", "POTANSİYEL FİRMA", "ORTALAMA MAAŞ BİLGİLERİ", 
    "FORKLİFT OPERATÖRÜ", "REACH TRUCK OPERATÖRÜ", "DEPO ELEMANI", "ŞOFÖR", "SEO UZMANI", 
    "FORKLIFT", "OPERATÖR", "OPERATÖRÜ", "SÜRÜCÜ", "ELEMAN", "SECRET CV", "ELEMAN.NET", 
    "KARİYER.NET", "İŞİN OLSUN", "İNDEED", "LINKEDIN", "POZİSYONU", "NEDİR", "MAAŞLARI"
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

    def _clean_company_name(self, raw_title, snippet, url):
        url_lower = url.lower()

        # Kategori, maaş ve rehber sayfalarını tamamen filtrele
        if any(p in url_lower for p in ["/pozisyonlar/", "/nedir", "/maas", "/is-ilanlari/kategori", "/cv/", "/ozgecmis"]):
            return ""

        title_clean = re.sub(r'\s*\|\s*(Kariyer\.net|LinkedIn|Eleman\.net|Indeed|Secretcv|İşinolsun|24saatteis).*$', '', raw_title, flags=re.I)
        title_clean = re.sub(r'\s*-\s*(Kariyer\.net|LinkedIn|Eleman\.net|Indeed|Secretcv|İşinolsun|24saatteis).*$', '', title_clean, flags=re.I)

        # 1. LinkedIn
        m_linkedin = re.search(r'^(.*?)\s+(?:hiring|is hiring)\s+(.*)$', title_clean, flags=re.I)
        if m_linkedin:
            return tr_upper(m_linkedin.group(1).strip())

        # 2. Kariyer.net & Eleman.net & İşinolsun Başlık Formatları
        parts = [p.strip() for p in re.split(r'\s*[-–|•:]\s*', title_clean) if p.strip()]
        
        candidates = []
        for p in parts:
            p_upper = tr_upper(p)
            
            # Tarih, şehir veya çöp kelimeleri atla
            if re.search(r'\d{1,2}\s+(OCAK|ŞUBAT|MART|NİSAN|MAYIS|HAZİRAN|TEMMUZ|AĞUSTOS|EYLÜL|EKİM|KASIM|ARALIK)', p_upper):
                continue
            if p_upper in TURKISH_81_CITIES or p_upper in DISTRICT_MAP or p_upper in ["TÜRKİYE", "MARMARA"]:
                continue
            if any(jw == p_upper for jw in JUNK_WORDS):
                continue

            # Şirket takıları varsa en yüksek öncelik ver
            has_corp_suffix = any(s in p_upper for s in ["A.Ş", "AŞ", "LTD", "ŞTİ", "SANAYİ", "SAN.", "TİC.", "TİCARET", "HOLDİNG", "GROUP", "GRUP", "LOJİSTİK", "FABRİKA", "AMBALAJ", "GIDA", "KİMYA"])
            
            clean_part = p
            for kw in ["Forklift Operatörü", "Reach Truck", "İş İlanı", "İş İlanları", "Forklift Şoförü", "Aranıyor"]:
                clean_part = re.sub(re.escape(kw), '', clean_part, flags=re.I).strip(' -–:')
            
            clean_part_upper = tr_upper(clean_part)
            if len(clean_part_upper) >= 2 and not any(jw == clean_part_upper for jw in JUNK_WORDS):
                score = 10 if has_corp_suffix else 5
                candidates.append((clean_part_upper, score))

        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            chosen = candidates[0][0]
            # Sadece 2 kelimelik şahıs adlarını (unvansız) engelle
            if len(chosen.split()) == 2 and not any(s in chosen for s in ["A.Ş", "LTD", "ŞTİ", "SAN", "TİC", "GROUP", "LOJİSTİK"]):
                return ""
            return chosen

        return ""

    def scrape_all_sources(self):
        if not self.serpapi_key:
            print("[-] SERPAPI_KEY bulunamadı!")
            return

        print("[+] Tüm platformlar taranıyor (Kariyer.net, Eleman.net, İşinolsun, Indeed, LinkedIn)...")
        queries = [
            '("forklift operatörü" OR "reach truck operatörü") site:kariyer.net inurl:is-ilani',
            '("forklift operatörü" OR "forklift şoförü") site:eleman.net inurl:is-ilani',
            '("forklift operatörü") site:isinolsun.com inurl:is-ilani',
            '("forklift operatörü" OR "reach truck") site:tr.indeed.com inurl:viewjob',
            '("forklift operatörü" OR "reach truck") site:tr.linkedin.com inurl:"/jobs/view"',
            '("forklift operatörü") site:secretcv.com inurl:ilan'
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
                        raw_title = r.get("title", "")
                        snippet = r.get("snippet", "")
                        link = r.get("link", "")

                        full_text = f"{raw_title} {snippet}"
                        company = self._clean_company_name(raw_title, snippet, link)
                        city = self._extract_city(full_text)
                        phone = extract_tr_phone(snippet)
                        source_site = self._extract_source_website(link)

                        if not company or len(company) < 2 or not city:
                            continue

                        sig = f"{company}_{city}"
                        if sig in self.seen_signatures:
                            continue

                        self.seen_signatures.add(sig)
                        self.raw_leads.append({
                            "company_name": company,
                            "city": city,
                            "direct_phone": phone,
                            "source_website": source_site,
                            "job_url": link
                        })
            except Exception as e:
                print(f"[-] Arama sorgusu hatası: {e}")

        print(f"[✓] Bulunan toplam temiz tekil ilan sayısı: {len(self.raw_leads)}")

    def run_all(self):
        self.scrape_all_sources()
        return self.raw_leads
