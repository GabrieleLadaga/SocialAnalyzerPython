from dataclasses import dataclass

@dataclass
class AnalysisReport:
    summary: str = ""
    patterns: str = ""
    social_engineering_risk: str = ""
    risk_level: str = ""
    recommendations: str = ""
