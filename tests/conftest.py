import pytest
from src.models import PIIResult, SentimentResult, AnalysisReport

@pytest.fixture
def mock_pii_result():
    result = PIIResult()
    result.emails = ["test@example.com"]
    result.phones = ["123-456-7890"]
    result.persons = ["Mario Rossi"]
    return result

@pytest.fixture
def mock_sentiment_result():
    return SentimentResult(
        score=0.5,
        magnitude=1.0,
        entities={"Google": {"type": "ORGANIZATION", "salience": 0.8}}
    )

@pytest.fixture
def mock_analysis_report():
    return AnalysisReport(
        summary="Test summary",
        patterns="Test patterns",
        social_engineering_risk="Test risk",
        risk_level="MEDIO",
        recommendations="Test recommendations"
    )

@pytest.fixture
def mock_scraped_data():
    return {
        "bio": "Test bio",
        "posts": ["Post 1", "Post 2"],
        "metadata": {"platform": "test", "post_count": 2}
    }
