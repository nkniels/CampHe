"""
CampHe — Base Scraper
=====================
Abstract base class that all source-specific scrapers must inherit from.
Provides shared HTTP fetching, logging, and a standard output schema.
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36 CampHe-Bot/2.0"
    ),
    "Accept-Language": "en,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class BaseScraper(ABC):
    """
    Abstract base class for all CampHe source scrapers.

    Subclasses must define:
      - `SOURCE_NAME`  : Human-readable name of the source.
      - `SOURCE_URL`   : The URL to scrape.
      - `CATEGORY`     : One of 'government', 'media', 'ngo', 'aggregator'.
      - `parse(soup)`  : Extracts and returns a list of campaign dicts.
    """

    SOURCE_NAME: str = "Unknown Source"
    SOURCE_URL: str = ""
    CATEGORY: str = "unknown"

    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self.scraped_at = datetime.utcnow().isoformat() + "Z"

    def fetch(self, url: str | None = None) -> BeautifulSoup | None:
        """Fetch a URL and return a BeautifulSoup object, or None on failure."""
        target = url or self.SOURCE_URL
        try:
            resp = requests.get(
                target,
                headers=COMMON_HEADERS,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            logger.info(f"[{self.SOURCE_NAME}] Fetched {target} ({resp.status_code})")
            return BeautifulSoup(resp.text, "lxml")
        except requests.RequestException as e:
            logger.error(f"[{self.SOURCE_NAME}] Failed to fetch {target}: {e}")
            return None

    @abstractmethod
    def parse(self, soup: BeautifulSoup) -> list[dict]:
        """Parse the page and return a list of campaign dicts."""
        ...

    def run(self) -> list[dict]:
        """Public entry point: fetch, parse, and return enriched campaigns."""
        logger.info(f"[{self.SOURCE_NAME}] Starting scrape...")
        soup = self.fetch()
        if soup is None:
            logger.warning(f"[{self.SOURCE_NAME}] Skipping — could not fetch page.")
            return []
        campaigns = self.parse(soup)
        # Enrich each result with standard metadata
        for c in campaigns:
            c.setdefault("source_name", self.SOURCE_NAME)
            c.setdefault("source_url", self.SOURCE_URL)
            c.setdefault("category", self.CATEGORY)
            c.setdefault("scraped_at", self.scraped_at)
            c.setdefault("status", "unknown")
            # Generate a stable ID from title + source to enable deduplication
            unique_str = f"{self.SOURCE_NAME}:{c.get('title', '')}"
            c["id"] = hashlib.md5(unique_str.encode()).hexdigest()[:12]
        logger.info(f"[{self.SOURCE_NAME}] Found {len(campaigns)} item(s).")
        return campaigns
