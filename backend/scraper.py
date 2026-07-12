"""
CampHe — Scraper Orchestrator
==============================
Runs all source scrapers in parallel, deduplicates results, and writes
the final dataset to frontend/data/campaigns.json.

Usage:
    python scraper.py               # Full run, all sources
    python scraper.py --source WHO  # Run only the WHO scraper (by SOURCE_NAME)
    python scraper.py --dry-run     # Print results without writing to disk
"""

import argparse
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from sources import (
    ActuCamerounScraper,
    CDCCameroonScraper,
    CDNSSScraper,
    CAPOneHealthScraper,
    CameroonTribuneScraper,
    CRTVScraper,
    IMCScraper,
    MinsanteScraper,
    ReliefWebScraper,
    WHOCameroonScraper,
)

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("camphe.orchestrator")

# ---------------------------------------------------------------------------
# Output Path
# ---------------------------------------------------------------------------
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "frontend", "data", "campaigns.json"
)

# ---------------------------------------------------------------------------
# All registered scrapers
# ---------------------------------------------------------------------------
ALL_SCRAPERS = [
    # Government
    MinsanteScraper(),
    CDNSSScraper(),
    # Media
    CameroonTribuneScraper(),
    ActuCamerounScraper(),
    CRTVScraper(),
    # NGOs / International Orgs
    WHOCameroonScraper(),
    CDCCameroonScraper(),
    IMCScraper(),
    # Aggregators
    ReliefWebScraper(),
    CAPOneHealthScraper(),
]


def deduplicate(campaigns: list[dict]) -> list[dict]:
    """
    Remove duplicates by stable ID.
    For items without an ID (shouldn't happen), fall back to title dedup.
    """
    seen_ids = set()
    seen_titles = set()
    unique = []
    for c in campaigns:
        cid = c.get("id")
        title = c.get("title", "").lower().strip()
        if cid and cid in seen_ids:
            continue
        if title and title in seen_titles:
            continue
        if cid:
            seen_ids.add(cid)
        if title:
            seen_titles.add(title)
        unique.append(c)
    return unique


def run_scrapers(scrapers: list, max_workers: int = 5) -> list[dict]:
    """Run all scrapers concurrently using a thread pool."""
    all_results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(s.run): s.SOURCE_NAME for s in scrapers}
        for future in as_completed(futures):
            source_name = futures[future]
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as exc:
                logger.error(f"[{source_name}] Raised an exception: {exc}")
    return all_results


def save(campaigns: list[dict], path: str) -> None:
    """Persist campaigns list as formatted JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(campaigns, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(campaigns)} campaigns → {path}")


def main():
    parser = argparse.ArgumentParser(description="CampHe Multi-Source Scraper")
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Run only a specific scraper by SOURCE_NAME (e.g., 'WHO Cameroon')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print results to stdout without writing to disk",
    )
    args = parser.parse_args()

    # Filter scrapers if --source is specified
    scrapers = ALL_SCRAPERS
    if args.source:
        scrapers = [
            s for s in ALL_SCRAPERS
            if s.SOURCE_NAME.lower() == args.source.lower()
        ]
        if not scrapers:
            logger.error(
                f"No scraper found with SOURCE_NAME='{args.source}'. "
                f"Available: {[s.SOURCE_NAME for s in ALL_SCRAPERS]}"
            )
            return

    logger.info(
        f"═══ CampHe Scraper Pipeline Starting — {len(scrapers)} source(s) ═══"
    )
    raw = run_scrapers(scrapers)
    logger.info(f"Total raw items collected: {len(raw)}")

    campaigns = deduplicate(raw)
    logger.info(f"After deduplication: {len(campaigns)} unique campaign(s)")

    if args.dry_run:
        print(json.dumps(campaigns, indent=2, ensure_ascii=False))
        logger.info("Dry run complete — no files written.")
    else:
        save(campaigns, OUTPUT_PATH)

    logger.info("═══ Pipeline Finished ═══")


if __name__ == "__main__":
    main()
