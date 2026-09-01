import pytest
from unittest.mock import patch, MagicMock
from src.services.scraper import SocialScraper

class TestSocialScraper:

    @pytest.fixture
    def scraper(self):
        return SocialScraper()

    @patch('src.services.scraper.requests')
    def test_detect_platform_instagram(self, mock_requests, scraper):
        url = "https://www.instagram.com/testuser/"
        platform = scraper._detect_platform(url)
        assert platform == "instagram"

    @patch('src.services.scraper.requests')
    def test_detect_platform_twitter(self, mock_requests, scraper):
        url = "https://twitter.com/testuser"
        platform = scraper._detect_platform(url)
        assert platform == "twitter"

    @patch('src.services.scraper.requests')
    def test_detect_platform_generic(self, mock_requests, scraper):
        url = "https://example.com"
        platform = scraper._detect_platform(url)
        assert platform == "generic"

    @patch('src.services.scraper.requests')
    def test_scrape_generic(self, mock_requests, scraper):
        result = scraper._scrape_generic()
        assert result["bio"] == "Profilo generico"
        assert len(result["posts"]) == 1
        assert result["metadata"]["platform"] == "generic"

    @patch('src.services.scraper.requests')
    def test_get_actor_id(self, mock_requests, scraper):
        assert scraper._get_actor_id("instagram") == "apify/instagram-scraper"
        assert scraper._get_actor_id("twitter") == "apify/twitter-scraper"
        assert scraper._get_actor_id("unknown") == "apify/generic-scraper"