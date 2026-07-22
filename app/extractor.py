"""
SGNL Content Extractor
Uses Trafilatura for high-quality content extraction from web pages.
Includes CPIDR-based density scoring via ideadensity.
"""

import trafilatura
from trafilatura.settings import use_config
import httpx
from typing import Optional, Dict, Any, Tuple
import logging
import re
from urllib.parse import urlparse
import time
import asyncio
import hashlib

from config import config
from security.url_validator import validate_url
from cache import get_cache

# ideadensity for content density scoring (CPIDR and DEPID metrics)
try:
    from ideadensity import cpidr, depid
    IDEADENSITY_AVAILABLE = True
except ImportError:
    IDEADENSITY_AVAILABLE = False
    cpidr = None
    depid = None

# textstat for readability metrics
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False
    textstat = None

logger = logging.getLogger(__name__)

# Configure Trafilatura for better extraction
TRAFILATURA_CONFIG = use_config()
TRAFILATURA_CONFIG.set("DEFAULT", "EXTRACTION_TIMEOUT", "15")

# Shared HTTP client with connection pooling for better performance
_http_client = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create a shared HTTP client with connection pooling."""
    global _http_client
    if _http_client is None:
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=50,
            keepalive_expiry=30.0
        )
        timeout = httpx.Timeout(15.0, connect=10.0)
        _http_client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
        )
    return _http_client


async def close_http_client():
    """Close the shared HTTP client (call on shutdown)."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
        logger.info("[HTTP] Shared client closed")


async def calculate_density(text: str) -> float:
    """
    Calculate content density using CPIDR (Content Propositional Idea Density Ratio).
    Results are cached by content hash to avoid redundant calculations.

    Args:
        text: The text content to analyze

    Returns:
        Density score from 0.0 to 1.0 where:
        - < 0.45 = Low density ("slop", thin content)
        - 0.45-0.65 = Medium density (average content)
        - > 0.65 = High density (information-rich content)
    """
    if not text or len(text.strip()) < 50:
        return 0.0

    if not IDEADENSITY_AVAILABLE:
        logger.warning("[DENSITY] ideadensity library not available, returning default 0.5")
        return 0.5

    # Generate SHA-256 hash of content for cache key
    content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    cache_key_prefix = "cpidr"

    # Check cache first
    try:
        cache = get_cache()
        cached_result = cache.get(cache_key_prefix, content_hash, 0)
        if cached_result is not None:
            logger.debug(f"[DENSITY] Cache hit for CPIDR: {content_hash[:16]}...")
            return float(cached_result)
        logger.debug(f"[DENSITY] Cache miss for CPIDR: {content_hash[:16]}...")
    except Exception as e:
        logger.warning(f"[DENSITY] Cache lookup failed: {e}")

    try:
        # CPIDR returns either a float (density) or a tuple
        # (proposition_count, word_count, density, error)
        # Offload to thread pool to avoid blocking event loop
        density_result = await asyncio.to_thread(cpidr, text)
        # Extract density float from result (handle both tuple and float returns)
        if isinstance(density_result, (tuple, list)):
            density = density_result[2]
        else:
            density = density_result
        # Normalize to 0.0-1.0 range (CPIDR typically ranges 0-1 but can vary)
        normalized = max(0.0, min(1.0, float(density)))

        # Cache the result with 1 hour TTL
        try:
            cache = get_cache()
            cache.set(cache_key_prefix, content_hash, 0, normalized, 3600)
            logger.debug(f"[DENSITY] Cached CPIDR result: {content_hash[:16]}... = {normalized}")
        except Exception as e:
            logger.warning(f"[DENSITY] Cache store failed: {e}")

        logger.debug(f"[DENSITY] Raw={density}, Normalized={normalized}")
        return normalized
    except Exception as e:
        logger.warning(f"[DENSITY] Calculation failed: {e}, returning default 0.5")
        return 0.5


