<div align="center">

# <span style="font-family: 'Courier New', Courier, monospace; font-weight: 900; font-size: 2.5em; letter-spacing: 8px; text-transform: uppercase; line-height: 1.1;">SGNL</span>
// SİNYAL ÇIKARMA MOTORU

**ÇÖP OKUMAYI DURDURUN.**

[![Status](https://img.shields.io/badge/durum-operasyonel-brightgreen)]()
[![Version](https://img.shields.io/badge/version-2.0.0-blue)]()
[![License](https://img.shields.io/badge/license-Apache%202.0-orange)]()

*Bilgi filtreleme aracı.*

</div>

---

<div align="center">

**🌐 Dil Seçimi / Language Selection**

[🇬🇧 English](README.md) | [🇹🇷 Türkçe](README_TR.md)

</div>

---

## 🎯 Yaklaşım: Gürültü Filtreleme

İnternette çok içerik var. Bazıları faydalı. Bazıları değil.

**SGNL yardımcı olmak için var.**

```python
core_principles = {
    "SIGNAL": "Kod benchmarkları, hakemli araştırmalar, birincil kaynaklar.",
    "NOISE": "Listeler, aşırı girişler, genel içerik.",
    "METHOD": "Filtreleme ve analiz yapıyoruz. Mükemmel değil, ama umarım faydalı."
}
```

---

## ⚡ Sistem Genel Bakışı

SGNL, hız ve derinliği dengelemek için tasarlanmış bir **Çift Motor Mimarisi** üzerinde çalışır.

| Motor | Gecikme | Eylem | Kullanıcı Deneyimi |
|--------|----------|--------|------------------|
| **Hızlı Şerit** | <1500ms | Ham Tavily arama vektörlerini çıkarır | İyimser UI — anlık sonuç tablosu |
| **Derin Tarama** | Zaman Uzun (Arka Plan) | GPT-OSS-120B yüksek değerli eserleri analiz eder (Deepinfra/n8n aracılığıyla) | Doğrulanmış sinyalde İstihbarat Raporu enjekte edilir |

### Mimari Akış

```
Kullanıcı İsteği → Hızlı Şerit (Tavily) → Anlık Sonuçlar
                        ↓
                 Derin Tarama (GPT-OSS-120B Deepinfra/n8n ile) → Sinyal Analizi → İstihbarat Raporu
```

**Strateji:** "Küratör İstemi". Yapay zeka'ya öğretmesini yasaklıyoruz. Sadece yoğunluğu ve gerçekleri tarar.

**LLM Mimarisi:** Derin tarama analizi, n8n iş akışları tarafından Deepinfra API ve GPT-OSS-120B modeli kullanılarak optimum performans ve maliyet verimliliği için işlenir.

---

## 🎨 Tasarım Sistemi: İsviçre Brutalizmi

Pürüzsüz kaydırmayı, aşırı animasyonları ve "memnuniyeti" reddediyoruz. Sürtünmeye tolerans sıfır.

### Renk Paleti

| Renk | Hex Kodu | Kullanım |
|-------|-----------|---------|
| ⬛ **Mürekkep Siyah** | `#000000` | Boşluk |
| ⬜ **Kırık Beyaz** | `#F4F1EA` | Kağıt |
| 🟧 **Güvenlik Turuncusu** | `#FF4500` | Uyarılar |
| 🟩 **Sinyal Yeşili** | `#00FF00` | Doğrulanmış gerçek |

### Tipografi

- **Başlıklar:** Endüstriyel Sans (Ağır ağırlık)
- **Veri:** Monospace/Terminal

---

## 🚀 Hızlı Başlangıç

### Ön Koşullar

- [x] Docker & Docker Compose
- [x] Geçerli `TAVILY_API_KEY` (web araması için)
- [x] Deepinfra API ile yapılandırılmış n8n örneği (LLM analizi için)
- [ ] `OPENAI_API_KEY` (isteğe bağlı, doğrudan LLM çağrıları için)

### Kurulum

```bash
# 1. Depoyu klonlayın
git clone https://github.com/sgnl/engine.git
cd engine

# 2. Ortamı yapılandırın
cp .env.example .env
nano .env  # API anahtarlarınızı ekleyin

# 3. Başlatın
docker compose up -d --build
```

### Erişim

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
| ✅ Sabitlenmiş Kimlik Bilgisi Yok | Aktif | Tüm sırlar ortam değişkenlerinde |
| ✅ Kısıtlı CORS | Aktif | Sadece alan adına özel erişim |
| ✅ SSL/TLS Şifreleme | Aktif | Nginx Proxy Manager aracılığıyla |
| ✅ Hız Sınırlama | Aktif | 20 istek/dakika/IP (yapılandırılabilir) |
| ✅ Ağ İzolasyonu | Aktif | Docker ağ güvenliği |

### Alan Adı Yapılandırması

```
Üretim: https://sgnl.metinkorkmaz.quest
n8n:       http://n8n.metinkorkmaz.quest (dahili)
```

### Ortam Kurulumu

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

### İçerik Çıkarımı

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
  "topic": "makine öğrenmesi benchmarkları",
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
| `RATE_WINDOW_SECONDS` | ❌ Hayır | 60 | Hız sınırlama zaman penceresi |
| `HOST` | ❌ Hayır | 0.0.0.0 | API sunucusu ana bilgisayarı |
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
sgnl-backend/
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
| **Kapsayıcı başlamıyor** | `docker-compose logs sgnl-api` komutunu kontrol edin ve `.env` dosyasının var olduğunu doğrulayın |
| **n8n bağlantısı başarısız** | `N8N_WEBHOOK_URL` ayarlandığını ve n8n çalıştığını doğrulayın |
| **CORS hataları** | `ALLOWED_ORIGINS` alan adınızı içerdiğini kontrol edin |
| **Hız sınırlaması çok katı** | `.env` dosyasında `RATE_LIMIT` değerini artırın |
| **SSL sertifikası sorunları** | [docs/DEPLOYMENT.md#troubleshooting](docs/DEPLOYMENT.md#troubleshooting) konusuna bakın |

### Hata Ayıklama Komutları

```bash
# Kapsayıcı günlüklerini kontrol edin
docker-compose logs -f sgnl-api

# Kapsayıcı durumunu kontrol edin
docker ps | grep sgnl-api

# Sağlık uç noktasını test edin
curl http://localhost:8000/health

# Kapsayıcı kabuğuna girin
docker exec -it sgnl-api bash

# Ortam değişkenlerini kontrol edin
docker exec sgnl-api env | grep -E "API_KEY|N8N"
```

---

## 📈 Performans

### Teknik Kısıtlamalar

| Metrik | Değer | Notlar |
|--------|--------|--------|
| **Hız Sınırı** | 20 istek/dakika/IP | `RATE_LIMIT` üzerinden yapılandırılabilir |
| **Maksimum İçerik Boyutu** | 12,000 karakter | `LLM_MAX_CHARS` üzerinden yapılandırılabilir |
| **Yoğunluk Eşiği** | 0.45 | `DENSITY_THRESHOLD` üzerinden yapılandırılabilir |
| **Hızlı Arama Gecikmesi** | <1500ms | Ham Tavily sonuçları |
| **Derin Tarama Gecikmesi** | 2-5s | GPT-OSS-120B analizi ile (Deepinfra/n8n aracılığıyla) |

### Uygulama

- **Hız Sınırlama:** Orta katmanda kötüye kullanımı engeller. 429 kodları zorlu soğuma tetikler.
- **Gizlilik:** Kullanıcı izlemesi yok. Günlük kayıtları geçicidir.
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

## 🏷️ Durum

```
Bakım: Proje SGNL Mimarcıları
Durum:        OPERASYONEL
Sürüm:       2.0.0
Son Güncelleme: 29 Aralık 2025
```

---

<div align="center">

**Bilgi filtreleme aracı.**

*Daha iyi içerik bulmanıza yardımcı olmaya çalışıyoruz.*

</div>
