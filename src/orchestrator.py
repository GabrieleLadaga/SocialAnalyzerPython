from typing import Dict

from services import SocialScraper, PIIExtractor, SentimentAnalyzer, ReportGenerator

class AnalysisOrchestrator:

    def __init__(self):
        self.scraper = SocialScraper()
        self.pii_extractor = PIIExtractor()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.report_generator = ReportGenerator()

    def analyze_profile(self, profile_url: str) -> Dict:
        print(f"\n{'=' * 60}")
        print(f"ANALISI PROFILO: {profile_url}")
        print(f"{'=' * 60}\n")

        scraped = self.scraper.scrape_profile(profile_url)
        bio = scraped.get("bio", "")
        posts = scraped.get("posts", [])

        all_text = f"{bio} " + " ".join(posts)
        pii = self.pii_extractor.extract(all_text)

        full_text = " ".join(posts)
        sentiment = self.sentiment_analyzer.analyze(full_text)

        report = self.report_generator.generate(profile_url, pii, sentiment, posts)

        result = {
            "profile_url": profile_url,
            "pii": pii,
            "sentiment": sentiment,
            "report": report,
            "post_count": len(posts),
            "scraped_data": scraped
        }

        print(f"\nAnalisi completata!")
        print(f"- Post analizzati: {len(posts)}")
        print(f"- Livello di rischio: {report.risk_level}")
        print(f"{'=' * 60}\n")

        return result
