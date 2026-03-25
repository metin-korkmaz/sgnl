from fastapi import FastAPI, HTTPException, Header, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles as StarletteStaticFiles
from starlette.types import ASGIApp, Receive, Scope, Send
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging
import os
import json
import time
import secrets
import traceback
import uuid
from collections import defaultdict
from dotenv import load_dotenv
import ipaddress


class CachedStaticFiles(StarletteStaticFiles):
    """StaticFiles with cache headers for better performance."""

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            # Add cache headers for static assets
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    # Cache for 1 year for versioned static files
                    headers[b"cache-control"] = b"public, max-age=31536000, immutable"
                    message = {"type": "http.response.start", "status": message.get("status"), "headers": list(headers.items())}
                await send(message)

            await super().__call__(scope, receive, send_wrapper)
        else:
            await super().__call__(scope, receive, send)

load_dotenv()

from config import config
from extractor import extractor
from services.analyzer import heuristic_analyzer
from security.api_key import require_api_key
from security.url_validator import validate_url
from models import (
    DeepScanRequest,
    DeepScanResponse,
    BiasRating,
    ScanTopicRequest,
    ExtractionRequest,
    ExtractionResponse,
)

from analytics_middleware import AnalyticsMiddleware, init_db
from analytics_routes import router as analytics_router
from analytics_utils import create_visitor, cleanup_old_visitors
from cache import get_cache
from rate_limiter_interface import InMemoryRateLimiter

try:
    from rate_limiter import RedisRateLimiter
except ImportError:
    RedisRateLimiter = None

# OpenAI client (lazy initialization)
_openai_client = None
OPENAI_AVAILABLE = False


def get_openai_client():
    """Get or create OpenAI client (lazy initialization)."""
    global _openai_client, OPENAI_AVAILABLE
    if not OPENAI_AVAILABLE:
        try:
            from openai import AsyncOpenAI
            _openai_client = AsyncOpenAI()
            OPENAI_AVAILABLE = True
            logger.info("[OPENAI] Client initialized")
        except Exception as e:
            OPENAI_AVAILABLE = False
            logger.warning(f"[OPENAI] Failed to initialize: {e}")
            _openai_client = None
    return _openai_client if OPENAI_AVAILABLE else None

