# AGENTS.md

## Commands

### Docker & Run
```bash
# Build and start production
docker compose up -d --build

# Build and start development (port mapping)
docker compose -f docker-compose.dev.yml up --build

# View logs
docker compose logs -f sgnl-api

# Enter container shell
docker exec -it sgnl-api bash
```

### Testing
```bash
# Run all tests
cd app
pytest tests/

# Run specific test file
pytest tests/test_analyzer.py

# Run specific test function
pytest tests/test_analyzer.py::TestHeuristicAnalyzer::test_init

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Dependencies
```bash
# Install dependencies
pip install -r app/requirements.txt

# Install spaCy model for ideadensity
python -m spacy download en_core_web_sm
```

### Linting
```bash
# Run linter
ruff check app/

# Format code
ruff format app/
```

Configuration is in `pyproject.toml` (lines 35-65).

## Project Structure

```
/app/
├── main.py                    # FastAPI entry point, middleware setup, route definitions
├── models.py                  # Pydantic request/response schemas (DeepScan*, Extraction*, ScanTopic*)
├── extractor.py                # Content extraction engine (ContentExtractor class, CPIDR density)
├── services/
│   ├── __init__.py
│   └── analyzer.py            # Heuristic analysis (HeuristicAnalyzer: code/data density, slop, affiliates)
├── analytics_middleware.py      # Analytics tracking middleware, session management
├── analytics_models.py          # SQLAlchemy models (VisitorLog, PageView, AnalyticsEvent)
├── analytics_utils.py          # Analytics helper functions (create_visitor, cleanup_old_visitors)
├── analytics_routes.py          # Analytics endpoints (/analytics/*)
├── static/
│   ├── css/main.css            # Brutalist design system (Swiss style)
│   └── js/                   # Frontend: main.js, analytics.js
├── templates/index.html         # Jinja2 template for landing page
└── tests/                    # Pytest test suite
    ├── conftest.py             # Shared fixtures (client, sample_html, mock_*)
    ├── test_analyzer.py         # HeuristicAnalyzer tests
    ├── test_extractor.py        # ContentExtractor tests
    ├── test_main.py            # FastAPI endpoint tests
    └── test_session.py         # Session/cookie tests
