"""
CampHe — Source Scrapers
=========================
One class per data source. Each scraper implements the `parse()` method
with selectors specific to that website's HTML structure.

All selectors are annotated with TODOs where live inspection is required
to confirm the exact CSS class/tag names on the live site.
"""

import hashlib
import logging
import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from base_scraper import BaseScraper, COMMON_HEADERS

logger = logging.getLogger(__name__)


def _safe_text(element, default: str = "") -> str:
    """Safely extract stripped text from a BS4 element."""
    return element.get_text(strip=True) if element else default


def _try_parse_date(raw: str) -> str:
    """Attempt to parse a date string into ISO 8601 format. Returns raw string on failure."""
    if not raw:
        return ""
    try:
        return dateparser.parse(raw, fuzzy=True).date().isoformat()
    except (ValueError, OverflowError):
        return raw.strip()


# =============================================================================
# CATEGORY 1: OFFICIAL GOVERNMENT & PUBLIC HEALTH SOURCES
# =============================================================================


class MinsanteScraper(BaseScraper):
    """
    Ministère de la Santé Publique (MINSANTE)
    URL: https://www.minsante.cm

    Targets the news/actualites section for press releases and
    immunization/campaign announcements.

    TODO: Inspect https://www.minsante.cm/site/?q=actualites in DevTools
          and update the selectors below to match the live HTML.
    """

    SOURCE_NAME = "MINSANTE"
    SOURCE_URL = "https://www.minsante.cm/site/?q=actualites"
    CATEGORY = "government"

    def parse(self, soup: BeautifulSoup) -> list[dict]:
        campaigns = []
        # TODO: Replace with actual article selector from live site inspection
        articles = soup.select("div.views-row, article.node--type-article")
        for art in articles:
            title_el = art.select_one("h3, h2, .node__title a, span.field-content a")
            date_el = art.select_one("span.date-display-single, time, .field--name-post-date")
            desc_el = art.select_one("div.field--name-body p, .field-content p")
            link_el = art.select_one("a")

            title = _safe_text(title_el)
            if not title:
                continue

            campaigns.append(
                {
                    "title": title,
                    "date": _try_parse_date(_safe_text(date_el)),
                    "description": _safe_text(desc_el),
                    "location": "Cameroun",
                    "link": urljoin(self.SOURCE_URL, link_el.get("href", "")) if link_el else self.SOURCE_URL,
                }
            )
        return campaigns


class CDNSSScraper(BaseScraper):
    """
    Digital Library Center for the Health Sector (CDNSS-MINSANTE)
    URL: https://www.cdnss-minsante.cm

    Targets published documents: situational reports, strategic plans, vaccination guides.

    TODO: Inspect the publications listing page and update selectors below.
    """

    SOURCE_NAME = "CDNSS-MINSANTE"
    SOURCE_URL = "https://www.cdnss-minsante.cm"
    CATEGORY = "government"

    def parse(self, soup: BeautifulSoup) -> list[dict]:
        campaigns = []
        # TODO: Update selectors after live inspection
        items = soup.select("div.document-item, li.document, article")
        for item in items:
            title_el = item.select_one("h3, h2, a.document-title, .title a")
            date_el = item.select_one(".date, time, .published-on")
            desc_el = item.select_one("p, .description, .summary")
            link_el = item.select_one("a[href]")

            title = _safe_text(title_el)
            if not title:
                continue
            campaigns.append(
                {
                    "title": title,
                    "date": _try_parse_date(_safe_text(date_el)),
                    "description": _safe_text(desc_el),
                    "location": "Cameroun",
                    "link": urljoin(self.SOURCE_URL, link_el.get("href", "")) if link_el else self.SOURCE_URL,
                }
            )
        return campaigns


# =============================================================================
# CATEGORY 2: NATIONAL NEWS & MEDIA OUTLETS
# =============================================================================