# ========== RATE LIMITER ==========
class RateLimitMiddleware(BaseHTTPMiddleware):
    """IP-based rate limiting: N requests per minute for search endpoints.

    Supports trusted proxy validation, IPv6 normalization, and authenticated bypass.
    Uses RedisRateLimiter if Redis is available, otherwise falls back to InMemoryRateLimiter.
    """

    # Protected paths: expensive operations requiring external API calls or CPU-intensive processing
    # /fast-search, /scan-topic, /deep-scan: n8n webhooks + LLM analysis
    # /extract: HTTP fetch + Trafilatura parsing
    # /analyze-results: HTTP fetch per result + heuristic scoring
    # /check-density: CPU-intensive NLP (spaCy, ideadensity)
    PROTECTED_PATHS = ['/fast-search', '/scan-topic', '/deep-scan', '/extract', '/analyze-results', '/check-density']

    def __init__(self, app):
        super().__init__(app)
        self._rate_limit = get_env('RATE_LIMIT', 3)
        self._window_seconds = get_env('RATE_WINDOW_SECONDS', 60)
        self.TRUSTED_PROXIES = config.TRUSTED_PROXIES_LIST
        self.AUTH_BYPASS = config.AUTH_BYPASS_RATE_LIMIT

        self._rate_limiter = self._init_rate_limiter()

        self._request_counts = defaultdict(list)

    def _init_rate_limiter(self):
        if RedisRateLimiter is None:
            logger.info("[RATE-LIMIT] Using InMemoryRateLimiter")
            return InMemoryRateLimiter(
                limit=self._rate_limit,
                window_seconds=self._window_seconds
            )

        try:
            cache = get_cache()
            if cache.is_redis_available() and cache._redis_cache:
                redis_client = cache._redis_cache._redis
                if redis_client:
                    logger.info("[RATE-LIMIT] Using RedisRateLimiter")
                    return RedisRateLimiter(
                        redis_client=redis_client,
                        limit=self._rate_limit,
                        window_seconds=self._window_seconds
                    )
        except Exception as e:
            logger.warning(f"[RATE-LIMIT] Redis initialization failed, falling back to in-memory: {e}")

        logger.info("[RATE-LIMIT] Using InMemoryRateLimiter")
        return InMemoryRateLimiter(
            limit=self._rate_limit,
            window_seconds=self._window_seconds
        )

    @property
    def request_counts(self):
        """Backward compatibility: access to request counts for tests."""
        if isinstance(self._rate_limiter, InMemoryRateLimiter):
            return self._rate_limiter._request_counts
        return self._request_counts

    @request_counts.setter
    def request_counts(self, value):
        """Backward compatibility: allow tests to set request counts."""
        if isinstance(self._rate_limiter, InMemoryRateLimiter):
            self._rate_limiter._request_counts = value
        else:
            self._request_counts = value

    @property
    def RATE_LIMIT(self):
        return self._rate_limit

    @RATE_LIMIT.setter
    def RATE_LIMIT(self, value):
        self._rate_limit = value
        if hasattr(self, '_rate_limiter') and self._rate_limiter:
            self._rate_limiter.limit = value

    @property
    def WINDOW_SECONDS(self):
        return self._window_seconds

    @WINDOW_SECONDS.setter
    def WINDOW_SECONDS(self, value):
        self._window_seconds = value
        if hasattr(self, '_rate_limiter') and self._rate_limiter:
            self._rate_limiter.window_seconds = value

    def _clean_old_requests(self, ip: str):
        """Backward compatibility: clean old requests for a specific IP."""
        # In the new implementation, this is handled by the rate limiter
        # For in-memory, delegate to the rate limiter's method
        if isinstance(self._rate_limiter, InMemoryRateLimiter):
            self._rate_limiter._clean_old_requests(ip)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, handling proxies."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _normalize_ip(self, ip: str) -> str:
        """Normalize IP address (handles IPv6 zone IDs and formats)."""
        if not ip or ip == "unknown":
            return "unknown"

        # Remove IPv6 zone ID (e.g., fe80::1%eth0 -> fe80::1)
        if '%' in ip:
            ip = ip.split('%')[0]

        try:
            # Parse and normalize the IP
            addr = ipaddress.ip_address(ip)
            # Return compressed IPv6 or standard IPv4
            return str(addr)
        except ValueError:
            # If parsing fails, return original (could be a hostname)
            return ip

    def _is_trusted_proxy(self, ip: str) -> bool:
        """Check if the connecting IP is in the trusted proxies list."""
        if not self.TRUSTED_PROXIES:
            return False

        normalized = self._normalize_ip(ip)
        return normalized in [self._normalize_ip(p) for p in self.TRUSTED_PROXIES]

    def _is_authenticated(self, request: Request) -> bool:
        """Check if request has valid authentication for rate limit bypass."""
        if not self.AUTH_BYPASS:
            return False

        # Check for API key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # In production, validate against stored API keys
            # For now, check if it matches a configured bypass key
            bypass_key = get_env('RATE_LIMIT_BYPASS_KEY')
            if bypass_key and api_key == bypass_key:
                return True

        # Check for bearer token (simplified check)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # In production, validate JWT or session token
            # For now, check if token format is valid (non-empty after Bearer)
            token = auth_header[7:].strip()
            if token and len(token) > 10:
                return True

        return False

    def _is_protected_path(self, path: str) -> bool:
        """Check if the path should be rate limited."""
        return any(path.startswith(p) for p in self.PROTECTED_PATHS)

    async def dispatch(self, request: Request, call_next):
        # Only rate limit protected paths
        if not self._is_protected_path(request.url.path):
            return await call_next(request)

        # Check for authentication bypass
        if self._is_authenticated(request):
            logger.debug("[RATE-LIMIT] Authenticated request bypassed rate limit")
            return await call_next(request)

        # Get client IP with trusted proxy validation and IPv6 normalization
        direct_ip = request.client.host if request.client else "unknown"
        normalized_direct = self._normalize_ip(direct_ip)

        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded and self._is_trusted_proxy(normalized_direct):
            client_ip = forwarded.split(",")[0].strip()
            ip = self._normalize_ip(client_ip)
        else:
            ip = normalized_direct

        # Check rate limit using the rate limiter
        is_allowed, metadata = await self._rate_limiter.is_allowed(ip)

        if not is_allowed:
            retry_after = metadata.get('reset_after', self.WINDOW_SECONDS)
            logger.warning(f"[RATE-LIMIT] IP {ip} exceeded limit. Retry after {retry_after}s")

            return Response(
                content=json.dumps({
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please wait before trying again.",
                    "retry_after": retry_after
                }),
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(retry_after)}
            )

        return await call_next(request)

        # Check for authentication bypass
        if self._is_authenticated(request):
            logger.debug(f"[RATE-LIMIT] Authenticated request bypassed rate limit")
            return await call_next(request)

        # Get client IP with trusted proxy validation and IPv6 normalization
        direct_ip = request.client.host if request.client else "unknown"
        normalized_direct = self._normalize_ip(direct_ip)

        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded and self._is_trusted_proxy(normalized_direct):
            client_ip = forwarded.split(",")[0].strip()
            ip = self._normalize_ip(client_ip)
        else:
            ip = normalized_direct

        self._clean_old_requests(ip)

        if len(self.request_counts[ip]) >= self.RATE_LIMIT:
            # Calculate retry time
            oldest_request = min(self.request_counts[ip])
            retry_after = int(self.WINDOW_SECONDS - (time.time() - oldest_request))

            logger.warning(f"[RATE-LIMIT] IP {ip} exceeded limit. Retry after {retry_after}s")

            return Response(
                content=json.dumps({
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please wait before trying again.",
                    "retry_after": retry_after
                }),
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(retry_after)}
            )

        # Record this request
        self.request_counts[ip].append(time.time())

        return await call_next(request)


