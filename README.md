# forklift-lead-hunter
# 🚜 B2B Lead Hunter: Otonom Pazar Analizi ve Lead Intelligence Pipeline
> **Yapay Zeka Destekli, Sunucusuz (Serverless) B2B Satış Geliştirme Otomasyonu**
> Hiring Intent (işe alım) verilerini satış fırsatlarına dönüştüren uçtan uca B2B Lead Pipeline sistemi.


![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Flash%203.1-4285F4?style=for-the-badge&logo=google&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![SerpApi](https://img.shields.io/badge/Data%20Mining-SerpApi-FF7043?style=for-the-badge)

---

# 🚜 B2B Lead Hunter: Otonom Pazar Analizi ve Lead Intelligence Pipeline

> **Yapay Zeka Destekli, Sunucusuz (Serverless) B2B Satış Geliştirme Otomasyonu**
> Hiring Intent (işe alım niyeti) verilerini satış fırsatlarına dönüştüren uçtan uca B2B Lead Pipeline sistemi.

---

## 🎯 1. Yönetici Özeti (TL;DR)

Bu proje; kendi bünyesinde lojistik, depolama veya üretim operasyonları yürüten ve endüstriyel istifleme makinelerine (forklift, reach truck vb.) aktif olarak ihtiyaç duyan potansiyel kurumsal müşterileri tespit etmek amacıyla geliştirilmiş uçtan uca otonom bir veri hattıdır (Data Pipeline). 

Sistem; kariyer platformlarındaki istihdam hareketlerini (Hiring Intent) tarayarak makine ihtiyacı doğan müşterileri bulur, ham veriyi **Google Gemini LLM** ile analiz edip temizler, eksik merkez telefon ve lokasyon bilgilerini otonom olarak zenginleştirir (Data Enrichment). Ardından 30 günlük döngüsel veritabanı ile tekilleştirip, her hafta ilgili paydaşlara kurumsal Excel formatında otomatik raporlar.

---

## ⚖️ 2. Problem ve Çözüm (Neden Geliştirildi?)

B2B satış ve iş geliştirme süreçlerinde bir şirketin "Forklift Operatörü" veya "Depo Elemanı" araması, o şirketin depo hacmini büyüttüğüne, yeni bir tesise geçtiğine veya mevcut makine filosunu genişlettiğine dair **en güçlü Intent Data (Satın Alma Niyeti Verisi)** niteliğindedir.

| Geleneksel Süreç (Manuel Araştırma) | Otonom Sistem (B2B Lead Hunter) |
| :--- | :--- |
| **Zaman Kaybı:** 6 farklı platformu tek tek taramak haftalık 3-4 saatlik operasyonel yük yaratır. | **Hız (Zero-Touch):** Tüm süreç sıfır insan müdahalesiyle sadece 2 dakikada tamamlanır. |
| **Veri Kirliliği:** CV havuzları ve danışmanlık firmaları lead listesini kirletir. | **Temiz Veri (Qualified Leads):** Gemini LLM sayesinde çöp ilanlar %100 oranında elenir. |
| **Eksik İletişim:** İlanlarda şirket merkezinin telefonu genelde yazmaz. | **Zenginleştirme (Enrichment):** Google Knowledge Graph ile santral numaraları otonom olarak çekilir. |
| **Tekrar Eden İş:** Aynı firmalar haftalarca listeye tekrar tekrar girebilir. | **Hafıza (Stateful DB):** 30 günlük akıllı SQLite veritabanı mükerrer (duplicate) kayıtları engeller. |

---

## 🔄 3. Sistem Mimarisi ve Veri Akışı

Sistem tamamen sunucusuz (serverless) bir yapıda, her Cuma günü Türkiye saati ile 09:00'da otonom olarak tetiklenir.

* **Adım 1: Veri Toplama (Multi-Platform Scraping)**
  * SerpApi kullanılarak Kariyer.net, Indeed, LinkedIn, Secretcv, Eleman.net ve Jooble platformları eşzamanlı taranır.
* **Adım 2: Anlamsal Filtreleme (AI Analysis & Parsing)**
  * Toplanan karmaşık veriler Gemini 2.5 Flash modeline iletilir. Model, gerçek kurumsal B2B firmaları tespit edip JSON formatında ayrıştırır.
* **Adım 3: Veri Zenginleştirme (Data Enrichment Katmanı)**
  * Lokasyon veya santral numarası eksik olan şirketler için Google Kurumsal İşletme Kartları (Business) taranarak eksikler tamamlanır.
* **Adım 4: Tekilleştirme (Rolling Memory Motoru)**
  * Şirket unvanları normalize edilir (A.Ş., Ltd. ekleri silinir). Son 30 günde iletilen firmalar veritabanı kontrolüyle listeden çıkarılır.
* **Adım 5: Raporlama ve Dağıtım (Reporting & Distribution)**
  * Özel formatlanmış 5 sütunlu Excel tablosu oluşturulur ve paydaşlara güvenli SMTP bağlantısıyla iletilir.

---

## 🛠️ 4. Kullanılan Teknolojiler 

| Teknoloji | Görevi ve Projedeki Rolü |
| :--- | :--- |
| **Python 3.11** | Tüm veri hattının omurgası ve orkestrasyonu (Orchestrator). |
| **Google Gemini API** | Kural tabanlı filtrelerin (Regex) yetersiz kaldığı noktalarda anlamsal analiz ve ayrıştırma. |
| **SerpApi** | Kariyer sitelerinin bot korumalarına takılmadan Google indeksine doğrudan erişim. |
| **SQLite3** | Şirketlerin mükerrer raporlanmasını önleyen 30 günlük hafif durum hafızası (Time-to-Live Database). |
| **OpenPyXL** | Sütun genişlikleri ayarlanmış, kurumsal temalı .xlsx formatlı çıktı üretimi. |
| **GitHub Actions** | Bulut CI/CD altyapısı ile sunucusuz (serverless) zamanlanmış görev (Cron Job) yürütme. |

---

## 📂 5. Proje Dizini

* **`.github/workflows/weekly_leads.yml`**: Otomasyonun bulut zamanlayıcı ve CI/CD konfigürasyonları.
* **`data/leads_history.db`**: 30 günlük döngüsel hafıza veritabanı.
* **`scraper.py`**: Arama motoru üzerinden ham ilanları çeken modül.
* **`ai_extractor.py`**: Gemini LLM ile B2B Lead niteliği taşımayan verileri eleyen motor.
* **`enricher.py`**: Şirketlerin eksik telefon ve lokasyon bilgilerini Google üzerinden tamamlayan "Enrichment" modülü.
* **`database.py`**: İsim normalizasyonu ve mükerrer firma kontrolünü yapan katman.
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
* 📞 **Satışa Hazır Pipeline (Sales-Ready Data):** Zenginleştirilmiş iletişim bilgileri ile satış ekibinin pazar araştırması yapmadan doğrudan cold-call (soğuk arama) yapabileceği bir standart yakalandı.
* 💰 **Sıfır Maliyet:** Sunucu veya bulut makine kiralamak yerine GitHub Actions kullanılarak tamamen masrafsız ve sürdürülebilir bir altyapı kuruldu.
ulut makine kiralamak yerine GitHub Actions kullanılarak tamamen masrafsız ve sürdürülebilir bir altyapı kuruldu.
