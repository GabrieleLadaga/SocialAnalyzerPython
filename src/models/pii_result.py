from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class PIIResult:
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    persons: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    organizations: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    credits_cards: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items() if v}