# ========== REQUEST SIZE LIMIT ==========
class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size to prevent DoS via large payloads.

    Checks Content-Length header and returns 413 if payload exceeds limit.
    Configurable via MAX_BODY_SIZE_MB environment variable (default: 10MB).
    """

    def __init__(self, app):
        super().__init__(app)
        # Default: 10MB, configurable via env var
        max_mb = get_env('MAX_BODY_SIZE_MB', 10)
        self.MAX_BODY_SIZE = int(max_mb) * 1024 * 1024  # Convert MB to bytes
        logger.info(f"[SIZE-LIMIT] Max body size: {self.MAX_BODY_SIZE / 1024 / 1024}MB")

    async def dispatch(self, request: Request, call_next):
        # Check Content-Length header if present
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.MAX_BODY_SIZE:
                    logger.warning(f"[SIZE-LIMIT] Rejected request: {size} bytes exceeds limit of {self.MAX_BODY_SIZE} bytes")
                    return Response(
                        content=json.dumps({
                            "error": "PAYLOAD_TOO_LARGE",
                            "message": f"Request body too large. Max allowed: {self.MAX_BODY_SIZE / 1024 / 1024}MB"
                        }),
                        status_code=413,
                        media_type="application/json",
                        headers={"Retry-After": "0"}
                    )
            except ValueError:
                # Invalid Content-Length header, let it through to fail naturally
                pass

        return await call_next(request)


# ========== SECURITY HEADERS ==========
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject HTTP security headers on every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # X-Frame-Options: Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options: Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Strict-Transport-Security: Force HTTPS (HSTS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Referrer-Policy: Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy: Disable dangerous APIs
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content-Security-Policy: Restrict resource loading
        csp = (
            "default-src 'self'; "
            "script-src 'self' https://cdnjs.cloudflare.com; "
            "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response


# ========== ERROR HANDLING ==========
from fastapi.responses import JSONResponse

class SanitizedException(Exception):
    """Custom exception with sanitized message for client, full details logged server-side."""
    def __init__(self, message: str, status_code: int = 500, error_id: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.error_id = error_id or str(uuid.uuid4())[:8]
        super().__init__(message)


async def sanitized_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that sanitizes error messages.
    
    - Logs full error details server-side with error ID
    - Returns generic, safe message to client
    - Preserves HTTPException behavior (don't break existing handling)
    """
    # Generate unique error ID for tracking
    error_id = str(uuid.uuid4())[:8]
    
    # Get full traceback for logging
    tb_str = traceback.format_exc()
    
    # Log full details server-side
    logger.error(f"[ERROR] {error_id} - Unhandled exception: {str(exc)}")
    logger.error(f"[ERROR] {error_id} - Traceback:\n{tb_str}")
    
    # Return sanitized response to client
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "error_id": error_id
        }
    )


app = FastAPI(title="SGNL Extraction Engine", version="2.0.0")

