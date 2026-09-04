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

        # Conta quante PII sono state trovate
        pii_count = sum(1 for v in pii_summary.values() if v)

        prompt = f"""
                Sei un esperto di privacy e cybersecurity. Analizza il profilo social e genera un report JSON strutturato.
            
                **Regole importanti**:
                - Rispondi SOLO con un JSON valido.
                - Usa i campi: summary, patterns, social_engineering_risk, risk_level, recommendations.
                - **risk_level deve essere "ALTO" se il profilo espone almeno due tra questi: email, telefono, nome completo, indirizzo, luogo di lavoro, organizzazione.**
                - **risk_level deve essere "BASSO" se non espone email, telefono o altri dati sensibili.**
                - **In tutti gli altri casi, assegna "MEDIO".**
            
                **Input**:
                - URL: {profile_url}
                - PII trovate: {json.dumps(pii_summary, indent=2)}
                - Numero di PII trovate: {pii_count}
                - Sentiment score: {sentiment.score:.2f} (da -1 negativo a +1 positivo)
                - Post analizzati: {json.dumps(sample_posts, indent=2)[:500]}
            
                **Esempi di output**:
            
                Esempio 1 (RISCHIO ALTO - profilo con email e telefono):
                Input: PII trovate: {{"emails": ["test@example.com"], "phones": ["+39 123 456 7890"], "persons": ["Mario Rossi"]}}
                Output:
                {{
                    "summary": "Il profilo espone numerose informazioni personali: email, telefono, nome e luogo di lavoro, aumentando significativamente il rischio di contatti indesiderati.",
                    "patterns": "L'utente pubblica frequentemente la sua posizione e i suoi spostamenti, rivelando routine quotidiane.",
                    "social_engineering_risk": "Email e telefono sono dati pubblici, permettendo a malintenzionati di contattare l'utente con tentativi di phishing personalizzati e mirati.",
                    "risk_level": "ALTO",
                    "recommendations": "Rimuovere email e telefono dalla biografia. Limitare la visibilità dei post che rivelano la posizione."
                }}
            
                Esempio 2 (RISCHIO BASSO - profilo senza PII):
                Input: PII trovate: {{"persons": ["Paolo Rossi"]}}
                Output:
                {{
                    "summary": "Il profilo mostra principalmente contenuti generici e professionali, con limitate informazioni personali identificabili.",
                    "patterns": "I post sono prevalentemente legati al lavoro, senza riferimenti a vita privata o routine.",
                    "social_engineering_risk": "Il rischio è basso, poiché non emergono dati sensibili come email, telefono o indirizzi.",
                    "risk_level": "BASSO",
                    "recommendations": "Mantenere l'attuale livello di privacy, evitando di pubblicare informazioni personali in futuro."
                }}
            
                Esempio 3 (RISCHIO MEDIO - profilo con solo nome ma senza contatti):
                Input: PII trovate: {{"persons": ["Giulia Bianchi"], "locations": ["Milano"]}}
                Output:
                {{
                    "summary": "Il profilo mostra alcune informazioni personali come nome e città, ma non espone dati di contatto diretti.",
                    "patterns": "I post sono di natura personale ma non rivelano routine specifiche o dati sensibili.",
                    "social_engineering_risk": "Il rischio è moderato, poiché nome e città sono informazioni pubbliche ma facilmente utilizzabili per contestualizzare un attacco.",
                    "risk_level": "MEDIO",
                    "recommendations": "Valutare se è necessario rendere pubblici nome e città. Considerare di limitare la visibilità dei post personali."
                }}
            
                Ora analizza il profilo e rispondi con un JSON seguendo ESATTAMENTE il formato degli esempi sopra.
                """
        return prompt

    def _parse_response(self, text: str) -> AnalysisReport:
        print(f"🔍 RISPOSTA GREZZA DI GEMINI:\n{text}\n{'-' * 60}")

        # Prova a estrarre JSON da vari formati
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        else:
            # Prova a trovare qualsiasi oggetto JSON
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)

        try:
            data = json.loads(text)

            # Verifica che i campi essenziali ci siano
            if "risk_level" not in data:
                print("Campo risk_level mancante nella risposta")
                return self._fallback_report()

            # Mappa il rischio
            risk_map = {"alto": "ALTO", "medio": "MEDIO", "basso": "BASSO"}
            risk_level = data.get("risk_level", "").upper()
            if risk_level not in ["ALTO", "MEDIO", "BASSO"]:
                risk_level = risk_map.get(data.get("risk_level", "").lower(), "MEDIO")

            return AnalysisReport(
                summary=data.get("summary", "Report generato automaticamente."),
                patterns=data.get("patterns", "N/A"),
                social_engineering_risk=data.get("social_engineering_risk", "N/A"),
                risk_level=risk_level,
                recommendations=data.get("recommendations", "N/A")
            )
        except json.JSONDecodeError as e:
            print(f"❌ Errore parsing JSON: {e}")
            print(f"📄 Testo ricevuto: {text[:500]}...")
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