async def calculate_depid_density(text: str) -> Optional[float]:
    """
    Calculate DEPID (Dependency-based Propositional Idea Density).
    Results are cached by content hash to avoid redundant calculations.

    Args:
        text: The text content to analyze

    Returns:
        Density score from 0.0 to 1.0 or None if unavailable
    """
    if not text or len(text.strip()) < 50:
        return None

    if not IDEADENSITY_AVAILABLE or depid is None:
        logger.debug("[DEPID] ideadensity library not available")
        return None

    # Generate SHA-256 hash of content for cache key
    content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    cache_key_prefix = "depid"

    # Check cache first
    try:
        cache = get_cache()
        cached_result = cache.get(cache_key_prefix, content_hash, 0)
        if cached_result is not None:
            logger.debug(f"[DEPID] Cache hit: {content_hash[:16]}...")
            return float(cached_result)
        logger.debug(f"[DEPID] Cache miss: {content_hash[:16]}...")
    except Exception as e:
        logger.warning(f"[DEPID] Cache lookup failed: {e}")

    try:
        # DEPID returns: (density, word_count, dependencies)
        # Offload to thread pool to avoid blocking event loop
        result = await asyncio.to_thread(depid, text, is_depid_r=True)
        density, word_count, dependencies = result
        normalized = max(0.0, min(1.0, float(density)))

        # Cache the result with 1 hour TTL
        try:
            cache = get_cache()
            cache.set(cache_key_prefix, content_hash, 0, normalized, 3600)
            logger.debug(f"[DEPID] Cached result: {content_hash[:16]}... = {normalized}")
        except Exception as e:
            logger.warning(f"[DEPID] Cache store failed: {e}")

        logger.debug(f"[DEPID] Raw={density}, Normalized={normalized}")
        return normalized
    except Exception as e:
        logger.warning(f"[DEPID] Calculation failed: {e}")
        return None


def calculate_readability_scores(text: str) -> Dict[str, float]:
    """
    Calculate readability metrics using textstat.

    Args:
        text: The text content to analyze

    Returns:
        Dict with readability scores (defaults to None if unavailable)
    """
    if not text or len(text.strip()) < 50:
        return {}

    if not TEXTSTAT_AVAILABLE or textstat is None:
        logger.debug("[READABILITY] textstat library not available")
        return {}

    try:
        textstat.set_lang("en")
        scores = {
            "flesch_reading_ease": textstat.flesch_reading_ease(text),
            "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
            "gunning_fog": textstat.gunning_fog(text),
            "automated_readability_index": textstat.automated_readability_index(text),
            "coleman_liau_index": textstat.coleman_liau_index(text),
        }
        logger.debug(f"[READABILITY] Scores: {scores}")
        return scores
    except Exception as e:
        logger.warning(f"[READABILITY] Calculation failed: {e}")
        return {}


def calculate_combined_density(
    cpidr_density: float,
    depid_density: Optional[float],
    readability: Dict[str, float]
) -> float:
    """
    Combine multiple density metrics into a weighted score.

    Args:
        cpidr_density: CPIDR density score (0.0-1.0)
        depid_density: DEPID density score (0.0-1.0 or None)
        readability: Readability scores dict

    Returns:
        Combined density score (0.0-1.0)
    """
    # Get weights from environment or defaults
    cpidr_weight = config.CPIDR_WEIGHT
    depid_weight = config.DEPID_WEIGHT
    readability_weight = config.READABILITY_WEIGHT

    total_weight = cpidr_weight + depid_weight + readability_weight

    # Base: CPIDR
    combined = cpidr_density * cpidr_weight

    # Add: DEPID (if available)
    if depid_density is not None:
        combined += depid_density * depid_weight
    else:
        total_weight -= depid_weight

    # Add: Readability (inverse of difficulty)
    if readability and "flesch_reading_ease" in readability:
        flesch_ease = readability["flesch_reading_ease"]
        # Flesch ease: higher = easier (90-100 = very easy, 0-30 = very difficult)
        # Normalize to 0-1 where 1 = difficult (dense), 0 = easy (sparse)
        reading_difficulty = max(0, min(1, (90 - flesch_ease) / 90))
        combined += reading_difficulty * readability_weight
    else:
        total_weight -= readability_weight

    if total_weight > 0:
        return max(0.0, min(1.0, combined / total_weight))
    return cpidr_density


