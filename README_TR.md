<div align="center">

# <span style="font-family: 'Courier New', Courier, monospace; font-weight: 900; font-size: 2.5em; letter-spacing: 8px; text-transform: uppercase; line-height: 1.1;">SGNL</span>
// Sinyal Çıkarma Motoru

**ÇÖP OKUMAYI DURDURUN.**

[![Status](https://img.shields.io/website-up-down-green-red/https/sgnl.metinkorkmaz.quest.svg)](https://sgnl.metinkorkmaz.quest)
[![License](https://img.shields.io/badge/license-Apache%202.0-orange)](LICENSE)
[![Stars](https://img.shields.io/github/stars/metin-korkmaz/sgnl)](https://github.com/metin-korkmaz/sgnl/stargazers)
[![Last commit](https://img.shields.io/github/last-commit/metin-korkmaz/sgnl)](https://github.com/metin-korkmaz/sgnl/commits/main)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/downloads/release/python-311/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-available-blue)](https://www.docker.com/)

*Bilgi filtreleme aracı.*

</div>

---

<div align="center">

**🌐 Dil Seçimi / Language Selection**

[🇬🇧 English](README.md) | [🇹🇷 Türkçe](README_TR.md)

</div>

---

## 📖 Bu Nedir? (Kısa Özet)

**SGNL, internetteki yüksek kaliteli içeriği düşük kaliteli gürültüden ayıran akıllı bir filtreleme sistemidir.**

Bir araştırma asistanı gibi düşünün; makaleleri, akademik çalışmaları ve web içeriğini analiz eder ve size şunları söyler:
- Okunmaya değer olan içerikler (sinyal)
- Sadece reklam ve SEO spamı olan içerikler (gürültü)

**3 basit adımda nasıl çalışır:**
1. Bir konu başlığı girin
2. SGNL ilgili içerikleri bulur ve kalite/yoğunluk puanı verir
3. Sadece değerli içerikleri yapay zeka analiziyle birlikte alırsınız

**Kimler için ideal?** Araştırmacılar, geliştiriciler, öğrenciler veya internet'teki bilgi kirliliğinden rahatsız olan herkes.

---

## 🎯 Çalışma Prensibi: Gürültü Filtreleme

İnternette çok fazla içerik var. Bir kısmı değerli, büyük kısmı zaman kaybı.

**SGNL işte tam bu noktada yardımcı oluyor.**

```python
core_principles = {
    "SIGNAL": "Kod benchmark'ları, hakemli araştırmalar, birincil kaynaklar.",
    "NOISE": "Listicle'ler, tık tuzağı başlıkları, yüzeysel içerik.",
    "METHOD": "Filtreleme ve analiz yapıyoruz. Mükemmel değil, ama faydalı olmayı hedefliyoruz."
}
```

---

## ⚡ Sistem Mimarisi

SGNL, hız ve derinlik arasındaki dengeyi kurmak için tasarlanmış **Çift Motor Mimarisi** ile çalışır.

| Motor | Yanıt Süresi | İşlev | Kullanıcı Deneyimi |
|--------|--------------|--------|------------------|
| **Hızlı Tarama** | <1500ms | Tavily API ile anlık web araması | Sade UI — anlık sonuç listesi |
| **Derin Tarama** | Uzun (Arka Planda) | GPT-OSS-120B ile yüksek kaliteli içerik analiz ediliyor (Deepinfra/n8n üzerinden) | Doğrulanmış sinyal için İstihbarat Raporu ekleniyor |

### Mimari Akış

```
Kullanıcı İsteği → Hızlı Tarama (Tavily) → Anlık Sonuçlar
                        ↓
                  Derin Tarama (GPT-OSS-120B Deepinfra/n8n ile) → Sinyal Analizi → İstihbarat Raporu
```

**Strateji:** "Curator Model" - Yapay zeka'ya eğitim verisi sağlamayı tamamen engelliyoruz. Sadece içerik yoğunluğunu ve gerçekçiliğini tarıyoruz.

**LLM Mimarisi:** Derin tarama analizi, n8n workflow'ları üzerinden Deepinfra API'si ve GPT-OSS-120B modeli kullanılarak optimum performans ve maliyet verimliliğiyle işleniyor.

---

## 🎨 Tasarım Dili: İsviçre Brutalizmi

Pürüzsüz geçişleri, aşırı animasyonları ve "müşteri memnuniyeti" taklidini reddediyoruz. Sürtünmeye toleransımız sıfır.

### Renk Paleti

| Renk | Hex Kodu | Kullanım Alanı |
|-------|-----------|---------------|
| ⬛ **Mürekkep Siyah** | `#000000` | Boşluklar |
| ⬜ **Kırık Beyaz** | `#F4F1EA` | Kağıt dokusu |
| 🟧 **Uyarı Turuncusu** | `#FF4500` | Vurgular ve aksiyon butonları |
| 🟩 **Sinyal Yeşili** | `#00FF00` | Doğrulanmış gerçek içerik |

### Tipografi

- **Başlıklar:** Endüstriyel Sans-Serif (Ağır ağırlık, cesur)
- **Veri ve Kod:** Monospace/Terminal stili

---

## 🚀 Hızlı Başlangıç

### Önkoşullar

- [x] Docker & Docker Compose
- [x] Geçerli `TAVILY_API_KEY` (web araması için)
- [x] Deepinfra API ile yapılandırılmış n8n örneği (LLM analizi için)
- [ ] `OPENAI_API_KEY` (isteğe bağlı, doğrudan LLM çağrıları için)

### Kurulum Adımları

```bash
# 1. Depoyu klonlayın
git clone https://github.com/metin-korkmaz/sgnl.git
cd sgnl

# 2. Ortam değişkenlerini yapılandırın
cp .env.example .env
nano .env  # API anahtarlarınızı ekleyin

# 3. Sistemi başlatın
docker compose up -d --build
```

### Erişim Noktaları

| Hizmet | URL |
|---------|-----|
| **Ön Yüz** | http://localhost:8000 |
| **API Belgeleri** | http://localhost:8000/docs |
| **Sağlık Kontrolü** | http://localhost:8000/health |

---

## 🔒 Güvenlik

### Üretim Özellikleri

| Özellik | Durum | Açıklama |
|---------|--------|----------|
| ✅ Hardcoded Credential Yok | Aktif | Tüm API anahtarları ortam değişkenlerinde |
| ✅ Kısıtlı CORS | Aktif | Sadece belirli alan adlarına erişime izin veriliyor |
| ✅ SSL/TLS Şifreleme | Aktif | Nginx Proxy Manager üzerinden |
| ✅ Hız Sınırlama | Aktif | 3 istek/dakika/IP (yapılandırılabilir) |
| ✅ Ağ İzolasyonu | Aktif | Docker ağ güvenliği |

### Alan Adı Yapılandırması

```
Üretim: https://sgnl.metinkorkmaz.quest
n8n:       http://n8n.metinkorkmaz.quest (dahili ağ)
```

### Ortam Kurulumu Örneği

```bash
# Örnek dosyayı kopyalayın
cp .env.example .env

# Kimlik bilgilerinizle düzenleyin
nano .env

# n8n URL'lerini yapılandırın (IP adresi yerine alan adı kullanın)
N8N_WEBHOOK_URL=http://n8n.metinkorkmaz.quest/webhook/sgnl/scan-topic
N8N_FAST_SEARCH_URL=http://n8n.metinkorkmaz.quest/webhook/fast-search

# CORS kaynaklarını yapılandırın
ALLOWED_ORIGINS=https://sgnl.metinkorkmaz.quest
```

📖 **Tam dağıtım kılavuzu:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 📊 API Uç Noktaları

### Sağlık ve Durum

```bash
GET /health
```

**Yanıt:**
```json
{
  "status": "ok",
  "version": "2.0.0",
  "openai_configured": true
}
```

### İçerik Çıkarma

```bash
POST /extract
Content-Type: application/json

{
  "url": "https://example.com/article"
}
```

### Derin Tarama (LLM Analizi ile)

```bash
POST /deep-scan
Content-Type: application/json

{
  "url": "https://example.com/technical-article"
}
```

### Hızlı Arama (Ham Sonuçlar)

```bash
POST /fast-search
Content-Type: application/json

{
  "topic": "makine öğrenmesi benchmark'ları",
  "max_results": 10
}
```

### Konu Taraması (Tam Analiz)

```bash
POST /scan-topic
Content-Type: application/json

{
  "topic": "rust vs go performansı",
  "max_results": 10
}
```

---

## ⚙️ Yapılandırma

### Ortam Değişkenleri

| Değişken | Gerekli | Varsayılan | Açıklama |
|----------|----------|-----------|-----------|
| `OPENAI_API_KEY` | ❌ Hayır | - | Doğrudan LLM çağrıları için OpenAI API anahtarı (isteğe bağlı) |
| `TAVILY_API_KEY` | ✅ Evet | - | Web araması için Tavily API anahtarı |
| `N8N_WEBHOOK_URL` | ✅ Evet | - | n8n derin tarama webhook URL'si |
| `N8N_FAST_SEARCH_URL` | ✅ Evet | - | n8n hızlı arama webhook URL'si |
| `ALLOWED_ORIGINS` | ❌ Hayır | `https://sgnl.metinkorkmaz.quest` | CORS izin verilen kaynaklar |
| `RATE_LIMIT` | ❌ Hayır | 3 | IP başına maksimum istek/dakika |
| `RATE_WINDOW_SECONDS` | ❌ Hayır | 60 | Hız sınırlama zaman penceresi (saniye) |
| `HOST` | ❌ Hayır | 0.0.0.0 | API sunucusu bağlayacağı bilgisayar |
| `PORT` | ❌ Hayır | 8000 | API sunucusu portu |
| `LOG_LEVEL` | ❌ Hayır | INFO | Günlük kaydı ayrıntı seviyesi |
| `DENSITY_THRESHOLD` | ❌ Hayır | 0.45 | İçerik yoğunluk eşiği (0.0-1.0) |
| `LLM_MAX_CHARS` | ❌ Hayır | 12000 | LLM için maksimum içerik uzunluğu |

---

## 🛠️ Geliştirme

### Yerel Geliştirme

```bash
# Geliştirme yapılandırmasını kullanın
cp .env.dev .env
nano .env  # Geliştirme API anahtarlarınızı ekleyin

# Port eşlemesiyle başlatın
docker-compose -f docker-compose.dev.yml up --build

# http://localhost:8000 adresinden erişin
```

### Testleri Çalıştırma

```bash
cd app
pytest tests/
```

### Proje Yapısı

```
sgnl/
├── app/
│   ├── main.py              # FastAPI uygulaması
│   ├── extractor.py         # İçerik çıkarma motoru
│   ├── models.py           # Pydantic modelleri
│   ├── services/
│   │   └── analyzer.py     # Sezgisel içerik analizi
│   ├── static/             # CSS, JS varlıkları
│   ├── templates/          # HTML şablonları
│   └── tests/             # Test paketi
├── docs/                  # Belgelendirme
│   ├── ARCHITECTURE.md     # Sistem mimarisi
│   ├── DEPLOYMENT.md       # Dağıtım kılavuzu
│   └── DEPLOYMENT_CHECKLIST.md
├── docker-compose.yml      # Üretim yapılandırması
├── docker-compose.dev.yml # Geliştirme yapılandırması
└── .env.example           # Ortam şablonu
```

---

## 🔧 Sorun Giderme

### Yaygın Sorunlar

| Sorun | Çözüm |
|-------|--------|
| **Konteyner başlamıyor** | `docker-compose logs sgnl-api` komutunu çalıştırın ve `.env` dosyasının var olduğunu doğrulayın |
| **n8n bağlantısı başarısız** | `N8N_WEBHOOK_URL` ayarlandığını ve n8n'in çalıştığını doğrulayın |
| **CORS hataları** | `ALLOWED_ORIGINS` ayarının alan adınızı içerdiğini kontrol edin |
| **Hız sınırlaması çok katı** | `.env` dosyasında `RATE_LIMIT` değerini artırın |
| **SSL sertifikası sorunları** | [docs/DEPLOYMENT.md#troubleshooting](docs/DEPLOYMENT.md#troubleshooting) başlığına bakın |

### Hata Ayıklama Komutları

```bash
# Konteyner günlüklerini izleyin
docker-compose logs -f sgnl-api

# Konteyner durumunu kontrol edin
docker ps | grep sgnl-api

# Sağlık uç noktasını test edin
curl http://localhost:8000/health

# Konteyner kabuğuna girin
docker exec -it sgnl-api bash

# Ortam değişkenlerini kontrol edin
docker exec sgnl-api env | grep -E "API_KEY|N8N"
```

---

## 📈 Performans

### Teknik Kısıtlamalar

| Metrik | Değer | Notlar |
|--------|--------|--------|
| **Hız Sınırı** | 3 istek/dakika/IP (varsayılan) | `RATE_LIMIT` üzerinden yapılandırılabilir |
| **Maksimum İçerik Boyutu** | 12,000 karakter | `LLM_MAX_CHARS` üzerinden yapılandırılabilir |
| **Yoğunluk Eşiği** | 0.45 | `DENSITY_THRESHOLD` üzerinden yapılandırılabilir |
| **Hızlı Arama Gecikmesi** | <1500ms | Tavily API ham sonuçları |
| **Derin Tarama Gecikmesi** | 2-5s | GPT-OSS-120B analizi ile (Deepinfra/n8n üzerinden) |

### Uygulama Notları

- **Hız Sınırlama:** Kötüye kullanımı engeller. Orta seviyede 429 hatası zorluk tetikler.
- **Gizlilik:** Kullanıcı izleme yok. Günlük kayıtları geçicidir.
- **İçerik Filtreleme:** Düşük yoğunluklu içerikler otomatik olarak atlanır (CPIDR puanlaması).

---

## 📚 Belgelendirme

- **[docs/](docs/)** - Tam belgelendirme indeksi
  - **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Sistem mimarisi ve tasarım
  - **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Nginx Proxy Manager ile tam dağıtım kılavuzu
  - **[DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md)** - Adım adım dağıtım doğrulama

---

## 🤝 Katkıda Bulunma

1. Depoyu fork edin
2. Özellik dalınızı oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Baz harika özellik ekle'`)
4. Dala itin (`git push origin feature/amazing-feature`)
5. Pull Request açın

---

## 📄 Lisans

Bu proje Apache License 2.0 altında lisanslanmıştır.

---

## 👨‍💻 Bakım

**Metin Samet Korkmaz**

[![GitHub](https://img.shields.io/badge/GitHub-metin--korkmaz-blue)](https://github.com/metin-korkmaz)

---

## 🏷️ Durum

```
Durum:        OPERASYONEL (yukarıdaki rozeti görün)
Son Güncelleme: 29 Aralık 2025
```

---

<div align="center">

**Bilgi filtreleme aracı.**

*Daha iyi içerik bulmanıza yardımcı olmaya çalışıyoruz.*

</div>
