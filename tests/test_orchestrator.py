import pytest
from unittest.mock import patch, MagicMock
from src.orchestrator import AnalysisOrchestrator

class TestOrchestrator:

    @pytest.fixture
    def orchestrator(self):
        return AnalysisOrchestrator()

    @patch('src.orchestrator.SocialScraper')
    @patch('src.orchestrator.PIIExtractor')
    @patch('src.orchestrator.SentimentAnalyzer')
    @patch('src.orchestrator.ReportGenerator')
    def test_analyze_profile(self, mock_report, mock_sentiment, mock_pii, mock_scraper, orchestrator):
        mock_scraper.return_value.scrape_profile.return_value = {
            "bio": "Test bio",
            "posts": ["Test post 1", "Test post 2"],
            "metadata": {"platform": "test", "post_count": 2}
        }

        mock_pii_result = MagicMock()
        mock_pii_result.emails = ["test@example.com"]
        mock_pii.return_value.extract.return_value = mock_pii_result

        mock_sentiment_result = MagicMock()
        mock_sentiment_result.score = 0.5
        mock_sentiment_result.magnitude = 1.0
        mock_sentiment_result.entities = {"test": {"type": "TEST", "salience": 0.5}}
        mock_sentiment.return_value.analyze.return_value = mock_sentiment_result

        mock_report_result = MagicMock()
        mock_report_result.summary = "Test summary"
        mock_report_result.risk_level = "MEDIO"
        mock_report.return_value.generate.return_value = mock_report_result

        result = orchestrator.analyze_profile("https://test.com/user")

        assert result["profile_url"] == "https://test.com/user"
        assert result["post_count"] == 2
        assert result["report"].risk_level == "MEDIO"
        assert len(result["pii"].emails) > 0
