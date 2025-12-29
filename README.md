<div align="center">

# <span style="font-family: 'Courier New', Courier, monospace; font-weight: 900; font-size: 2.5em; letter-spacing: 8px; text-transform: uppercase; line-height: 1.1;">SGNL</span>
// SIGNAL EXTRACTION ENGINE

**STOP READING GARBAGE.**

[![Status](https://img.shields.io/badge/status-operational-brightgreen)]()
[![Version](https://img.shields.io/badge/version-2.0.0-blue)]()
[![License](https://img.shields.io/badge/license-Apache%202.0-orange)]()

*The internet is broken. We fix it.*

</div>

---

<div align="center">

**🌐 Language Selection / Dil Seçimi**

[🇬🇧 English](README.md) | [🇹🇷 Türkçe](README_TR.md)

</div>

---

## 🎯 The Manifesto: Anti-Slop

The modern internet is a landfill of SEO spam, affiliate farms, and AI-generated noise. Google has abdicated its role as a curator, favoring engagement over truth.

**SGNL exists to reclaim Signal.**

```python
core_principles = {
    "SIGNAL": "High-density information. Code benchmarks, peer-reviewed research, primary sources.",
    "NOISE": "Listicles, 'SEO-optimized' fluff, anecdotal marketing, 10-minute intros.",
    "METHOD": "We do not 'search'. We 'curate'. LLMs are strict editors, not creative writers."
}
```

---

## ⚡ System Overview

SGNL operates on a **Dual-Engine Architecture** designed to balance velocity with depth.

| Engine | Latency | Action | UX Pattern |
|--------|----------|--------|------------|
| **Fast Lane** | <1500ms | Retrieves raw Tavily search vectors | Optimistic UI — instant results table |
 | **Deep Scan** | Async (Background) | GPT-OSS-120B analyzes high-value artifacts (via Deepinfra/n8n) | Intelligence Report injected on verified signal |

### Architecture Flow

```
User Request → Fast Lane (Tavily) → Instant Results
                    ↓
               Deep Scan (GPT-OSS-120B via Deepinfra/n8n) → Signal Analysis → Intelligence Report
```

**Strategy:** The "Curator Prompt". We strictly forbid AI from lecturing. It scans for density and facts only.

**LLM Architecture:** Deep scan analysis is handled by n8n workflows using Deepinfra API with GPT-OSS-120B model for optimal performance and cost efficiency.

---

## 🎨 Design System: Swiss Brutalism

We reject smooth scrolling, excessive animations, and "delight". Tolerance for friction is zero.

### Color Palette

| Color | Hex Code | Usage |
|-------|----------|-------|
| ⬛ **Ink Black** | `#000000` | The void |
| ⬜ **Off White** | `#F4F1EA` | The paper |
| 🟧 **Safety Orange** | `#FF4500` | Alerts |
| 🟩 **Signal Green** | `#00FF00` | Verified truth |

### Typography

- **Headers:** Industrial Sans (Heavy weight)
- **Data:** Monospace/Terminal

---

## 🚀 Quick Start

### Prerequisites

- [x] Docker & Docker Compose
- [x] Valid `TAVILY_API_KEY` (for web search)
- [x] n8n instance with Deepinfra API configured (for LLM analysis)
- [ ] `OPENAI_API_KEY` (optional, for direct LLM calls)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/sgnl/engine.git
cd engine

# 2. Configure environment
cp .env.example .env
nano .env  # Add your API keys

# 3. Ignite
docker compose up -d --build
```

### Access

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/health |

---

## 🔒 Security

### Production Features

| Feature | Status | Description |
|---------|--------|-------------|
| ✅ No Hardcoded Credentials | Enabled | All secrets in environment variables |
| ✅ Restricted CORS | Enabled | Domain-specific access only |
| ✅ SSL/TLS Encryption | Enabled | Via Nginx Proxy Manager |
| ✅ Rate Limiting | Enabled | 20 req/min/IP (configurable) |
| ✅ Network Isolation | Enabled | Docker network security |

### Domain Configuration

```
Production: https://sgnl.metinkorkmaz.quest
n8n:       http://n8n.metinkorkmaz.quest (internal)
```

### Environment Setup

```bash
# Copy example file
cp .env.example .env

# Edit with your credentials
nano .env

# Configure n8n URLs (use domains, not IP addresses)
N8N_WEBHOOK_URL=http://n8n.metinkorkmaz.quest/webhook/sgnl/scan-topic
N8N_FAST_SEARCH_URL=http://n8n.metinkorkmaz.quest/webhook/fast-search

# Configure CORS origins
ALLOWED_ORIGINS=https://sgnl.metinkorkmaz.quest
```

📖 **Full deployment guide:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 📊 API Endpoints

### Health & Status

```bash
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "version": "2.0.0",
  "openai_configured": true
}
```

### Content Extraction

```bash
POST /extract
Content-Type: application/json

{
  "url": "https://example.com/article"
}
```

### Deep Scan (with LLM Analysis)

```bash
POST /deep-scan
Content-Type: application/json

{
  "url": "https://example.com/technical-article"
}
```

### Fast Search (Raw Results)

```bash
POST /fast-search
Content-Type: application/json

{
  "topic": "machine learning benchmarks",
  "max_results": 10
}
```

### Topic Scan (Full Analysis)

```bash
POST /scan-topic
Content-Type: application/json

{
  "topic": "rust vs go performance",
  "max_results": 10
}
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
 | `OPENAI_API_KEY` | ✅ Yes | - | OpenAI API key (optional, for direct LLM calls) |
| `TAVILY_API_KEY` | ✅ Yes | - | Tavily API key for web search |
| `N8N_WEBHOOK_URL` | ✅ Yes | - | n8n deep scan webhook URL |
| `N8N_FAST_SEARCH_URL` | ✅ Yes | - | n8n fast search webhook URL |
| `ALLOWED_ORIGINS` | ❌ No | `https://sgnl.metinkorkmaz.quest` | CORS allowed origins |
| `RATE_LIMIT` | ❌ No | 20 | Max requests per IP/minute |
| `RATE_WINDOW_SECONDS` | ❌ No | 60 | Rate limiting time window |
| `HOST` | ❌ No | 0.0.0.0 | API server host |
| `PORT` | ❌ No | 8000 | API server port |
| `LOG_LEVEL` | ❌ No | INFO | Logging verbosity |
| `DENSITY_THRESHOLD` | ❌ No | 0.45 | Content density threshold (0.0-1.0) |
| `LLM_MAX_CHARS` | ❌ No | 12000 | Max content length for LLM |

---

## 🛠️ Development

### Local Development

```bash
# Use development config
cp .env.dev .env
nano .env  # Add your dev API keys

# Start with port mapping
docker-compose -f docker-compose.dev.yml up --build

# Access at http://localhost:8000
```

### Running Tests

```bash
cd app
pytest tests/
```

### Project Structure

```
sgnl-backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── extractor.py         # Content extraction engine
│   ├── models.py           # Pydantic models
│   ├── services/
│   │   └── analyzer.py     # Heuristic content analysis
│   ├── static/             # CSS, JS assets
│   ├── templates/          # HTML templates
│   └── tests/             # Test suite
├── docs/                  # Documentation
│   ├── ARCHITECTURE.md     # System architecture
│   ├── DEPLOYMENT.md       # Deployment guide
│   └── DEPLOYMENT_CHECKLIST.md
├── docker-compose.yml      # Production config
├── docker-compose.dev.yml # Development config
└── .env.example           # Environment template
```

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Container won't start** | Check `docker-compose logs sgnl-api` and verify `.env` exists |
| **n8n connection failed** | Verify `N8N_WEBHOOK_URL` is set and n8n is running |
| **CORS errors** | Check `ALLOWED_ORIGINS` includes your domain |
| **Rate limiting too strict** | Increase `RATE_LIMIT` in `.env` |
| **SSL certificate issues** | See [docs/DEPLOYMENT.md#troubleshooting](docs/DEPLOYMENT.md#troubleshooting) |

### Debug Commands

```bash
# Check container logs
docker-compose logs -f sgnl-api

# Check container status
docker ps | grep sgnl-api

# Test health endpoint
curl http://localhost:8000/health

# Enter container shell
docker exec -it sgnl-api bash

# Check environment variables
docker exec sgnl-api env | grep -E "API_KEY|N8N"
```

---

## 📈 Performance

### Technical Constraints

| Metric | Value | Notes |
|--------|-------|-------|
| **Rate Limit** | 20 req/min/IP | Configurable via `RATE_LIMIT` |
| **Max Content Size** | 12,000 chars | Configurable via `LLM_MAX_CHARS` |
| **Density Threshold** | 0.45 | Configurable via `DENSITY_THRESHOLD` |
| **Fast Search Latency** | <1500ms | Raw Tavily results |
 | **Deep Scan Latency** | 2-5s | With GPT-OSS-120B analysis (via Deepinfra/n8n) |

### Enforcement

- **Rate Limiting:** Middleware intercepts abuse at edge. 429 codes trigger hard cooldown.
- **Privacy:** No user tracking. Logs are ephemeral.
- **Content Filtering:** Low-density content skipped automatically (CPIDR scoring).

---

## 📚 Documentation

- **[docs/](docs/)** - Complete documentation index
  - **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and design
  - **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Full deployment guide with Nginx Proxy Manager
  - **[DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md)** - Step-by-step deployment verification

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the Apache License 2.0.

---

## 🏷️ Status

```
Maintained by: Project SGNL Architects
Status:        OPERATIONAL
Version:       2.0.0
Last Updated:  December 29, 2025
```

---

<div align="center">

**Built with frustration. Deployed with hope.**

*If you're reading this, you're already part of the problem.*

</div>
