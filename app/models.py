from pydantic import BaseModel
from typing import Optional, List, Dict
from enum import Enum


class BiasRating(str, Enum):
    NEUTRAL = "Neutral"
    PROMOTIONAL = "Promotional"
    BIASED = "Biased"
    SPONSORED = "Sponsored"


class DeepScanRequest(BaseModel):
    url: str


class DeepScanResponse(BaseModel):
    url: str
    title: Optional[str] = None
    summary: Optional[str] = None
    key_findings: List[str] = []
    technical_depth_score: int = 0
    bias_rating: BiasRating = BiasRating.NEUTRAL
    heuristic_score: Optional[int] = None
    raw_content_preview: Optional[str] = None
    density_score: Optional[float] = None
    depid_density: Optional[float] = None
    readability_score: Optional[Dict[str, float]] = None
    signal_score: Optional[float] = None
    skipped_llm: bool = False


class ScanTopicRequest(BaseModel):
    topic: str
    max_results: int = 10


class ExtractionRequest(BaseModel):
    url: str
    force_depth: bool = False


class ExtractionResponse(BaseModel):
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    word_count: int = 0
    extraction_method: str = "trafilatura"
    density_score: Optional[float] = None
    depid_density: Optional[float] = None
    readability_score: Optional[Dict[str, float]] = None
    signal_score: Optional[float] = None