```

### Business Logic Locations
- **Content extraction**: `extractor.py` (ContentExtractor.extract_from_url, calculate_density)
- **Heuristic scoring**: `services/analyzer.py` (HeuristicAnalyzer.calculate_structure_score)
- **Density calculation**: Uses `ideadensity.cpidr()` library
- **Analytics**: `analytics_utils.py` (create_visitor, cleanup_old_visitors)

### Database Schemas
- SQLAlchemy declarative models in `analytics_models.py` (VisitorLog, PageView, AnalyticsEvent)
- Uses declarative_base pattern
- Connection via `get_db()` generator in analytics_middleware.py

### API Routes
- **Main entry point**: `main.py`
- **Core endpoints**: `/deep-scan`, `/fast-search`, `/scan-topic`, `/extract`, `/check-density`, `/analyze-results`, `/health`
- **Analytics routes**: `/analytics/*` via `analytics_routes.py`

## Code Style

### Import Patterns
```python
# Standard library imports first
import logging
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

# Third-party imports
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import httpx

# Local imports
from extractor import extractor
from services.analyzer import heuristic_analyzer
from models import DeepScanRequest, DeepScanResponse
```

### Logging Pattern
```python
logger = logging.getLogger(__name__)

logger.info("[PREFIX] Message here")
logger.warning("[PREFIX] Warning message")
logger.error("[PREFIX] Error: {error}")
```

Use prefixes in brackets: `[HEURISTIC]`, `[EXTRACTOR]`, `[ANALYTICS]`, `[FAST-SEARCH]`, etc.

### Async/Await
```python
# Always use async for I/O operations
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.get(url, follow_redirects=True)

# Async test endpoints use pytest-asyncio
@pytest.mark.asyncio
async def test_endpoint():
    response = await client.post("/endpoint")
```

### Error Handling
```python
try:
    # Operation
    result = some_function()
except HTTPException:
    raise  # Re-raise FastAPI errors
except Exception as e:
    logger.error(f"[PREFIX] Error: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))
```

### Pydantic Models (v2)
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum

class BiasRating(str, Enum):
    NEUTRAL = "Neutral"
    PROMOTIONAL = "Promotional"

class DeepScanRequest(BaseModel):
    url: str

class DeepScanResponse(BaseModel):
    url: str
    title: Optional[str] = None
    summary: Optional[str] = None
    technical_depth_score: int = Field(default=0, ge=0, le=100)
```

### Database Sessions (SQLAlchemy)
```python
from sqlalchemy.orm import Session

# Use generator pattern
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Usage in functions
def some_function():
    db: Session = next(get_db())
    try:
        result = db.query(Model).filter(...).first()
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
```

### Environment Variables
```python
from dotenv import load_dotenv
import os

load_dotenv()

# With defaults
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
RATE_LIMIT = int(os.getenv('RATE_LIMIT', '3'))
DENSITY_THRESHOLD = float(os.getenv('DENSITY_THRESHOLD', '0.45'))
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
```

### Singleton Pattern
```python
# Used for expensive-to-initialize objects
heuristic_analyzer = HeuristicAnalyzer()  # Defined once, imported elsewhere
extractor = ContentExtractor()
```

## Conventions

### Naming
- **Classes**: PascalCase (HeuristicAnalyzer, ContentExtractor)
- **Functions/variables**: snake_case (calculate_structure_score, base_score)
- **Constants**: UPPER_SNAKE_CASE (CODING_KEYWORDS, DENSITY_THRESHOLD)
- **Private methods**: Leading underscore (_analyze_code_density, _fetch_page)

### File Organization
- One class per file typically (analyzer.py → HeuristicAnalyzer, extractor.py → ContentExtractor)
- Related functionality grouped in services/ (analyzer.py)
- Analytics split: models, middleware, utils, routes

### Return Types
```python
from typing import Dict, Tuple, List, Optional

# Tuple with score and reason
def _analyze_code_density(self, soup: BeautifulSoup) -> Tuple[int, str]:
    return (score, reason)

# Dict with multiple fields
def extract_from_url(self, url: str, force_depth: bool = False) -> Dict[str, Any]:
    return {
        "url": url,
        "title": title,
        "content": content,
        "error": error
    }
```

### Test Organization
- Fixtures in `conftest.py` for reuse
- Test class per module (TestHeuristicAnalyzer, TestContentExtractor)
- Async tests use `pytest.mark.asyncio`
- Mock external dependencies (httpx, openai)

### Frontend
- Vanilla JavaScript in `static/js/main.js`, `static/js/analytics.js`
- GSAP for animations (Intelligence Report slide-down)
- Brutalist CSS in `static/css/main.css` (Swiss design system)
- Jinja2 templates in `templates/index.html`

## Safety

### Never
- Execute shell commands with user input without sanitization
- Use `sudo` without explicit permission
- Commit/push git changes without user instruction (AGENTS.md rule)
- Expose API keys or secrets in logs or responses
- Use `cat`, `head`, `tail`, `echo` on sensitive files (use Read tool instead)

### Environment Variables
- All secrets in `.env` (never in code)
- Use `os.getenv()` with sensible defaults
- Never commit `.env` files (in .gitignore)
- Reference template in `.env.example`

### Docker Security
- Run containers as non-root user (not implemented yet, add if needed)
- Use specific version tags in Dockerfile (`python:3.11-slim`)
- Mount only necessary volumes
- Network isolation via dedicated network

### API Security
- Rate limiting middleware (RateLimitMiddleware) on protected paths
- CORS restrictions via ALLOWED_ORIGINS
- No hardcoded credentials
- HTTP-only cookies with samesite=lax
- Input validation via Pydantic models

### File Operations
- Use Read tool for reading files (safer, line numbers)
- Use Bash only for operations not possible with Read (git, docker, etc.)
- Never use echo/printf on files with secrets

## Key Implementation Details

### CPIDR Density (Content Quality)
- Library: `ideadensity.cpidr(text)`
- Returns normalized 0.0-1.0 score
- Threshold: `DENSITY_THRESHOLD` (default 0.45)
- Low density (<0.45) skips LLM analysis to save tokens

### Heuristic Scoring (app/services/analyzer.py:65-140)
- Base score: 50
- Adjustments: code density (+0 to +20), data density (+0 to +15), slop (-30 to +10), affiliates (-30), hype (-20)
- Final: clamped to 0-100 range

### Rate Limiting
- IP-based, 3 requests per 60 seconds (configurable)
- Returns HTTP 429 with Retry-After header
- Protects: `/fast-search`, `/scan-topic`, `/deep-scan`

### LLM Integration
- Direct OpenAI API in `/deep-scan` (optional, requires OPENAI_API_KEY)
- n8n webhooks for production (GPT-OSS-120B via Deepinfra)
- Response format: JSON with `summary`, `key_findings`, `technical_depth_score`, `bias_rating`
- Max chars: `LLM_MAX_CHARS` (default 12000)

### Database (Analytics)
- PostgreSQL (configurable)
- Models: VisitorLog, PageView, AnalyticsEvent
- Session management via cookies (sgnl_session, 30 days)
- Cleanup: Deletes records >90 days
