import json
from google.cloud import pubsub_v1

from config import Config
from firestore_client import FirestoreClient
from orchestrator import AnalysisOrchestrator

def process_message(message):
    try:
        data = json.loads(message.data.decode('utf-8'))
        job_id = data.get('jobId')
        profile_url = data.get('profileUrl')

        print(f"\nRicevuto job: {job_id}")
        print(f"Profilo: {profile_url}")

        firestore = FirestoreClient()
        analyzer = AnalysisOrchestrator()

        firestore.update_job_status(job_id, "PROCESSING")

        try:
            result = analyzer.analyze_profile(profile_url)
            result["job_id"] = job_id

            firestore.update_analysis_result(job_id, result)

        except Exception as e:
            error_msg = str(e)
            print(f"Errore durante l'analisi: {error_msg}")
            firestore.update_job_status(job_id, "FAILED", error_message=error_msg)

        message.ack()

    except Exception as e:
        print(f"Errore generale: {e}")
        message.nack()

def main():
    try:
        Config.validate()
    except ValueError as e:
        print(f"Errore di configurazione: {e}")
        return

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(
        Config.PROJECT_ID,
        Config.PUBSUB_SUBSCRIPTION_ID
    )

    print(f"In ascolto su: {subscription_path}")
    print("In attesa di messaggi...\n")

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=process_message)

    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
    except Exception as e:
        print(f"\nErrore inatteso: {e}")
        streaming_pull_future.cancel()


if __name__ == "__main__":
    main()