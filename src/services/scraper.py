import re
import logging
from typing import Dict, List, Optional, Tuple
import requests

from config import Config

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
MAX_POST_CAPTIONS = 6

def _instagram_input(url: str) -> dict:
    match = re.search(r'instagram\.com/([a-zA-Z0-9_.]+)', url)
    username = match.group(1) if match else url
    return {"usernames": [username]}


def _instagram_extract(items: list) -> str:
    texts = []
    for item in items:
        if item.get("biography"):
            texts.append(item["biography"])
        if item.get("fullName"):
            texts.append(f"Nome completo: {item['fullName']}")
        if item.get("username"):
            texts.append(f"@{item['username']}")
        if item.get("externalUrl"):
            texts.append(item["externalUrl"])
        for k in ("businessPhoneNumber", "public_phone_number", "contactPhoneNumber"):
            if item.get(k):
                texts.append(str(item[k]))
        if item.get("businessCategoryName"):
            texts.append(f"Categoria: {item['businessCategoryName']}")
        for v in item.values():
            if isinstance(v, str):
                texts.extend(_EMAIL_RE.findall(v))
        if item.get("caption"):
            texts.append(item["caption"])
        if item.get("latestPosts"):
            for post in item["latestPosts"][:MAX_POST_CAPTIONS]:
                if post.get("caption"):
                    texts.append(post["caption"])
    return " | ".join(texts)


def _instagram_images(items: list) -> list:
    urls = []
    for item in items:
        if item.get("private"):
            continue
        owner = (item.get("username") or "").lower()
        for post in (item.get("latestPosts") or []):
            post_owner = (post.get("ownerUsername") or "").lower()
            if owner and post_owner and post_owner != owner:
                continue
            if post.get("type") in ("Image", "Sidecar") and post.get("displayUrl"):
                urls.append(post["displayUrl"])
    return urls


def _tiktok_input(url: str) -> dict:
    match = re.search(r'tiktok\.com/@([a-zA-Z0-9_.]+)', url)
    username = match.group(1) if match else url
    return {"profiles": [username], "resultsPerPage": 10}


def _tiktok_extract(items: list) -> str:
    texts = []
    for item in items:
        if item.get("authorMeta"):
            meta = item["authorMeta"]
            if meta.get("name"):
                texts.append(f"Nome: {meta['name']}")
            if meta.get("nickName"):
                texts.append(f"Nickname: {meta['nickName']}")
            if meta.get("signature"):
                texts.append(meta["signature"])
        if item.get("signature"):
            texts.append(item["signature"])
        if item.get("nickname"):
            texts.append(f"Nickname: {item['nickname']}")
        if item.get("text"):
            texts.append(item["text"])
        if item.get("desc"):
            texts.append(item["desc"])
    return " | ".join(texts)


def _facebook_input(url: str) -> dict:
    return {"profileUrls": [url], "maxResults": 5}


def _facebook_extract(items: list) -> str:
    texts = []
    for item in items:
        if item.get("name"):
            texts.append(f"Nome: {item['name']}")
        if item.get("bio"):
            texts.append(item["bio"])
        if item.get("about"):
            texts.append(item["about"])
        if item.get("email"):
            texts.append(item["email"])
        if item.get("phone"):
            texts.append(item["phone"])
        if item.get("website"):
            texts.append(item["website"])
    return " | ".join(texts)

PLATFORM_CONFIGS = {
    "instagram": {
        "url_patterns": ["instagram.com"],
        "actor_id": "apify~instagram-profile-scraper",
        "build_input": _instagram_input,
        "extract_text": _instagram_extract,
        "extract_images": _instagram_images,
    },
    "tiktok": {
        "url_patterns": ["tiktok.com"],
        "actor_id": "clockworks~tiktok-scraper",
        "build_input": _tiktok_input,
        "extract_text": _tiktok_extract,
        "extract_images": None,
    },
    "facebook": {
        "url_patterns": ["facebook.com", "fb.com"],
        "actor_id": "apivault_labs~facebook-profile-scraper",
        "build_input": _facebook_input,
        "extract_text": _facebook_extract,
        "extract_images": None,
    },
}