# Register custom exception handler for unhandled exceptions
# Note: HTTPException is handled natively by FastAPI and will not be caught here
app.add_exception_handler(Exception, sanitized_exception_handler)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add GZip compression for all responses
app.add_middleware(GZipMiddleware, minimum_size=500)

# Initialize analytics database
try:
    init_db()
    logger.info("[ANALYTICS] Analytics system initialized")
except Exception as e:
    logger.warning(f"[ANALYTICS] Failed to initialize: {e}")

# Add rate limiting middleware FIRST
app.add_middleware(RateLimitMiddleware)

# Add request size limit middleware (early to catch large payloads)
app.add_middleware(RequestSizeLimitMiddleware)

# Add analytics middleware
app.add_middleware(AnalyticsMiddleware)

# Include analytics routes
app.include_router(analytics_router)

# Enable CORS for frontend
# Log warning if permissive CORS configuration is detected
if "*" in config.ALLOWED_ORIGINS_LIST:
    logger.warning("[CORS] WARNING: ALLOWED_ORIGINS contains '*'. This is insecure for production.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)

# Add security headers middleware (after CORS so headers are not overwritten)
app.add_middleware(SecurityHeadersMiddleware)

# Get the directory where main.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount static files (CSS, JS) with cache headers
app.mount("/static", CachedStaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# n8n webhook URLs
N8N_WEBHOOK_URL = config.N8N_WEBHOOK_URL
N8N_FAST_SEARCH_URL = config.N8N_FAST_SEARCH_URL

if not N8N_WEBHOOK_URL or not N8N_FAST_SEARCH_URL:
    logger.warning("[CONFIG] n8n webhook URLs not configured. LLM endpoints may not work.")

# LLM System Prompt
DEEP_SCAN_SYSTEM_PROMPT = """ROLE: You are SGNL, a ruthless technical editor. Analyze this text. Ignore marketing fluff.
OUTPUT JSON ONLY: { "summary": "One sentence thesis", "key_findings": ["Fact 1", "Fact 2"], "technical_depth_score": 0-100, "bias_rating": "Neutral|Promotional|Biased|Sponsored" }
Rules:
- summary: Single sentence capturing the core thesis
- key_findings: 2-5 concrete technical facts, no fluff
- technical_depth_score: 0=empty, 50=average, 80+=expert-level
- bias_rating: Neutral=objective, Promotional=sells product, Biased=one-sided, Sponsored=paid content"""


def get_env(key: str, default=None):
    """Get config value by key (backward compatibility).

    Uses the centralized config module. Maintains backward compatibility
    with code that was using the old _CACHED_ENV dictionary.
    """
    return getattr(config, key, default)


@app.get("/")
async def serve_frontend(request: Request):
    """Serve SGNL Heavy Brutalist landing page."""
    session_id = request.cookies.get("sgnl_session")

    # Create session if it doesn't exist
    if not session_id:
        session_id = f"sess_{int(time.time())}_{secrets.token_hex(8)}"

    response = templates.TemplateResponse(request, "index.html")

    # Set session cookie
    response.set_cookie(
        key="sgnl_session",
        value=session_id,
        max_age=30 * 24 * 60 * 60,  # 30 days
        httponly=True,
        samesite="lax",
        secure=True
    )

    # Add cache headers for HTML (short cache to allow updates)
    response.headers["Cache-Control"] = "public, max-age=300, s-maxage=600"

    # Create visitor record
    try:
        await create_visitor(request, session_id)
        logger.info(f"[ANALYTICS] Session created: {session_id}")
    except Exception as e:
        logger.warning(f"[ANALYTICS] Failed to create visitor: {e}")

    return response


@app.post("/fast-search")
async def fast_search(req: ScanTopicRequest):
    """
    Fast search endpoint - returns raw Tavily results in <2 seconds.
    Does NOT include LLM analysis. Use /scan-topic for full analysis.
    """
    if not N8N_FAST_SEARCH_URL:
        raise HTTPException(
            status_code=503,
            detail="n8n service not configured. Please set N8N_FAST_SEARCH_URL environment variable."
        )

    logger.info(f"[FAST-SEARCH] Topic: {req.topic}, Max Results: {req.max_results}")

    cache = get_cache()

    cached_result = cache.get("fast-search", req.topic, req.max_results)
    if cached_result is not None:
        logger.info(f"[FAST-SEARCH] Cache hit for topic: {req.topic}")
        return cached_result

    try:
        from extractor import get_http_client
        client = get_http_client()
        response = await client.post(
            N8N_FAST_SEARCH_URL,
            json={"topic": req.topic, "max_results": req.max_results},
            headers={"Content-Type": "application/json"},
            timeout=get_env('FAST_SEARCH_TIMEOUT_SECONDS', 30.0)
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"[FAST-SEARCH] Raw response: {type(result)}")

        if isinstance(result, dict) and "results" in result:
            results_array = result["results"]
        elif isinstance(result, list):
            results_array = result
        else:
            results_array = [result]

        logger.info(f"[FAST-SEARCH] Got {len(results_array)} results")

        response_data = {"results": results_array}

        cache_ttl = config.CACHE_TTL_FAST_SEARCH
        cache.set("fast-search", req.topic, req.max_results, response_data, ttl_seconds=cache_ttl)
        logger.info(f"[FAST-SEARCH] Cached result for {cache_ttl}s")

        return response_data

    except httpx.TimeoutException:
        logger.error("[FAST-SEARCH] Request timed out after 15 seconds")
        raise HTTPException(status_code=504, detail="Analysis timeout. Try a more specific topic for faster results.")
    except httpx.HTTPStatusError as e:
        logger.error(f"[FAST-SEARCH] Error: {e.response.status_code}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Search error: {e.response.text}")
    except Exception as e:
        logger.error(f"[FAST-SEARCH] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scan-topic")
async def scan_topic(req: ScanTopicRequest):
    """
    Scan a topic by forwarding request to n8n workflow.
    Returns the JSON response from n8n (includes LLM analysis).
    """
    request_start = time.time()
    logger.info(f"[SCAN-TOPIC] Topic: {req.topic}, Max Results: {req.max_results}")

    cache = get_cache()

    cache_check_start = time.time()
    cached_result = cache.get("scan-topic", req.topic, req.max_results)
    cache_check_duration = time.time() - cache_check_start

    if cached_result is not None:
        total_duration = time.time() - request_start
        logger.info(f"[SCAN-TOPIC] Cache hit for topic: {req.topic} | Cache check: {cache_check_duration:.3f}s | Total: {total_duration:.3f}s")
        return cached_result

    try:
        http_start = time.time()
        from extractor import get_http_client
        client = get_http_client()
        response = await client.post(
            N8N_WEBHOOK_URL,
            json={"topic": req.topic, "max_results": req.max_results},
            headers={"Content-Type": "application/json"},
            timeout=get_env('SCAN_TOPIC_TIMEOUT_SECONDS', 180.0)
        )
        response.raise_for_status()
        http_duration = time.time() - http_start

        parse_start = time.time()
        result = response.json()
        parse_duration = time.time() - parse_start

        cache_set_start = time.time()
        cache_ttl = config.CACHE_TTL_SCAN_TOPIC
        cache.set("scan-topic", req.topic, req.max_results, result, ttl_seconds=cache_ttl)
        cache_set_duration = time.time() - cache_set_start

        total_duration = time.time() - request_start
        logger.info(f"[SCAN-TOPIC] Got {len(result) if isinstance(result, list) else 1} results | "
                   f"Cache check: {cache_check_duration:.3f}s | HTTP: {http_duration:.3f}s | "
                   f"Parse: {parse_duration:.3f}s | Cache set: {cache_set_duration:.3f}s | "
                   f"Total: {total_duration:.3f}s")

        return result

    except httpx.TimeoutException:
        timeout_seconds = get_env('SCAN_TOPIC_TIMEOUT_SECONDS', 180.0)
        logger.error(f"[SCAN-TOPIC] Request to n8n timed out after {timeout_seconds} seconds")
        return {
            "summary": "Deep search took longer than expected, but the raw search results are still available.",
            "key_findings": [
                f"Deep analysis timed out after {timeout_seconds} seconds",
                "Top search results are still shown below",
                "Reduce max results or narrow the topic if you need a full synthesized report"
            ],
            "signal_score": 0,
            "verdict": "PARTIAL",
            "timed_out": True
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"[SCAN-TOPIC] n8n returned error: {e.response.status_code}")
        raise HTTPException(status_code=e.response.status_code, detail=f"n8n error: {e.response.text}")
    except Exception as e:
        logger.error(f"[SCAN-TOPIC] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/deep-scan", response_model=DeepScanResponse)
async def deep_scan(req: DeepScanRequest):
    """
    Deep scan a URL with LLM analysis.
    
    Workflow:
    1. Fetch & clean content with Trafilatura
    2. Check content density (CPIDR) - skip LLM if < 0.45
    3. Run heuristic pre-scoring
    4. LLM analysis with GPT-4o (if density passed)
    5. Return structured analysis
    """
    request_start = time.time()
    logger.info(f"[DEEP-SCAN] URL: {req.url}")
    
    extraction_start = time.time()
    try:
        extraction = await extractor.extract_from_url(req.url, force_depth=True)
        extraction_duration = time.time() - extraction_start
        
        if extraction.get("length", 0) < 100:
            raise HTTPException(
                status_code=422, 
                detail=f"Insufficient content extracted: {extraction.get('error', 'Too short')}"
            )
        
        content = extraction["content"]
        title = extraction.get("title", "Untitled")
        density_score = extraction.get("density_score", 0.5)
        depid_density = extraction.get("depid_density")
        readability_scores = extraction.get("readability_score", {})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DEEP-SCAN] Extraction failed: {e}")
        raise HTTPException(status_code=422, detail=f"Failed to extract content: {str(e)}")
    
    density_check_start = time.time()
    DENSITY_THRESHOLD = get_env('DENSITY_THRESHOLD', 0.45)
    if density_score < DENSITY_THRESHOLD:
        density_check_duration = time.time() - density_check_start
        total_duration = time.time() - request_start
        logger.info(f"[DEEP-SCAN] Low density ({density_score:.3f} < {DENSITY_THRESHOLD}) | "
                   f"Extraction: {extraction_duration:.3f}s | Density check: {density_check_duration:.3f}s | "
                   f"Total: {total_duration:.3f}s | Skipped LLM")
        return DeepScanResponse(
            url=req.url,
            title=title,
            summary=f"Low Signal: Content filtered (density={density_score:.2f})",
            key_findings=["Content density below threshold (SKIPPED_LLM)", f"Density score: {density_score:.3f}"],
            technical_depth_score=0,
            bias_rating=BiasRating.NEUTRAL,
            heuristic_score=None,
            density_score=density_score,
            depid_density=depid_density,
            readability_score=readability_scores,
            skipped_llm=True
        )
    
    heuristic_start = time.time()
    try:
        # Use raw_html from extraction result instead of re-fetching
        raw_html = extraction.get("raw_html", "")
        
        heuristic_result = heuristic_analyzer.calculate_structure_score(
            raw_html, 
            title
        )
        heuristic_score = heuristic_result["score"]
        heuristic_duration = time.time() - heuristic_start
        
    except Exception as e:
        logger.warning(f"[DEEP-SCAN] Heuristic analysis failed: {e}")
        heuristic_score = None
        heuristic_duration = time.time() - heuristic_start
    
    openai_client = get_openai_client()
    if openai_client is None:
        density_check_duration = time.time() - density_check_start
        total_duration = time.time() - request_start
        logger.warning(f"[DEEP-SCAN] OpenAI client not available | "
                      f"Extraction: {extraction_duration:.3f}s | Density check: {density_check_duration:.3f}s | "
                      f"Heuristic: {heuristic_duration:.3f}s | Total: {total_duration:.3f}s")
        return DeepScanResponse(
            url=req.url,
            title=title,
            summary=f"Content extracted from {title}",
            key_findings=["LLM analysis unavailable - OpenAI API key not configured"],
            technical_depth_score=heuristic_score or 50,
            bias_rating=BiasRating.NEUTRAL,
            heuristic_score=heuristic_score,
            density_score=density_score,
            skipped_llm=True
        )
    
    try:
        llm_start = time.time()
        max_chars = get_env('LLM_MAX_CHARS', 12000)
        truncated_content = content[:max_chars] if len(content) > max_chars else content
        
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": DEEP_SCAN_SYSTEM_PROMPT},
                {"role": "user", "content": f"Title: {title}\n\nContent:\n{truncated_content}"}
            ],
            response_format={"type": "json_object"},
            max_tokens=500,
            temperature=0.3
        )
        llm_duration = time.time() - llm_start
        
        result_text = response.choices[0].message.content
        logger.info(f"[DEEP-SCAN] LLM response: {result_text[:200]}...")
        
        parse_start = time.time()
        try:
            llm_result = json.loads(result_text)
        except json.JSONDecodeError as e:
            logger.error(f"[DEEP-SCAN] JSON parse error: {e}")
            raise HTTPException(status_code=500, detail="LLM returned invalid JSON")
        parse_duration = time.time() - parse_start
        
        bias_str = llm_result.get("bias_rating", "Neutral")
        try:
            bias_rating = BiasRating(bias_str)
        except ValueError:
            bias_rating = BiasRating.NEUTRAL
        
        density_check_duration = time.time() - density_check_start
        total_duration = time.time() - request_start
        logger.info(f"[DEEP-SCAN] Complete | Extraction: {extraction_duration:.3f}s | "
                   f"Density check: {density_check_duration:.3f}s | Heuristic: {heuristic_duration:.3f}s | "
                   f"LLM: {llm_duration:.3f}s | Parse: {parse_duration:.3f}s | Total: {total_duration:.3f}s")
        
        return DeepScanResponse(
            url=req.url,
            title=title,
            summary=llm_result.get("summary", "No summary generated"),
            key_findings=llm_result.get("key_findings", []),
            technical_depth_score=llm_result.get("technical_depth_score", 50),
            bias_rating=bias_rating,
            heuristic_score=heuristic_score,
            density_score=density_score,
            depid_density=depid_density,
            readability_score=readability_scores,
            skipped_llm=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DEEP-SCAN] LLM analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM analysis failed: {str(e)}")


