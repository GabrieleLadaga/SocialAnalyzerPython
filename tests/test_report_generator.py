import pytest
from unittest.mock import patch, MagicMock
from src.services.report_generator import ReportGenerator
from src.models import PIIResult, SentimentResult

class TestReportGenerator:

    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    @pytest.fixture
    def sample_pii(self):
        pii = PIIResult()
        pii.emails = ["test@example.com"]
        pii.phones = ["123-456-7890"]
        pii.persons = ["Mario Rossi"]
        return pii

    @pytest.fixture
    def sample_sentiment(self):
        return SentimentResult(score=0.5, magnitude=1.0, entities={"test": {"type": "TEST"}})

    @patch('src.services.report_generator.genai')
    def test_generate_report(self, mock_genai, generator, sample_pii, sample_sentiment):
        mock_response = MagicMock()
        mock_response.text = """
        ```json
        {
            "summary": "Test summary",
            "patterns": "Test patterns",
            "social_engineering_risk": "Test risk",
            "risk_level": "MEDIO",
            "recommendations": "Test recommendations"
        }
        """
        mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response

        result = generator.generate(
            "https://test.com/user",
            sample_pii,
            sample_sentiment,
            ["Post 1", "Post 2"]
        )

        assert result.summary == "Test summary"
        assert result.risk_level == "MEDIO"

    @patch('src.services.report_generator.genai')
    def test_generate_report_fallback(self, mock_genai, generator, sample_pii, sample_sentiment):
        mock_genai.GenerativeModel.return_value.generate_content.side_effect = Exception("API Error")

        result = generator.generate(
            "https://test.com/user",
            sample_pii,
            sample_sentiment,
            ["Post 1", "Post 2"]
        )

        assert result.risk_level == "MEDIO"
        assert result.summary == "Analisi completata con successo."
