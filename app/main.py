from fastapi import FastAPI, HTTPException, Header, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging
import os
import json
import time
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

from extractor import extractor
from services.analyzer import heuristic_analyzer
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

# OpenAI client (lazy init)
try:
    from openai import OpenAI
    openai_client = OpenAI()
except Exception:
    openai_client = None

# ========== RATE LIMITER ==========
class RateLimitMiddleware(BaseHTTPMiddleware):
    """IP-based rate limiting: N requests per minute for search endpoints."""

    RATE_LIMIT = int(os.getenv('RATE_LIMIT', '3'))
    WINDOW_SECONDS = int(os.getenv('RATE_WINDOW_SECONDS', '60'))
    PROTECTED_PATHS = ['/fast-search', '/scan-topic', '/deep-scan']
    
    def __init__(self, app):
        super().__init__(app)
        self.request_counts = defaultdict(list)  # IP -> list of timestamps
    
    def _clean_old_requests(self, ip: str):
        """Remove timestamps older than the window."""
        now = time.time()
        self.request_counts[ip] = [
            ts for ts in self.request_counts[ip] 
            if now - ts < self.WINDOW_SECONDS
        ]
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, handling proxies."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next):
        # Only rate limit protected paths
        if not any(request.url.path.startswith(p) for p in self.PROTECTED_PATHS):
            return await call_next(request)
        
        ip = self._get_client_ip(request)
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


app = FastAPI(title="SGNL Extraction Engine", version="2.0.0")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize analytics database
try:
    init_db()
    logger.info("[ANALYTICS] Analytics system initialized")
except Exception as e:
    logger.warning(f"[ANALYTICS] Failed to initialize: {e}")

# Add rate limiting middleware FIRST
app.add_middleware(RateLimitMiddleware)

# Add analytics middleware
app.add_middleware(AnalyticsMiddleware)

# Include analytics routes
app.include_router(analytics_router)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the directory where main.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# n8n webhook URLs
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')
N8N_FAST_SEARCH_URL = os.getenv('N8N_FAST_SEARCH_URL')

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


