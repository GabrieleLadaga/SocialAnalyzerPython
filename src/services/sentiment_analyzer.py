from google.cloud import language_v1

from models import SentimentResult

class SentimentAnalyzer:

    def __init__(self):
        self.client = language_v1.LanguageServiceClient()

    def analyze(self, text: str) -> SentimentResult:

        document = language_v1.Document(
            content=text,
            type_=language_v1.Document.Type.PLAIN_TEXT
        )

        sentiment_response = self.client.analyze_sentiment(
            request={'document': document}
        )
        sentiment = sentiment_response.document_sentiment

        entities_response = self.client.analyze_entities(
            request={'document': document}
        )
        entities = {
            entity.name: {
                "type": entity.type_.name,
                "salience": entity.salience
            }
            for entity in entities_response.entities
        }

        return SentimentResult(
            score=sentiment.score,
            magnitude=sentiment.magnitude,
            entities=entities
        )
