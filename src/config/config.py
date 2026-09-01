import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
    PUBSUB_SUBSCRIPTION_ID = os.getenv("PUBSUB_SUBSCRIPTION_ID", "")

    APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
    APIFY_BASE_URL = "https://api.apify.com/v2"

    MAX_POSTS_PER_PROFILE = 5

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = "models/gemini-3.6-flash"

    FIRESTORE_COLLECTION = "analysis_jobs"

    POLLING_INTERVAL = 5

    DEBUG = os.getenv("DEBUG", "False").lower() == "True"

    @staticmethod
    def validate():
        required = [
            Config.PROJECT_ID,
            Config.APIFY_TOKEN,
            Config.GEMINI_API_KEY
        ]
        missing = [v for v in required if not v]
        if missing:
            raise ValueError(f"Variabili d'ambiente mancanti: {missing}.")
