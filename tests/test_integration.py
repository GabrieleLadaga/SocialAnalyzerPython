import pytest
import os
from src.firestore_client import FirestoreClient
from src.orchestrator import AnalysisOrchestrator

@pytest.mark.skipif(
    not os.getenv("FIRESTORE_EMULATOR_HOST"),
    reason="Firestore emulator non attivo. Imposta FIRESTORE_EMULATOR_HOST."
)
class TestIntegration:

    @pytest.fixture
    def firestore_client(self):
        return FirestoreClient()

    @pytest.fixture
    def orchestrator(self):
        return AnalysisOrchestrator()

    def test_firestore_connection(self, firestore_client):
        try:
            result = firestore_client.get_job("non-existent-job-id")
            assert result is None
        except Exception as e:
            pytest.fail(f"Errore connessione Firestore: {e}")

    def test_analyze_profile_with_emulator(self, orchestrator):
        result = orchestrator.analyze_profile("https://www.instagram.com/testuser/")

        assert result is not None
        assert "profile_url" in result
        assert "pii" in result
        assert "sentiment" in result
        assert "report" in result
        assert "post_count" in result
        assert result["post_count"] > 0