@app.get("/")
async def serve_frontend(request: Request):
    """Serve SGNL Heavy Brutalist landing page."""
    session_id = request.cookies.get("sgnl_session")
    
    if session_id:
        try:
            await create_visitor(request, session_id)
        except Exception as e:
            logger.warning(f"[ANALYTICS] Failed to create visitor: {e}")
    
    return templates.TemplateResponse("index.html", {"request": request})


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

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                N8N_FAST_SEARCH_URL,
                json={"topic": req.topic, "max_results": req.max_results},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"[FAST-SEARCH] Raw response: {type(result)}")
            
            # Handle n8n returning {results: [...]} or direct array
            if isinstance(result, dict) and "results" in result:
                results_array = result["results"]
            elif isinstance(result, list):
                results_array = result
            else:
                results_array = [result]
            
            logger.info(f"[FAST-SEARCH] Got {len(results_array)} results")
            return {"results": results_array}

    except httpx.TimeoutException:
        logger.error("[FAST-SEARCH] Request timed out")
        raise HTTPException(status_code=504, detail="Fast search timed out")
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
    if not N8N_WEBHOOK_URL:
        raise HTTPException(
            status_code=503,
            detail="n8n service not configured. Please set N8N_WEBHOOK_URL environment variable."
        )

    logger.info(f"[SCAN-TOPIC] Topic: {req.topic}, Max Results: {req.max_results}")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                N8N_WEBHOOK_URL,
                json={"topic": req.topic, "max_results": req.max_results},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"[SCAN-TOPIC] Got {len(result) if isinstance(result, list) else 1} results")
            return result

    except httpx.TimeoutException:
        logger.error("[SCAN-TOPIC] Request to n8n timed out")
        raise HTTPException(status_code=504, detail="Request to n8n workflow timed out")
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
    logger.info(f"[DEEP-SCAN] URL: {req.url}")
    
    # Step 1: Fetch and extract content
    try:
        extraction = await extractor.extract_from_url(req.url, force_depth=True)
        
        if extraction.get("length", 0) < 100:
            raise HTTPException(
                status_code=422, 
                detail=f"Insufficient content extracted: {extraction.get('error', 'Too short')}"
            )
        
        content = extraction["content"]
        title = extraction.get("title", "Untitled")
        density_score = extraction.get("density_score", 0.5)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DEEP-SCAN] Extraction failed: {e}")
        raise HTTPException(status_code=422, detail=f"Failed to extract content: {str(e)}")
    
    # Step 2: Density Gatekeeper - Skip LLM for low-signal content
    DENSITY_THRESHOLD = float(os.getenv('DENSITY_THRESHOLD', '0.45'))
    if density_score < DENSITY_THRESHOLD:
        logger.info(f"[DEEP-SCAN] Low density ({density_score:.3f} < {DENSITY_THRESHOLD}), skipping LLM")
        return DeepScanResponse(
            url=req.url,
            title=title,
            summary=f"Low Signal: Content filtered (density={density_score:.2f})",
            key_findings=["Content density below threshold (SKIPPED_LLM)", f"Density score: {density_score:.3f}"],
            technical_depth_score=0,
            bias_rating=BiasRating.NEUTRAL,
            heuristic_score=None,
            density_score=density_score,
            skipped_llm=True
        )
    
    # Step 3: Heuristic pre-scoring (fast, no LLM)
    try:
        # We need raw HTML for heuristics, fetch it
        async with httpx.AsyncClient(timeout=30.0) as client:
            html_response = await client.get(req.url, follow_redirects=True)
            raw_html = html_response.text
        
        heuristic_result = heuristic_analyzer.calculate_structure_score(
            raw_html, 
            title  # Use title as query context
        )
        heuristic_score = heuristic_result["score"]
        
    except Exception as e:
        logger.warning(f"[DEEP-SCAN] Heuristic analysis failed: {e}")
        heuristic_score = None
    
    # Step 4: LLM Analysis
    if openai_client is None:
        logger.warning("[DEEP-SCAN] OpenAI client not available, using fallback")
        # Fallback without LLM
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
        # Truncate content for token limits
        max_chars = int(os.getenv('LLM_MAX_CHARS', '12000'))
        truncated_content = content[:max_chars] if len(content) > max_chars else content
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": DEEP_SCAN_SYSTEM_PROMPT},
                {"role": "user", "content": f"Title: {title}\n\nContent:\n{truncated_content}"}
            ],
            response_format={"type": "json_object"},
            max_tokens=500,
            temperature=0.3
        )
        
        result_text = response.choices[0].message.content
        logger.info(f"[DEEP-SCAN] LLM response: {result_text[:200]}...")
        
        # Parse JSON response
        try:
            llm_result = json.loads(result_text)
        except json.JSONDecodeError as e:
            logger.error(f"[DEEP-SCAN] JSON parse error: {e}")
            raise HTTPException(status_code=500, detail="LLM returned invalid JSON")
        
        # Map bias rating
        bias_str = llm_result.get("bias_rating", "Neutral")
        try:
            bias_rating = BiasRating(bias_str)
        except ValueError:
            bias_rating = BiasRating.NEUTRAL
        
        return DeepScanResponse(
            url=req.url,
            title=title,
            summary=llm_result.get("summary", "No summary generated"),
            key_findings=llm_result.get("key_findings", []),
            technical_depth_score=llm_result.get("technical_depth_score", 50),
            bias_rating=bias_rating,
            heuristic_score=heuristic_score,
            density_score=density_score,
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
            source=result["source"],
            length=result["length"],
            signal_score=result["signal_score"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "2.0.0",
        "openai_configured": openai_client is not None
    }


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
        density_score = calculate_density(content) if content else 0.0
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

    DENSITY_THRESHOLD = float(os.getenv('DENSITY_THRESHOLD', '0.45'))
    analyzed = []
    
    for item in req.results:
        url = item.get("url", "")
        title = item.get("title", "Untitled")
        content = item.get("content", "")
        original_score = item.get("score", 0.5)
        
        # Fetch raw HTML for heuristic analysis
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, follow_redirects=True)
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
                density_score = calculate_density(extracted_text)
            else:
                density_score = calculate_density(content) if content else 0.0
            
        except Exception as e:
            logger.warning(f"[ANALYZE] Failed to fetch {url}: {e}")
            heuristic_score = 50  # Default
            heuristic_reason = "Could not analyze (fetch failed)"
            density_score = calculate_density(content) if content else 0.5
        
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
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    uvicorn.run(app, host=host, port=port)