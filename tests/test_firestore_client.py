import pytest
from unittest.mock import patch, MagicMock
from src.firestore_client import FirestoreClient

class TestFirestoreClient:

    @pytest.fixture
    def client(self):
        return FirestoreClient()

    @patch('src.firestore_client.firestore.Client')
    def test_update_job_status(self, mock_client, client):
        mock_doc_ref = MagicMock()
        mock_client.return_value.collection.return_value.document.return_value = mock_doc_ref

        client.update_job_status("job-123", "PROCESSING")

        mock_doc_ref.update.assert_called_once()
        args, kwargs = mock_doc_ref.update.call_args
        assert args[0]["status"] == "PROCESSING"

    @patch('src.firestore_client.firestore.Client')
    def test_get_job_not_found(self, mock_client, client):
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value.exists = False
        mock_client.return_value.collection.return_value.document.return_value = mock_doc_ref

        result = client.get_job("non-existent")
        assert result is None

    @patch('src.firestore_client.firestore.Client')
    def test_update_analysis_result(self, mock_client, client):
        mock_doc_ref = MagicMock()
        mock_client.return_value.collection.return_value.document.return_value = mock_doc_ref

        analysis_result = {
            "pii": MagicMock(to_dict=lambda: {"emails": ["test@example.com"]}),
            "sentiment": MagicMock(score=0.5, magnitude=1.0, entities={}),
            "report": MagicMock(summary="Test", patterns="Test", social_engineering_risk="Test", risk_level="MEDIO",
                                recommendations="Test"),
            "post_count": 2
        }

        client.update_analysis_result("job-123", analysis_result)

        mock_doc_ref.update.assert_called_once()
        args, kwargs = mock_doc_ref.update.call_args
        assert args[0]["status"] == "COMPLETED"
        assert args[0]["riskLevel"] == "MEDIO"