def detect_platform(url: str) -> Optional[str]:
    url_lower = url.lower()
    for platform_name, config in PLATFORM_CONFIGS.items():
        for pattern in config["url_patterns"]:
            if pattern in url_lower:
                return platform_name
    return None

class SocialScraper:

    def __init__(self):
        self.apify_token = Config.APIFY_TOKEN
        self.apify_base_url = "https://api.apify.com/v2"
        self.max_posts = Config.MAX_POSTS_PER_PROFILE

    def scrape_profile(self, profile_url: str) -> Dict:
        platform = detect_platform(profile_url)

        if not platform:
            print(f"⚠Piattaforma non supportata per: {profile_url}")
            return self._scrape_generic(profile_url)

        config = PLATFORM_CONFIGS[platform]
        actor_id = config["actor_id"]
        print(f"Scraping {platform} con Actor: {actor_id}")

        try:
            text, image_urls = self._scrape_apify(profile_url, config)
            if not text:
                print(f"Nessun dato per {profile_url}, uso fallback generico")
                return self._scrape_generic(profile_url)

            bio = self._extract_bio(text)
            posts = self._extract_posts(text)

            return {
                "bio": bio,
                "posts": posts[:self.max_posts],
                "metadata": {
                    "platform": platform,
                    "post_count": len(posts),
                    "image_urls": image_urls or []
                }
            }
        except Exception as e:
            print(f"Errore durante lo scraping: {e}")
            return self._scrape_generic(profile_url)

    def _scrape_apify(self, url: str, config: dict) -> Tuple[Optional[str], List[str]]:
        actor_id = config["actor_id"]
        payload = config["build_input"](url)

        run_url = f"{self.apify_base_url}/acts/{actor_id}/run-sync-get-dataset-items"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.apify_token}",
        }

        print(f"Invocazione sincrona actor {actor_id}")

        response = requests.post(
            run_url,
            json=payload,
            headers=headers,
            timeout=180,
        )
        response.raise_for_status()

        items = response.json()
        if not items:
            print(f"Nessun risultato per {url}")
            return None, []

        if all(isinstance(it, dict) and it.get("error") for it in items):
            err = items[0].get("error")
            print(f"Profilo non accessibile: {err}")
            return None, []

        combined = config["extract_text"](items)
        if not combined.strip():
            print(f"Testo estratto vuoto per {url}")
            return None, []

        extract_images = config.get("extract_images")
        image_urls = extract_images(items) if extract_images else []

        print(f"Scraping completato: {len(combined)} caratteri, {len(image_urls)} immagini")
        return combined, image_urls

    def _extract_bio(self, text: str) -> str:
        lines = text.split(" | ")
        for line in lines:
            if "biography" in line.lower() or "nome completo" in line.lower():
                return line
        return lines[0] if lines else "Profilo generico"

    def _extract_posts(self, text: str) -> List[str]:
        lines = text.split(" | ")
        posts = []

        for line in lines:
            if "@" in line or "#" in line or "http" in line or "mailto" in line:
                if "biography" not in line.lower() and "nome completo" not in line.lower():
                    posts.append(line)
        return posts if posts else ["Post di esempio per la demo"]

    def _scrape_generic(self, url: str) -> Dict:
        username = url.rstrip('/').split('/')[-1] if url else "testuser"
        print(f"Fallback generico per: {url}")

        posts = [
            f"Oggi al lavoro, che bella giornata! #team #success",
            f"Rilassandomi al parco con la mia famiglia",
            f"Nuovo progetto avviato con i colleghi!",
            f"Visita il mio sito: {url}",
            f"Compleanno di mio figlio oggi",
            f"Viaggiando per lavoro a Milano, che città!",
            f"La mia email: {username}@gmail.com"
        ]

        return {
            "bio": "Appassionato di tecnologia, papà di due bambini, viaggiatore",
            "posts": posts[:self.max_posts],
            "metadata": {
                "platform": "generic",
                "post_count": len(posts),
                "image_urls": []
            }

        }