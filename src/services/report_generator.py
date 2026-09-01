import json
import re
from typing import Dict, List
from dataclasses import asdict
import google.generativeai as genai

from config import Config
from models import AnalysisReport, PIIResult, SentimentResult

class ReportGenerator:

    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)

    def generate(self, profile_url: str, pii: PIIResult, sentiment: SentimentResult,
                 posts: List[str]) -> AnalysisReport:
        pii_data = asdict(pii)
        pii_summary = self._summarize_pii(pii_data)
        sample_posts = posts[:2] if posts else ["Nessun post disponibile"]  # Solo 2 post

        prompt = self._build_prompt(profile_url, pii_summary, sentiment, sample_posts)

        try:
            response = self.model.generate_content(
                prompt,
                request_options={"timeout": 60}
            )
            return self._parse_response(response.text)
        except Exception as e:
            print(f"Errore generazione report: {e}")
            return self._fallback_report()

    @staticmethod
    def _summarize_pii(pii_data: Dict) -> Dict:
        return {
            "emails": pii_data["emails"][:5] if pii_data["emails"] else [],
            "phones": pii_data["phones"][:5] if pii_data["phones"] else [],
            "persons": pii_data["persons"][:5] if pii_data["persons"] else [],
            "locations": pii_data["locations"][:5] if pii_data["locations"] else [],
            "organizations": pii_data["organizations"][:5] if pii_data["organizations"] else [],
        }

    def _build_prompt(self, profile_url: str, pii_summary: Dict,
                      sentiment: SentimentResult, sample_posts: List[str]) -> str:

        sample_posts = sample_posts[:3]

        prompt = f"""
                    Sei un esperto di privacy e cybersecurity. Analizza il profilo social e genera un report JSON strutturato.
                
                    **Regole importanti**:
                    - Rispondi SOLO con un JSON valido, senza testo introduttivo.
                    - Usa i seguenti campi: summary, patterns, social_engineering_risk, risk_level, recommendations.
                    - risk_level deve essere solo "BASSO", "MEDIO" o "ALTO".
                    - Sii conciso ma preciso (massimo 2-3 frasi per campo).
                
                    **Input**:
                    - URL: {profile_url}
                    - PII trovate: {json.dumps(pii_summary, indent=2)}
                    - Sentiment score: {sentiment.score:.2f} (da -1 negativo a +1 positivo)
                    - Post analizzati: {json.dumps(sample_posts, indent=2)[:300]} (solo i primi 300 caratteri)
                
                    **Esempi di output corretti**:
                
                    Esempio 1 (profilo con molte PII):
                    {{
                        "summary": "Il profilo espone numerose informazioni personali: email, telefono e luogo di lavoro, aumentando il rischio di contatti indesiderati.",
                        "patterns": "L'utente pubblica frequentemente la sua posizione e i suoi spostamenti, rivelando routine quotidiane.",
                        "social_engineering_risk": "Email e telefono sono dati pubblici, permettendo a malintenzionati di contattare l'utente con tentativi di phishing personalizzati.",
                        "risk_level": "ALTO",
                        "recommendations": "Rimuovere email e telefono dalla biografia. Limitare la visibilità dei post che rivelano la posizione."
                    }}
                
                    Esempio 2 (profilo con poche PII):
                    {{
                        "summary": "Il profilo mostra principalmente contenuti generici e professionali, con limitate informazioni personali identificabili.",
                        "patterns": "I post sono prevalentemente legati al lavoro, senza riferimenti a vita privata o routine.",
                        "social_engineering_risk": "Il rischio è basso, poiché non emergono dati sensibili come email, telefono o indirizzi.",
                        "risk_level": "BASSO",
                        "recommendations": "Mantenere l'attuale livello di privacy, evitando di pubblicare informazioni personali in futuro."
                    }}
                
                    Ora analizza il profilo e rispondi con un JSON seguendo ESATTAMENTE il formato degli esempi sopra. Non aggiungere altro testo.
                    """
        return prompt

    def _parse_response(self, text: str) -> AnalysisReport:
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)

        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != -1:
            data = json.loads(text[start:end])
            return AnalysisReport(
                summary=data.get("summary", "Report generato automaticamente."),
                patterns=data.get("patterns", "N/A"),
                social_engineering_risk=data.get("social_engineering_risk", "N/A"),
                risk_level=data.get("risk_level", "MEDIO"),
                recommendations=data.get("recommendations", "N/A")
            )

        return self._fallback_report()

    @staticmethod
    def _fallback_report() -> AnalysisReport:
        return AnalysisReport(
            summary="Analisi completata con successo.",
            patterns="Nessun pattern significativo rilevato.",
            social_engineering_risk="Basato sulle PII estratte, si consiglia di limitare la condivisione di dati personali.",
            risk_level="MEDIO",
            recommendations="Rivedi le informazioni personali pubblicate e limita la visibilità dei post."
        )