class ContentExtractor:
    """Extracts clean content from web pages using Trafilatura."""

    # High-signal domains get a reputation boost
    HIGH_TRUST_DOMAINS = {
        "arxiv.org": 1.15,
        "github.com": 1.10,
        "openai.com": 1.12,
        "deepmind.com": 1.12,
        "research.google": 1.12,
        "anthropic.com": 1.10,
        "huggingface.co": 1.08,
        "pytorch.org": 1.08,
        "tensorflow.org": 1.08,
        "nature.com": 1.15,
        "science.org": 1.15,
        "acm.org": 1.10,
        "ieee.org": 1.10,
        "distill.pub": 1.15,
        "lilianweng.github.io": 1.12,
        "colah.github.io": 1.12,
        "karpathy.github.io": 1.12,
        "martin.kleppmann.com": 1.10,
        "jvns.ca": 1.08,
        "rachelbythebay.com": 1.08,
        "danluu.com": 1.10,
        "brandur.org": 1.08,
    }

    # Patterns that indicate low-quality content
    SPAM_PATTERNS = [
        r"subscribe\s+to\s+our\s+newsletter",
        r"sign\s+up\s+for\s+free",
        r"limited\s+time\s+offer",
        r"click\s+here\s+to\s+buy",
        r"affiliate\s+link",
        r"sponsored\s+content",
        r"you\s+won't\s+believe",
        r"shocking",
        r"this\s+one\s+trick",
    ]

    async def extract_from_url(self, url: str, force_depth: bool = False) -> Dict[str, Any]:
        """
        Extract content from a URL and return structured data.
        
        Args:
            url: The URL to extract content from
            force_depth: If True, attempts deeper extraction (follows links, etc.)
        
        Returns:
            Dict with extracted content and metadata
        """
        extract_start = time.time()
        logger.info(f"[EXTRACTOR] Starting extraction for: {url}")

        try:
            fetch_start = time.time()
            html = await self._fetch_page(url)
            fetch_duration = time.time() - fetch_start
            
            if not html:
                total_duration = time.time() - extract_start
                logger.error(f"[EXTRACTOR] Failed to fetch page | Fetch: {fetch_duration:.3f}s | Total: {total_duration:.3f}s")
                return self._error_response(url, "Failed to fetch page")

            trafilatura_start = time.time()
            extracted = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_links=False,
                output_format="txt",
                config=TRAFILATURA_CONFIG,
            )
            trafilatura_duration = time.time() - trafilatura_start

            if not extracted:
                total_duration = time.time() - extract_start
                logger.error(f"[EXTRACTOR] No content extracted | Fetch: {fetch_duration:.3f}s | Trafilatura: {trafilatura_duration:.3f}s | Total: {total_duration:.3f}s")
                return self._error_response(url, "No content extracted")

            metadata_start = time.time()
            metadata = trafilatura.extract_metadata(html)
            title = metadata.title if metadata else self._extract_title_fallback(html)
            metadata_duration = time.time() - metadata_start

            signal_start = time.time()
            signal_score = self._calculate_signal_score(
                content=extracted,
                url=url,
                title=title or ""
            )
            signal_duration = time.time() - signal_start

            density_start = time.time()
            cpidr_score = await calculate_density(extracted)
            depid_score = await calculate_depid_density(extracted)
            readability_scores = calculate_readability_scores(extracted)
            density_duration = time.time() - density_start

            density_threshold = config.DENSITY_THRESHOLD

            combined_start = time.time()
            combined_density = calculate_combined_density(
                cpidr_density=cpidr_score,
                depid_density=depid_score,
                readability=readability_scores
            )
            combined_duration = time.time() - combined_start

            total_duration = time.time() - extract_start
            logger.info(f"[EXTRACTOR] Success: {len(extracted)} chars, signal={signal_score:.2f}, density={cpidr_score:.3f} | "
                       f"Fetch: {fetch_duration:.3f}s | Trafilatura: {trafilatura_duration:.3f}s | "
                       f"Metadata: {metadata_duration:.3f}s | Signal: {signal_duration:.3f}s | "
                       f"Density: {density_duration:.3f}s | Combined: {combined_duration:.3f}s | Total: {total_duration:.3f}s")

            result = {
                "url": url,
                "title": title or "Untitled",
                "content": extracted,
                "raw_html": html,
                "source": self._extract_domain(url),
                "length": len(extracted),
                "signal_score": round(signal_score, 2),
                "density_score": round(cpidr_score, 3),
                "depid_density": round(depid_score, 3) if depid_score is not None else None,
                "readability_score": readability_scores,
            }

            return result

        except Exception as e:
            total_duration = time.time() - extract_start
            logger.error(f"[EXTRACTOR] Error: {str(e)} | Total: {total_duration:.3f}s")
            return self._error_response(url, str(e))

    async def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content from a URL using shared connection pool."""
        try:
            # Validate URL for SSRF protection
            is_valid, error_message = validate_url(url)
            if not is_valid:
                logger.error(f"[FETCH] SSRF validation failed for {url}: {error_message}")
                return None
            
            client = get_http_client()
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"[FETCH] Failed to fetch {url}: {e}")
            return None

    def _calculate_signal_score(self, content: str, url: str, title: str) -> float:
        """
        Calculate a signal score based on multiple factors.
        
        Score ranges from 0.0 to 1.0 where:
        - 0.0-0.3 = Low signal (spam, thin content)
        - 0.3-0.6 = Medium signal (average content)
        - 0.6-0.8 = Good signal (quality content)
        - 0.8-1.0 = High signal (exceptional content)
        """
        score = 0.5  # Start at neutral

        # Factor 1: Content Length (longer = better, up to a point)
        word_count = len(content.split())
        if word_count < 200:
            score -= 0.15  # Too short
        elif word_count < 500:
            score -= 0.05
        elif word_count < 1000:
            score += 0.05
        elif word_count < 3000:
            score += 0.10
        elif word_count < 5000:
            score += 0.12
        else:
            score += 0.15  # Long-form content

        # Factor 2: Domain Reputation
        domain = self._extract_domain(url)
        for trusted_domain, boost in self.HIGH_TRUST_DOMAINS.items():
            if trusted_domain in domain:
                score *= boost
                break

        # Factor 3: Code Block Density (technical content indicator)
        code_indicators = len(re.findall(r'```|`[^`]+`|def |class |function |const |import ', content))
        if code_indicators > 0:
            code_boost = min(0.15, code_indicators * 0.02)
            score += code_boost

        # Factor 4: Reference Density (citations, links to papers)
        ref_indicators = len(re.findall(r'\[\d+\]|arxiv\.|doi\.org|et al\.|figure \d|table \d', content, re.I))
        if ref_indicators > 0:
            ref_boost = min(0.10, ref_indicators * 0.015)
            score += ref_boost

        # Factor 5: Spam Pattern Detection (negative)
        spam_count = sum(
            1 for pattern in self.SPAM_PATTERNS
            if re.search(pattern, content, re.I)
        )
        if spam_count > 0:
            score -= spam_count * 0.10

        # Factor 6: Information Density (unique word ratio)
        words = content.lower().split()
        if words:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio > 0.5:
                score += 0.05  # High vocabulary diversity
            elif unique_ratio < 0.3:
                score -= 0.05  # Repetitive content

        # Factor 7: Structural Indicators (headers, lists)
        structural_patterns = len(re.findall(r'\n#{1,3}\s|\n\*\s|\n\d+\.\s|\n-\s', content))
        if structural_patterns > 3:
            score += 0.05

        # Clamp to valid range
        return max(0.0, min(1.0, score))

    def _extract_domain(self, url: str) -> str:
        """Extract the domain from a URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            return domain if domain else "unknown"
        except:
            return "unknown"

    def _extract_title_fallback(self, html: str) -> Optional[str]:
        """Fallback title extraction from HTML."""
        # First try to match a properly closed title tag
        match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.I)
        if match:
            return match.group(1).strip()
        # Fallback: match unclosed title tag (malformed HTML)
        match = re.search(r'<title[^>]*>([^<]+)$', html, re.I)
        if match:
            return match.group(1).strip()
        return None

    def _error_response(self, url: str, error: str) -> Dict[str, Any]:
        """Return an error response structure."""
        return {
            "url": url,
            "title": "Extraction Failed",
            "content": f"Error: {error}",
            "source": self._extract_domain(url),
            "length": 0,
            "signal_score": 0.0,
            "density_score": 0.0,
            "error": error,
        }


# Singleton instance
extractor = ContentExtractor()
