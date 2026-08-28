# B2B Lead Hunter

# 🚜 B2B Lead Hunter: Otonom Pazar Analizi ve Lead Intelligence Pipeline

> **Yapay Zeka Destekli, Sunucusuz (Serverless) B2B Satış Geliştirme Otomasyonu**
> Hiring Intent (işe alım) verilerini satış fırsatlarına dönüştüren uçtan uca B2B Lead Pipeline sistemi.



![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Flash%203.1-4285F4?style=for-the-badge&logo=google&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![SerpApi](https://img.shields.io/badge/Data%20Mining-SerpApi-FF7043?style=for-the-badge)


---

## 🎯 1. Yönetici Özeti (TL;DR)

Bu proje; kendi bünyesinde lojistik, depolama veya üretim operasyonları yürüten ve endüstriyel istifleme makinelerine (forklift, reach truck vb.) aktif olarak ihtiyaç duyan potansiyel kurumsal müşterileri tespit etmek amacıyla geliştirilmiş uçtan uca otonom bir veri hattıdır (Data Pipeline). 

Sistem; kariyer platformlarındaki istihdam hareketlerini (Hiring Intent) tarayarak makine ihtiyacı doğan müşterileri bulur ve ham veriyi **Google Gemini LLM** ile analiz edip temizler. Eğer iş ilanında iletişim bilgisi veya adres verilmemişse; sistem şirket ismini algılayıp arka planda otonom bir Google Search başlatır ve firmanın genel merkez santral numarasını bularak tabloya ekler (Data Enrichment). Son olarak, aynı firmanın her hafta tekrar tekrar raporlara girmesini (duplike kayıtları) engellemek için 30 günlük hafızaya sahip bir veritabanı kullanır ve sadece yeni müşteri fırsatlarını satış ekibine haftalık olarak Excel formatında otomatik raporlar.

---

## ⚖️ 2. Problem ve Çözüm (Neden Geliştirildi?)

B2B satış ve iş geliştirme süreçlerinde bir şirketin "Forklift Operatörü" veya "Depo Elemanı" araması, o şirketin depo hacmini büyüttüğüne, yeni bir tesise geçtiğine veya mevcut makine filosunu genişlettiğine dair **en güçlü Intent Data (Satın Alma Verisi)** niteliğindedir.

| Geleneksel Süreç (Manuel Araştırma) | Otonom Sistem (B2B Lead Hunter) |
| :--- | :--- |
| **Zaman Kaybı:** 6 farklı platformu tek tek taramak haftalık 3-4 saatlik operasyonel yük yaratır. | **Hız (Zero-Touch):** Tüm süreç sıfır insan müdahalesiyle sadece 2 dakikada tamamlanır. |
| **Veri Kirliliği:** CV havuzları ve danışmanlık firmaları lead listesini kirletir. | **Temiz Veri (Qualified Leads):** Gemini LLM sayesinde çöp ilanlar %100 oranında elenir. |
| **Eksik İletişim:** İlanlarda şirket merkezinin telefonu genelde yazmaz. | **Arka Plan Araması (Enrichment):** İlanda numara yoksa, sistem internette firmayı kendi aratıp santral numarasını bulur. |
| **Tekrar Eden İş:** Aynı firmalar haftalarca listeye tekrar tekrar girebilir. | **Hafıza (Stateful DB):** 30 günlük akıllı SQLite veritabanı duplike kayıtları tamamen engeller. |

---

## 🔄 3. Sistem Mimarisi ve Veri Akışı

Sistem tamamen sunucusuz (serverless) bir yapıda, her Cuma günü Türkiye saati ile 09:00'da otonom olarak tetiklenir.

* **Adım 1: Veri Toplama (Multi-Platform Scraping)**
  * SerpApi kullanılarak Kariyer.net, Indeed, LinkedIn, Secretcv, Eleman.net ve Jooble platformları eşzamanlı taranır.
* **Adım 2: Anlamsal Filtreleme (AI Analysis & Parsing)**
  * Toplanan karmaşık veriler Gemini 2.5 Flash modeline iletilir. Model, gerçek kurumsal B2B firmaları tespit edip JSON formatında ayrıştırır.
* **Adım 3: İnternet Taraması ile Veri Zenginleştirme (Data Enrichment)**
  * İlan detayında telefonu veya lokasyonu eksik olan şirketler tespit edilir. Sistem, bu şirketler için Google Kurumsal İşletme Kartları (Business) üzerinden otomatik bir arka plan araması yaparak eksik numaraları ve illeri bulur.
* **Adım 4: Duplike Kontrolü (Rolling Memory Motoru)**
  * Şirket unvanları normalize edilir (A.Ş., Ltd. ekleri silinir). Satış ekibine aynı listenin gitmemesi için, son 30 gün içinde gönderilen firmalar tespit edilip yeni listeden çıkarılır.
* **Adım 5: Raporlama ve Dağıtım (Reporting & Distribution)**
  * Özel formatlanmış Excel tablosu oluşturulur ve ekibe güvenli SMTP bağlantısıyla iletilir.

---
### 4.1. `scraper.py` — Arama Motoru Veri Toplama Katmanı
* **Amaç:** Hedef anahtar kelimelerle (`forklift operatörü`, `istif makinesi operatörü`, `depo elemanı arayanlar`) 6 büyük platformu taramak.
* **Teknik Çözüm:** Doğrudan sitelerin HTML kodunu kazımak yerine (sürekli değişen DOM yapısı ve bot engelleri sebebiyle), Google Arama Operatörleri (`site:kariyer.net`, `site:tr.indeed.com` vb.) kullanılarak SerpApi üzerinden yapılandırılmış arama sonuçları çekilmiştir.

### 4.2. `ai_extractor.py` — Yapay Zeka Tabanlı Filtreleme Motoru
* **Amaç:** Ham arama sonuçlarındaki karmaşık başlıklardan gerçek işveren firmaları ayıklamak.
* **Teknik Çözüm:** Google Gemini Flash modeline katı bir sistem rolü (System Prompt) ve `JSON Schema` tanımlanmıştır. Model; "Anadolu Yakası Forklift İlanları", "Örnek CV'ler", "Danışmanlık Portalı" gibi ilan olmayan içerikleri eler; sadece B2B potansiyeli taşıyan gerçek ticari unvanları JSON formatında çıktı verir.

### 4.3. `enricher.py` — Otonom Veri Zenginleştirme
* **Amaç:** İlan metninde telefon numarası veya merkez şehri yazmayan şirketleri eksiksiz hale getirmek.
* **Teknik Çözüm:** Eksik verisi olan her şirket için ikincil bir alt arama tetiklenir. Google Kurumsal İşletme Kartları (Google Knowledge Graph) taranarak şirketin resmi müşteri hizmetleri/santral numarası ve genel merkez ili bulunarak tabloya eklenir.

### 4.4. `database.py` — 30 Günlük Döngüsel Hafıza ve Normalizasyon
* **Amaç:** Aynı şirketin her hafta tekrar tekrar raporlanmasını önlemek.
* **Teknik Çözüm:** 
  * Şirket unvanlarındaki kurumsal uzantılar (`A.Ş.`, `LTD. ŞTİ.`, `SAN. VE TİC.`) regex ile temizlenir (`normalize_company_name`).
  * SQLite üzerinde `leads` tablosunda `(company_name, date_added)` kaydı tutulur.
  * Son 30 gün içinde gönderilmiş olan firmalar filtrelenir.
  * 30 günü aşan eski kayıtlar otomatik temizlenerek (TTL mantığı) veritabanı boyutu optimum tutulur.

### 4.5. `mailer.py` — Kurumsal Raporlama ve Dağıtım
* **Amaç:** Toplanan temiz lead havuzunu satış ekiplerinin anında aksiyon alabileceği bir formata dönüştürmek.
* **Teknik Çözüm:** 
  * OpenPyXL ile 5 sütunlu (`FİRMA İSMİ`, `KONUM`, `İLETİŞİM BİLGİSİ`, `İLANIN ALINDIĞI WEBSİTESİ`, `İLAN LİNKİ`) Excel tablosu oluşturulur.
  * Başlıklar koyu kurumsal renkle biçimlendirilir, sütun genişlikleri içeriğe göre otomatik ayarlanır.
  * Hazırlanan dosya dinamik HTML özet metniyle birlikte `RECIPIENTS` listesindeki tüm yetkililere SMTP TLS şifrelemesiyle gönderilir.

### 4.6. `.github/workflows/weekly_leads.yml` — Sunucusuz CI/CD ve State Persistence
* **Amaç:** Sistemin harici bir sanal sunucu kiralamadan her Cuma sabahı kendiliğinden çalışması.
* **Teknik Çözüm:** 
  * `cron: '0 6 * * 5'` kuralı ile her Cuma Türkiye saatiyle 09:00'da (06:00 UTC) tetiklenir.
  * Ubuntu sanal makinesinde Python ortamı ayağa kaldırılır, kodlar çalıştırılır.
  * Çalışma bittiğinde güncellenen `data/leads_history.db` dosyası `github-actions[bot]` tarafından GitHub reposuna geri `commit` ve `push` edilir. Bu sayede sunucusuz mimaride dahi veritabanı hafızası korunur.

---

## 🛠️ 4. Kullanılan Teknolojiler 

| Teknoloji | Görevi ve Projedeki Rolü |
| :--- | :--- |
| **Python 3.11** | Tüm veri hattının omurgası ve orkestrasyonu. |
| **Google Gemini API** | Kural tabanlı filtrelerin (Regex) yetersiz kaldığı noktalarda anlamsal analiz ve ayrıştırma. |
| **SerpApi** | Kariyer sitelerinin bot korumalarına takılmadan Google indeksine doğrudan erişim. |
| **SQLite3** | Şirketlerin duplike (tekrar eden) şekilde raporlanmasını önleyen 30 günlük durum hafızası. |
| **OpenPyXL** | Sütun genişlikleri ayarlanmış, kurumsal temalı .xlsx formatlı çıktı üretimi. |
| **GitHub Actions** | Bulut CI/CD altyapısı ile sunucusuz (serverless) zamanlanmış görev (Cron Job) yürütme. |

---

## 📂 5. Proje Dizini

* **`.github/workflows/weekly_leads.yml`**: Otomasyonun bulut zamanlayıcı ve CI/CD konfigürasyonları.
* **`data/leads_history.db`**: Duplike gönderimleri engelleyen 30 günlük hafıza veritabanı.
* **`scraper.py`**: Arama motoru üzerinden ham ilanları çeken modül.
* **`ai_extractor.py`**: Gemini LLM ile B2B Lead niteliği taşımayan verileri eleyen motor.
* **`enricher.py`**: İlanlarda eksik olan telefon ve lokasyon bilgilerini Google üzerinden aratıp bulan "Enrichment" modülü.
* **`database.py`**: İsim normalizasyonu ve duplike firma kontrolünü yapan katman.
* **`mailer.py`**: Excel tablosunu oluşturup SMTP üzerinden e-posta dağıtımını gerçekleştiren modül.
* **`main.py`**: Tüm pipeline'ı sırasıyla çalıştıran ana şef.

---

## 🔒 6. Güvenlik Standartları (DevSecOps)

Sistem mimarisi kurumsal veri güvenliği standartlarına tam uyumlu olarak tasarlanmıştır:
* **Sıfır Açık Metin (Zero Hardcoding):** Kod tabanının hiçbir yerinde API anahtarları, şifreler veya e-posta adresleri bulunmaz.
* Tüm hassas veriler **GitHub Encrypted Secrets** kasasında şifreli olarak saklanır ve sadece çalışma anında sisteme (Environment Variables olarak) dahil edilir.

---

## 📈 7. İş Zekası Kazanımları (ROI & Business Value)

* ⏱️ **Operasyonel Verimlilik:** Manuel süreçte haftada 3-4 saat alan araştırma süresi **2 dakikaya** indirildi.
* 🎯 **%100 Doğrulanmış Lead (Qualified Leads):** AI destekli anlamsal ayrıştırma sayesinde satış ekibine giden veri havuzundaki gürültü tamamen yok edildi.
* 📞 **Satışa Hazır Pipeline (Sales-Ready Data):** Arka plan taramasıyla bulunan iletişim bilgileri sayesinde satış ekibinin tekrar numara aramadan doğrudan arama yapabileceği bir standart yakalandı.
* 💰 **Sıfır Maliyet:** Sunucu veya bulut makine kiralamak yerine GitHub Actions kullanılarak tamamen masrafsız, sürdürülebilir ve kalıcı bir altyapı kuruldu.
