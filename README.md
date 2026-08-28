# forklift-lead-hunter
# 🚜 Autonomous B2B Lead Generation & Data Enrichment Pipeline
### Yapay Zeka Destekli, Sıfır Dokunuşlu (Zero-Touch) Kurumsal Müşteri Adayı ve İstihbarat Otomasyonu

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Flash%203.1-4285F4?style=for-the-badge&logo=google&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![SerpApi](https://img.shields.io/badge/Data%20Mining-SerpApi-FF7043?style=for-the-badge)

---

## 📌 1. Projeye Genel Bakış ve Problem Tanımı

B2B iş geliştirme ve satış analitiği süreçlerinde, depolama ve malzeme taşıma ekipmanları (forklift, reach truck, istif makineleri) kiralama/satış operasyonları için en sıcak müşteri adayları **kendi bünyesine aktif olarak forklift operatörü veya depo personeli arayan kurumsal firmalardır**.

### Geleneksel Yöntemin Kısıtları (Manuel Operasyon):
* **Yüksek Zaman Maliyeti:** Haftalık olarak 6 farklı kariyer platformunu (Kariyer.net, LinkedIn, Eleman.net, Indeed, Secretcv, İşinolsun) taramak ve ayrıştırmak saatler alıyordu.
* **Veri Kirliliği:** Arama motorlarında iş ilanlarının yanı sıra iş arayanların özgeçmişleri (CV), SEO makaleleri, maaş rehberleri ve alakasız platform sayfaları listeleniyordu.
* **Eksik İletişim Verisi:** Çoğu ilanda şirketin doğrudan merkez santral/telefon bilgisi veya net lokasyonu yer almıyordu.
* **Mükerrerlik ve Takip Zorluğu:** Önceki haftalarda ulaşılan firmaların tekrar listeye girmesi zaman kaybına yol açıyordu.

### Geliştirilen Çözüm:
Bu proje; veri madenciliği, büyük dil modelleri (LLM), web zenginleştirme motorları, ilişkisel hafıza ve bulut tabanlı CI/CD iş akışlarını bir araya getirerek **insan müdahalesine ihtiyaç duymayan uçtan uca otonom bir pazar istihbarat boru hattı (pipeline)** kurar.

---

## 🏗️ 2. Sistem Mimarisi ve Veri Akışı
