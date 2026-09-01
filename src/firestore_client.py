from typing import Optional, Dict
from google.cloud import firestore
import json

from config import Config

class FirestoreClient:

    def __init__(self):
        self.db = firestore.Client(project=Config.PROJECT_ID)
        self.collection = Config.FIRESTORE_COLLECTION

    def update_job_status(self, job_id: str, status: str, report_summary: Optional[str] = None, risk_level: Optional[str] = None, error_message: Optional[str] = None):
        doc_ref = self.db.collection(self.collection).document(job_id)

        updates = {
            "status": status,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }

        if report_summary:
            updates["reportSummary"] = report_summary
        if risk_level:
            updates["riskLevel"] = risk_level
        if error_message:
            updates["errorMessage"] = error_message

        doc_ref.update(updates)

    def get_job(self, job_id: str) -> Optional[Dict]:
        doc_ref = self.db.collection(self.collection).document(job_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None

    def update_analysis_result(self, job_id: str, analysis_result: Dict):
        result_dict = {
            "pii": analysis_result["pii"].to_dict() if hasattr(analysis_result["pii"], "to_dict") else analysis_result[
                "pii"],
            "sentiment": {
                "score": analysis_result["sentiment"].score,
                "magnitude": analysis_result["sentiment"].magnitude,
                "entities": analysis_result["sentiment"].entities
            },
            "report": {
                "summary": analysis_result["report"].summary,
                "patterns": analysis_result["report"].patterns,
                "social_engineering_risk": analysis_result["report"].social_engineering_risk,
                "risk_level": analysis_result["report"].risk_level,
                "recommendations": analysis_result["report"].recommendations
            },
            "post_count": analysis_result["post_count"]
        }

        self.update_job_status(
            job_id=job_id,
            status="COMPLETED",
            report_summary=json.dumps(result_dict, indent=2, default=str),
            risk_level=analysis_result["report"].risk_level
        )
