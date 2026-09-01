from dataclasses import dataclass, field
from typing import Dict

@dataclass
class SentimentResult:
    score: float = 0.0
    magnitude: float = 0.0
    entities: Dict[str, Dict] = field(default_factory=dict)