class CameroonTribuneScraper(BaseScraper):
    """
    Cameroon Tribune (State-owned bilingual newspaper)
    URL: https://www.cameroon-tribune.cm/categorie.html?cat=6

    Targets the "Santé" (Health) section for ministerial health announcements
    and parliamentary health coverage.

    TODO: Inspect the health category listing and confirm selectors.
    """

    SOURCE_NAME = "Cameroon Tribune"
    SOURCE_URL = "https://www.cameroon-tribune.cm/categorie.html?cat=6"
    CATEGORY = "media"

    def parse(self, soup: BeautifulSoup) -> list[dict]:
        campaigns = []
        # TODO: Update selectors after live inspection of the health category page
        articles = soup.select("article, div.article-item, div.item-list li")
        for art in articles:
            title_el = art.select_one("h2 a, h3 a, .article-title a")
            date_el = art.select_one("time, span.article-date, .date")
            desc_el = art.select_one(".article-intro, p.description, .teaser")
            link_el = title_el  # title usually holds the link

            title = _safe_text(title_el)
            if not title:
                continue
            campaigns.append(
                {
                    "title": title,
                    "date": _try_parse_date(_safe_text(date_el)),
                    "description": _safe_text(desc_el),
                    "location": "Cameroun",
                    "link": urljoin(self.SOURCE_URL, link_el.get("href", "")) if link_el else self.SOURCE_URL,
                }
            )
        return campaigns


class ActuCamerounScraper(BaseScraper):
    """
    Actu Cameroun — Health Section
    URL: https://actucameroun.com/category/sante/

    Targets news articles in the dedicated health category.
    Good source for real-time blood donation drives and free screening events.

    TODO: Inspect the category page and confirm article selectors.
    """

    SOURCE_NAME = "Actu Cameroun"
    SOURCE_URL = "https://actucameroun.com/category/sante/"
    CATEGORY = "media"

    def parse(self, soup: BeautifulSoup) -> list[dict]:
        campaigns = []
        # Common WordPress theme selectors — likely to work but should be verified
        articles = soup.select("article.post, div.post, article[class*='post']")
        for art in articles:
            title_el = art.select_one("h2.entry-title a, h3.entry-title a, .post-title a")
            date_el = art.select_one("time.entry-date, span.post-date, .published")
            desc_el = art.select_one("div.entry-summary p, .excerpt p, .post-excerpt")
            link_el = title_el

            title = _safe_text(title_el)
            if not title:
                continue
            campaigns.append(
                {
                    "title": title,
                    "date": _try_parse_date(
                        date_el.get("datetime", _safe_text(date_el)) if date_el else ""
                    ),
                    "description": _safe_text(desc_el),
                    "location": "Cameroun",
                    "link": urljoin(self.SOURCE_URL, link_el.get("href", "")) if link_el else self.SOURCE_URL,
                }
            )
        return campaigns


class CRTVScraper(BaseScraper):
    """
    CRTV (Cameroon Radio Television)
    URL: https://www.crtv.cm

    Targets the latest news for health-related keywords in national broadcasts.

    TODO: Inspect CRTV's news listing page and refine selectors.
    """

    SOURCE_NAME = "CRTV"
    SOURCE_URL = "https://www.crtv.cm"
    CATEGORY = "media"

    HEALTH_KEYWORDS = [
        "santé", "sante", "health", "vaccin", "vaccine", "campagne",
        "campaign", "paludisme", "malaria", "cholera", "vih", "hiv",
        "dépistage", "screening", "minsante",
    ]

    def parse(self, soup: BeautifulSoup) -> list[dict]:
        campaigns = []
        # TODO: Update news article selector after live inspection
        articles = soup.select("article, div.news-item, div.post")
        for art in articles:
            title_el = art.select_one("h2 a, h3 a, .entry-title a, .article-title a")
            date_el = art.select_one("time, .date, .post-date")
            desc_el = art.select_one("p, .excerpt, .summary")

            title = _safe_text(title_el).lower()
            # Only keep articles that contain health-related keywords
            if not any(kw in title for kw in self.HEALTH_KEYWORDS):
                continue
            title = _safe_text(title_el)  # Get original casing after filter
            campaigns.append(
                {
                    "title": title,
                    "date": _try_parse_date(_safe_text(date_el)),
                    "description": _safe_text(desc_el),
                    "location": "Cameroun",
                    "link": urljoin(self.SOURCE_URL, title_el.get("href", "")) if title_el else self.SOURCE_URL,
                }
            )
        return campaigns


# =============================================================================
# CATEGORY 3: INTERNATIONAL HEALTH ORGANIZATIONS & NGOs
# =============================================================================


