import pytest
from unittest.mock import patch, MagicMock
from src.services.sentiment_analyzer import SentimentAnalyzer

class TestSentimentAnalyzer:

    @pytest.fixture
    def analyzer(self):
        return SentimentAnalyzer()

    @patch('src.services.sentiment_analyzer.language_v1.LanguageServiceClient')
    def test_analyze_sentiment(self, mock_client, analyzer):
        mock_sentiment = MagicMock()
        mock_sentiment.document_sentiment.score = 0.8
        mock_sentiment.document_sentiment.magnitude = 1.2

        mock_entity = MagicMock()
        mock_entity.name = "test"
        mock_entity.type_.name = "TEST"
        mock_entity.salience = 0.5

        mock_entities_response = MagicMock()
        mock_entities_response.entities = [mock_entity]

        mock_client.return_value.analyze_sentiment.return_value = mock_sentiment
        mock_client.return_value.analyze_entities.return_value = mock_entities_response

        result = analyzer.analyze("This is a positive text!")

        assert result.score > 0
        assert result.magnitude > 0
        assert "test" in result.entities

    @patch('src.services.sentiment_analyzer.language_v1.LanguageServiceClient')
    def test_analyze_negative_sentiment(self, mock_client, analyzer):
        mock_sentiment = MagicMock()
        mock_sentiment.document_sentiment.score = -0.7
        mock_sentiment.document_sentiment.magnitude = 0.9

        mock_entities_response = MagicMock()
        mock_entities_response.entities = []

        mock_client.return_value.analyze_sentiment.return_value = mock_sentiment
        mock_client.return_value.analyze_entities.return_value = mock_entities_response

        result = analyzer.analyze("This is a negative text!")

        assert result.score < 0
        assert result.magnitude > 0