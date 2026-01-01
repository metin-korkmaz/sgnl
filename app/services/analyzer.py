"""
SGNL Heuristic Analyzer
Logic-based content scoring without LLM (for speed).
"""

import re
from typing import Dict, List, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class HeuristicAnalyzer:
    """
    Analyzes raw HTML content and returns a signal score based on
    structural heuristics (no LLM required).
    """
    
    # Coding-related keywords that indicate technical content
    CODING_KEYWORDS = {
        "python", "javascript", "typescript", "java", "rust", "go", "golang",
        "api", "error", "how to", "tutorial", "example", "code", "function",
        "class", "method", "algorithm", "data structure", "programming",
        "debug", "exception", "library", "framework", "sdk", "cli",
        "docker", "kubernetes", "database", "sql", "nosql", "git"
    }
    
    # Affiliate patterns to detect monetization spam
    AFFILIATE_PATTERNS = [
        r"amzn\.to",
        r"shareasale",
        r"clickbank",
        r"cj\.com",
        r"affiliate",
        r"awin1\.com",
        r"rakuten",
        r"impact\.com",
        r"partner\.",
        r"ref=",
        r"tag=",
        r"utm_source=affiliate"
    ]
    
    # Hype words that indicate clickbait/low-quality content
    HYPE_WORDS = [
        "shocking", "miracle", "secret", "unbelievable", "amazing",
        "you won't believe", "mind-blowing", "insane", "crazy",
        "game-changer", "revolutionary", "ultimate", "best ever",
        "10x", "100x", "overnight", "instantly", "quick fix",
        "one weird trick", "doctors hate", "they don't want you to know"
    ]
    
    def __init__(self):
        self.affiliate_regex = re.compile(
            "|".join(self.AFFILIATE_PATTERNS), 
            re.IGNORECASE
        )
        self.hype_regex = re.compile(
            "|".join(self.HYPE_WORDS), 
            re.IGNORECASE
        )
    
    def calculate_structure_score(
        self, 
        html_content: str, 
        query_context: str
    ) -> Dict[str, any]:
        """
        Analyze HTML content and return a signal score.
        
        Args:
            html_content: Raw HTML of the page
            query_context: User's search query for context
            
        Returns:
            Dict with 'score' (0-100) and 'reason' (explanation)
        """
        if not html_content or len(html_content) < 100:
            return {"score": 0, "reason": "Empty or too short content", "adjustments": []}

        try:
            soup = BeautifulSoup(html_content, "lxml")
        except Exception as e:
            logger.warning(f"Failed to parse HTML: {e}")
            return {"score": 30, "reason": "Failed to parse HTML", "adjustments": []}
        
        # Initialize scores
        base_score = 50
        adjustments: List[Tuple[int, str]] = []
        
        # 1. Code Density Analysis
        code_score, code_reason = self._analyze_code_density(
            soup, query_context
        )
        if code_score != 0:
            adjustments.append((code_score, code_reason))
        
        # 2. Data Density (tables)
        data_score, data_reason = self._analyze_data_density(soup)
        if data_score != 0:
            adjustments.append((data_score, data_reason))
        
        # 3. Slop Detection (HTML bloat)
        slop_score, slop_reason = self._detect_slop(html_content, soup)
        if slop_score != 0:
            adjustments.append((slop_score, slop_reason))
        
        # 4. Affiliate Detection
        affiliate_score, affiliate_reason = self._detect_affiliates(soup)
        if affiliate_score != 0:
            adjustments.append((affiliate_score, affiliate_reason))
        
        # 5. Title Hype Detection
        hype_score, hype_reason = self._detect_hype(soup)
        if hype_score != 0:
            adjustments.append((hype_score, hype_reason))
        
        # Calculate final score
        total_adjustment = sum(adj[0] for adj in adjustments)
        final_score = max(0, min(100, base_score + total_adjustment))
        
        # Build reason string
        if adjustments:
            reasons = [adj[1] for adj in adjustments if adj[0] != 0]
            reason = "; ".join(reasons[:3])  # Top 3 reasons
        else:
            reason = "Average content quality"
        
        logger.info(
            f"[HEURISTIC] Score: {final_score}, "
            f"Adjustments: {len(adjustments)}, Reason: {reason}"
        )
        
        return {
            "score": final_score,
            "reason": reason,
            "adjustments": adjustments
        }
    
    def _analyze_code_density(
        self, 
        soup: BeautifulSoup, 
        query: str
    ) -> Tuple[int, str]:
        """Boost score if coding content matches coding query."""
        query_lower = query.lower()
        is_coding_query = any(
            kw in query_lower for kw in self.CODING_KEYWORDS
        )
        
        # Count code elements
        pre_tags = len(soup.find_all("pre"))
        code_tags = len(soup.find_all("code"))
        total_code = pre_tags + code_tags
        
        if is_coding_query and total_code >= 3:
            return (20, f"High code density ({total_code} blocks)")
        elif is_coding_query and total_code >= 1:
            return (10, f"Contains code examples ({total_code} blocks)")
        elif not is_coding_query and total_code >= 5:
            # Technical content even without coding query
            return (10, f"Rich in code samples ({total_code} blocks)")
        
        return (0, "")
    
    def _analyze_data_density(self, soup: BeautifulSoup) -> Tuple[int, str]:
        """Boost score if structured data (tables) exists."""
        tables = soup.find_all("table")
        
        if len(tables) >= 3:
            return (15, f"Structured data tables ({len(tables)})")
        elif len(tables) >= 1:
            return (8, "Contains data tables")
        
        return (0, "")
    
    def _detect_slop(
        self, 
        html: str, 
        soup: BeautifulSoup
    ) -> Tuple[int, str]:
        """Penalize if HTML-to-text ratio indicates bloat/ads."""
        text = soup.get_text(separator=" ", strip=True)

        # Calculate ratio
        html_len = len(html)
        text_len = len(text)

        # Check for NO text first (more severe than thin content)
        if text_len == 0:
            return (-30, "No readable text content")

        if len(text) < 200:
            return (-20, "Very thin content")
        
        ratio = html_len / text_len
        
        # High ratio means lots of HTML markup (ads, scripts, etc.)
        if ratio > 20:
            return (-25, f"Extremely bloated HTML (ratio: {ratio:.1f})")
        elif ratio > 12:
            return (-15, f"High HTML bloat (ratio: {ratio:.1f})")
        elif ratio > 8:
            return (-5, "Moderate HTML overhead")
        elif ratio < 3:
            # Very clean, text-focused content
            return (10, "Clean, text-focused content")
        
        return (0, "")
    
    def _detect_affiliates(self, soup: BeautifulSoup) -> Tuple[int, str]:
        """Penalize if external links contain affiliate patterns."""
        links = soup.find_all("a", href=True)
        affiliate_count = 0
        
        for link in links:
            href = link.get("href", "")
            if self.affiliate_regex.search(href):
                affiliate_count += 1
        
        if affiliate_count >= 5:
            return (-30, f"Affiliate farm detected ({affiliate_count} links)")
        elif affiliate_count >= 3:
            return (-20, f"Multiple affiliate links ({affiliate_count})")
        elif affiliate_count >= 1:
            return (-10, "Contains affiliate links")
        
        return (0, "")
    
    def _detect_hype(self, soup: BeautifulSoup) -> Tuple[int, str]:
        """Penalize if title contains hype/clickbait words."""
        # Check title tag first (higher penalty)
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text()
            if self.hype_regex.search(title):
                return (-20, f"Clickbait title detected: '{title[:50]}...'")

        # Also check h1 (lower penalty)
        h1_tag = soup.find("h1")
        if h1_tag:
            h1_text = h1_tag.get_text()
            if self.hype_regex.search(h1_text):
                return (-15, f"Hype headline detected: '{h1_text[:50]}...'")

        return (0, "")


# Singleton instance
heuristic_analyzer = HeuristicAnalyzer()