class WHOCameroonScraper(BaseScraper):
    """
    WHO Regional Office for Africa — Cameroon
    URL: https://www.afro.who.int/countries/cameroon

    Targets press releases on disease outbreaks, food safety, and regional transitions.

    TODO: Inspect the Cameroon country page and update selectors.
    """

    SOURCE_NAME = "WHO Cameroon"
    SOURCE_URL = "https://www.afro.who.int/countries/cameroon"
    CATEGORY = "ngo"

    def parse(self, soup: BeautifulSoup) -> list[dict]:
        campaigns = []
        # WHO Africa uses Drupal — these selectors are typical for afro.who.int
        articles = soup.select(
            "div.views-row, article.node--type-news, div.field--name-field-news"
        )
        for art in articles:
            title_el = art.select_one("h3.node__title a, h2 a, span.field-content a")
            date_el = art.select_one("time, span.date-display-single, .field--name-post-date")
            desc_el = art.select_one("div.field--name-body, .field--name-field-summary, p")
            link_el = title_el

            title = _safe_text(title_el)
            if not title:
                continue
            campaigns.append(
                {
                    "title": title,
                    "date": _try_parse_date(_safe_text(date_el)),
                    "description": _safe_text(desc_el),
                    "location": "Cameroun",
                    "link": urljoin(self.SOURCE_URL, link_el.get("href", "")) if link_el else self.SOURCE_URL,
                }
            )
        return campaigns


class CDCCameroonScraper(BaseScraper):
    """
    CDC Global Health — Cameroon
    URL: https://www.cdc.gov/global-health/countries/cameroon.html

    Targets summaries of vaccination campaigns (polio, RTS,S malaria) and
    disease-control programs (HIV, TB, malaria).

    Note: CDC pages are largely static, so this scraper extracts program descriptions.
    TODO: Inspect the page structure and verify selectors.
    """

    SOURCE_NAME = "CDC Cameroon"
    SOURCE_URL = "https://www.cdc.gov/global-health/countries/cameroon.html"
    CATEGORY = "ngo"

    def parse(self, soup: BeautifulSoup) -> list[dict]:
        campaigns = []
        # CDC uses structured content blocks — headings + paragraphs
        # TODO: Inspect the live page and update selectors if needed
        sections = soup.select("div.card, section, div.syndicate")
        for sec in sections:
            title_el = sec.select_one("h2, h3, h4")
            desc_el = sec.select_one("p")

            title = _safe_text(title_el)
            desc = _safe_text(desc_el)

            if not title or not desc:
                continue
            campaigns.append(
                {
                    "title": title,
                    "date": "",
                    "description": desc,
                    "location": "Cameroun",
                    "link": self.SOURCE_URL,
                }
            )
        return campaigns


class IMCScraper(BaseScraper):
    """
    International Medical Corps — Cameroon
    URL: https://internationalmedicalcorps.org/country/cameroon/

    Targets program reports on community surveillance, nutrition,
    and maternal health in the Far North and Adamawa regions.

    TODO: Inspect the country page and verify content selectors.
    """

    SOURCE_NAME = "International Medical Corps"
    SOURCE_URL = "https://internationalmedicalcorps.org/country/cameroon/"
    CATEGORY = "ngo"

    def parse(self, soup: BeautifulSoup) -> list[dict]:
        campaigns = []
        # TODO: Inspect page and update selectors — IMC uses a custom CMS
        items = soup.select("div.program-block, article, div.impact-item, section.country-section")
        for item in items:
            title_el = item.select_one("h2, h3, h4, .program-title")
            desc_el = item.select_one("p, .program-description")

            title = _safe_text(title_el)
            if not title:
                continue
            campaigns.append(
                {
                    "title": title,
                    "date": "",
                    "description": _safe_text(desc_el),
                    "location": "Far North / Adamawa, Cameroun",
                    "link": self.SOURCE_URL,
                }
            )
        return campaigns


# =============================================================================
# CATEGORY 4: AGGREGATORS & SPECIALIZED REPOSITORIES
# =============================================================================