@app.post("/extract", response_model=ExtractionResponse)
async def extract_content(req: ExtractionRequest, x_api_key: Optional[str] = Header(None)):
    """
    Extract content from a URL using Trafilatura.
    Headers: x-api-key (optional for now)
    """
    logger.info(f"[EXTRACT] URL: {req.url}, Force Depth: {req.force_depth}")

    try:
        result = await extractor.extract_from_url(req.url, req.force_depth)
        
        if "error" in result and result.get("length", 0) == 0:
            logger.warning(f"[EXTRACT] Extraction failed: {result.get('error')}")
            raise HTTPException(status_code=422, detail=f"Extraction failed: {result.get('error')}")

        return ExtractionResponse(
            url=result["url"],
            title=result["title"],
            content=result["content"],
            author=result.get("author"),
            date=result.get("date"),
            word_count=len(result.get("content", "").split()),
            extraction_method="trafilatura",
            density_score=result.get("density_score"),
            depid_density=result.get("depid_density"),
            readability_score=result.get("readability_score")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    cache = get_cache()
    stats = cache.get_stats()

    # Get Redis-specific status
    redis_status = {
        "available": stats.get("redis_available", False),
    }

    # Mask credentials in Redis URL for security
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    if '@' in redis_url:
        # Extract host:port/db from URL with auth
        redis_display = redis_url.split('@')[-1].replace('redis://', '')
    else:
        redis_display = redis_url.replace('redis://', '')
    redis_status["url"] = redis_display

    return {
        "status": "ok",
        "version": "2.0.0",
        "openai_configured": get_openai_client() is not None,
        "cache": stats,
        "redis": redis_status
    }


@app.get("/cache/stats")
async def cache_stats(api_key: str = Depends(require_api_key)):
    cache = get_cache()
    return cache.get_stats()


@app.post("/cache/clear")
async def cache_clear(api_key: str = Depends(require_api_key)):
    cache = get_cache()
    cache.clear()
    return {"status": "ok", "message": "Cache cleared"}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    # Close shared HTTP client
    from extractor import close_http_client
    await close_http_client()
    logger.info("[SHUTDOWN] Resources cleaned up")


# ============ n8n Integration Endpoints ============

class CheckDensityRequest(BaseModel):
    """Request to check content density for filtering."""
    results: List[dict]  # List of {url, title, content, ...}
    threshold: float = 0.45  # Density threshold for skipping LLM


@app.post("/check-density")
async def check_density(req: CheckDensityRequest):
    """
    Fast density check for n8n integration.
    
    Use this BEFORE your LLM node to filter low-quality content.
    Returns results with density_score and skipped_llm flag.
    
    Example n8n config:
    - URL: http://your-host:8000/check-density
    - Method: POST
    - Body: {"results": {{$json.results}}, "threshold": 0.45}
    """
    from extractor import calculate_density
    
    logger.info(f"[CHECK-DENSITY] Checking {len(req.results)} items, threshold={req.threshold}")
    
    enriched = []
    skipped_count = 0
    
    for item in req.results:
        content = item.get("content", "")
        
        # Calculate density
        density_score = await calculate_density(content) if content else 0.0
        skipped_llm = density_score < req.threshold
        
        if skipped_llm:
            skipped_count += 1
            logger.info(f"[CHECK-DENSITY] SKIP: {item.get('url', 'unknown')[:50]}... density={density_score:.3f}")
        
        # Return original item with density info added
        enriched_item = {
            **item,
            "density_score": round(density_score, 3),
            "skipped_llm": skipped_llm
        }
        enriched.append(enriched_item)
    
    logger.info(f"[CHECK-DENSITY] Done: {len(enriched)} items, {skipped_count} will skip LLM")
    
    return {
        "results": enriched,
        "count": len(enriched),
        "skipped_count": skipped_count,
        "threshold": req.threshold
    }


class AnalyzeResultsRequest(BaseModel):
    """Request from n8n with search results to analyze."""
    results: List[dict]  # List of {url, title, content, score}
    query: str  # Original search query


class AnalyzedResult(BaseModel):
    """Single analyzed result."""
    url: str
    title: str
    content: str
    original_score: float
    heuristic_score: int
    heuristic_reason: str
    final_score: float  # Combined score


@app.post("/analyze-results")
async def analyze_results(req: AnalyzeResultsRequest):
    """
    Analyze search results with heuristic and density scoring.
    Called by n8n after Tavily search, before LLM node.
    
    Flow: n8n → Tavily Search → This Endpoint → n8n LLM Node
    
    Returns enriched results with heuristic and density scores.
    Low-density items are flagged for LLM skip.
    """
    from extractor import calculate_density
    import trafilatura
    
    logger.info(f"[ANALYZE] Query: {req.query}, Results: {len(req.results)}")

    DENSITY_THRESHOLD = get_env('DENSITY_THRESHOLD', 0.45)
    analyzed = []
    
    for item in req.results:
        url = item.get("url", "")
        title = item.get("title", "Untitled")
        content = item.get("content", "")
        original_score = item.get("score", 0.5)
        
        # Fetch raw HTML for heuristic analysis
        try:
            # Validate URL for SSRF protection before fetching
            is_valid, error_message = validate_url(url)
            if not is_valid:
                logger.warning(f"[ANALYZE] URL validation failed for {url}: {error_message}")
                raise Exception(f"URL validation failed: {error_message}")
            
            from extractor import get_http_client
            client = get_http_client()
            response = await client.get(url)
            raw_html = response.text
            
            # Calculate heuristic score
            heuristic = heuristic_analyzer.calculate_structure_score(
                raw_html,
                req.query
            )
            heuristic_score = heuristic["score"]
            heuristic_reason = heuristic["reason"]
            
            # Extract clean text and calculate density
            extracted_text = trafilatura.extract(raw_html, include_comments=False, include_tables=True)
            if extracted_text:
                density_score = await calculate_density(extracted_text)
            else:
                density_score = await calculate_density(content) if content else 0.0
            
        except Exception as e:
            logger.warning(f"[ANALYZE] Failed to fetch {url}: {e}")
            heuristic_score = 50  # Default
            heuristic_reason = "Could not analyze (fetch failed)"
            density_score = await calculate_density(content) if content else 0.5
        
        # Determine if LLM should be skipped
        skipped_llm = density_score < DENSITY_THRESHOLD
        if skipped_llm:
            logger.info(f"[ANALYZE] Low density for {url}: {density_score:.3f}")
        
        # Combine scores: 60% heuristic, 40% original
        final_score = (heuristic_score * 0.6 + original_score * 100 * 0.4) / 100
        
        analyzed.append({
            "url": url,
            "title": title,
            "content": content,
            "original_score": original_score,
            "heuristic_score": heuristic_score,
            "heuristic_reason": heuristic_reason,
            "density_score": round(density_score, 3),
            "skipped_llm": skipped_llm,
            "final_score": round(final_score, 3)
        })
    
    # Sort by final_score descending
    analyzed.sort(key=lambda x: x["final_score"], reverse=True)
    
    skipped_count = sum(1 for a in analyzed if a["skipped_llm"])
    logger.info(f"[ANALYZE] Completed: {len(analyzed)} results, {skipped_count} skipped LLM (low density)")
    
    return {
        "query": req.query,
        "results": analyzed,
        "count": len(analyzed),
        "skipped_llm_count": skipped_count
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)
