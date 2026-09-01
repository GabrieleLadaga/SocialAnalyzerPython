import re
from presidio_analyzer import AnalyzerEngine
import spacy

from models import PIIResult

class PIIExtractor:

    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.analyzer = AnalyzerEngine()

        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_pattern = re.compile(r'(\+?[0-9]{1,3}[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}')
        self.url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*')

    def extract(self, text: str) -> PIIResult:
        result = PIIResult()

        presidio_results = self.analyzer.analyze(text=text, language='en')
        for item in presidio_results:
            value = text[item.start:item.end]
            self._add_to_result(result, item.entity_type, value)

        result.emails.extend(self.email_pattern.findall(text))
        result.phones.extend(self.phone_pattern.findall(text))
        result.urls.extend(self.url_pattern.findall(text))

        for field in ["emails", "phones", "persons", "locations",
                      "dates", "organizations", "urls", "credits_cards"]:
            setattr(result, field, list(set(getattr(result, field))))

        return result

    @staticmethod
    def _add_to_result(result: PIIResult, entity_type: str, value: str):
        mapping = {
            "EMAIL_ADDRESS": "emails",
            "PHONE_NUMBER": "phones",
            "PERSON": "persons",
            "LOCATION": "locations",
            "DATE_TIME": "dates",
            "ORGANIZATION": "organizations",
            "URL": "urls",
            "CREDIT_CARD": "credits_cards"
        }
        if entity_type in mapping:
            getattr(result, mapping[entity_type]).append(value)