class ReliefWebScraper(BaseScraper):
    """
    ReliefWeb — Cameroon Health Reports (OCHA)
    URL: https://reliefweb.int/updates?advanced-search=%28PC192%29_%28F10%29

    Uses the ReliefWeb public API (JSON) for maximum reliability —
    no HTML parsing needed.
    Returns health reports for Cameroon from UNICEF, UNFPA, IFRC, etc.
    """

    SOURCE_NAME = "ReliefWeb"
    # ReliefWeb REST API — filtered for Cameroon (PC192) and Health (F10 = sector)
    SOURCE_URL = (
        "https://api.reliefweb.int/v1/reports"
        "?appname=camphe-scraper"
        "&filter[operator]=AND"
        "&filter[conditions][0][field]=country.id&filter[conditions][0][value]=192"
        "&filter[conditions][1][field]=theme.id&filter[conditions][1][value]=4590"
        "&fields[include][]=title&fields[include][]=date&fields[include][]=body"
        "&fields[include][]=url&fields[include][]=source"
        "&sort[]=date:desc"
        "&limit=20"
    )
    CATEGORY = "aggregator"

    def parse(self, soup: BeautifulSoup) -> list[dict]:  # pragma: no cover
        """Not used — ReliefWebScraper overrides run() to consume a JSON API instead."""
        return []

    def fetch(self, url: str | None = None) -> dict | None:  # type: ignore[override]
        """Override fetch to return JSON directly from the ReliefWeb API."""
        import requests as req
        target = url or self.SOURCE_URL
        try:
            resp = req.get(target, headers=COMMON_HEADERS, timeout=self.timeout)
            resp.raise_for_status()
            logger.info(f"[{self.SOURCE_NAME}] API response OK ({resp.status_code})")
            return resp.json()
        except Exception as e:
            logger.error(f"[{self.SOURCE_NAME}] API call failed: {e}")
            return None

    def run(self) -> list[dict]:  # type: ignore[override]
        """Override run() to handle JSON API response instead of HTML."""
        logger.info(f"[{self.SOURCE_NAME}] Starting API fetch...")
        data = self.fetch()
        if not data:
            return []

        campaigns = []
        from datetime import datetime
        for item in data.get("data", []):
            fields = item.get("fields", {})
            title = fields.get("title", "")
            if not title:
                continue
            raw_date = fields.get("date", {}).get("created", "")
            source_names = ", ".join(
                s.get("name", "") for s in fields.get("source", [])
            )
            campaigns.append(
                {
                    "id": hashlib.md5(f"reliefweb:{title}".encode()).hexdigest()[:12],
                    "title": title,
                    "date": raw_date[:10] if raw_date else "",
                    "description": (fields.get("body", "")[:300] + "…")
                    if fields.get("body")
                    else f"Source: {source_names}",
                    "location": "Cameroun",
                    "link": fields.get("url", ""),
                    "source_name": self.SOURCE_NAME,
                    "source_url": self.SOURCE_URL,
                    "category": self.CATEGORY,
                    "scraped_at": datetime.utcnow().isoformat() + "Z",
                    "status": "active",
                }
            )
        logger.info(f"[{self.SOURCE_NAME}] Found {len(campaigns)} item(s) via API.")
        return campaigns





class CAPOneHealthScraper(BaseScraper):
    """
    CAP-One Health Platform
    URL: https://www.cap-onehealth.com

    Targets risk communication campaigns, academic health events,
    and virtual conferences on One Health issues in Cameroon.

    TODO: Inspect the site and identify event/news listing page and selectors.
    """

    SOURCE_NAME = "CAP-One Health"
    SOURCE_URL = "https://www.cap-onehealth.com"
    CATEGORY = "aggregator"

    def parse(self, soup: BeautifulSoup) -> list[dict]:
        campaigns = []
        # TODO: Inspect the events or news section and update selectors
        items = soup.select("div.event-item, article, div.news-card, li.post")
        for item in items:
            title_el = item.select_one("h2, h3, h4, .event-title, .post-title")
            date_el = item.select_one("time, .event-date, .date")
            desc_el = item.select_one("p, .event-description, .excerpt")
            link_el = item.select_one("a[href]")

            title = _safe_text(title_el)
            if not title:
                continue
            campaigns.append(
                {
                    "title": title,
                    "date": _try_parse_date(_safe_text(date_el)),
                    "description": _safe_text(desc_el),
                    "location": "Cameroun",
                    "link": urljoin(self.SOURCE_URL, link_el.get("href", "")) if link_el else self.SOURCE_URL,
                }
            )
        return campaigns
