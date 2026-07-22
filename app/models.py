from pydantic import BaseModel
from typing import Optional, List, Dict
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
