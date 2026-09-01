from dataclasses import dataclass
from typing import Optional, Dict

from .pii_result import PIIResult
from .analysis_report import AnalysisReport
from .sentiment_result import SentimentResult

@dataclass
class AnalysisResult:
    job_id: str
    profile_url: str
    pii: PIIResult
    sentiment: SentimentResult
    report: AnalysisReport
    post_count: int
    scraped_data: Optional[Dict] = None
