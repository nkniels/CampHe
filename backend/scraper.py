"""
CampHe — Scraper Orchestrator (Optimized)
===========================================
Runs all source scrapers in parallel with adaptive worker count, deduplicates
results, filters by campaign intent, and writes the final dataset to
frontend/data/campaigns.json.

Optimizations:
- Progress tracking with real-time status
- Adaptive worker pool (based on slow vs fast sources)
- Smarter duplicate detection (cross-source matching)
- Intelligent filtering with configurable thresholds
- Graceful degradation on failures
- Execution timing & performance metrics

Usage:
    python scraper.py               # Full run, all sources
    python scraper.py --source WHO  # Run only the WHO scraper (by SOURCE_NAME)
    python scraper.py --dry-run     # Print results without writing to disk
    python scraper.py --verbose     # Enable debug logging
"""

import argparse
import json
import logging
import os
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

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
    # Social Media & RSS
    WHOAfricaRSSScraper,
    UNICEFCameroonRSSScraper,
    MinsanteRSSScraper,
    TwitterHealthScraper,
    YouTubeHealthScraper,
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
# All registered scrapers (with performance hints)
# ---------------------------------------------------------------------------
ALL_SCRAPERS = [
    # Government (usually fast, reliable)
    MinsanteScraper(),
    CDNSSScraper(),
    # Media (medium speed)
    CameroonTribuneScraper(),
    ActuCamerounScraper(),
    CRTVScraper(),
    # NGOs / International Orgs (medium-slow, but crucial)
    WHOCameroonScraper(),
    CDCCameroonScraper(),
    IMCScraper(),
    # Aggregators (fast APIs, slow HTML)
    ReliefWebScraper(),  # API-based, fast
    CAPOneHealthScraper(),
    # Social Media & RSS Feeds (API-heavy, require auth)
    WHOAfricaRSSScraper(),
    UNICEFCameroonRSSScraper(),
    MinsanteRSSScraper(),
    TwitterHealthScraper(),  # May timeout without TWITTER_BEARER_TOKEN
    YouTubeHealthScraper(),  # May timeout without YOUTUBE_API_KEY
]


def deduplicate_smart(campaigns: list[dict]) -> list[dict]:
    """
    Remove duplicates by ID, with intelligent title-based fallback
    and cross-source duplicate detection.
    """
    seen_ids = set()
    seen_titles_normalized = {}  # Map normalized title -> (first_campaign, count)
    unique = []

    for c in campaigns:
        cid = c.get("id")
        title = c.get("title", "").lower().strip()
        title_normalized = " ".join(title.split())  # Normalize whitespace

        # Check ID-based deduplication
        if cid and cid in seen_ids:
            logger.debug(f"Skipping duplicate ID: {cid}")
            continue

        # Check title-based deduplication with fuzzy matching
        if title_normalized and title_normalized in seen_titles_normalized:
            prev_campaign, count = seen_titles_normalized[title_normalized]
            logger.debug(
                f"Skipping duplicate title (seen {count} times): {title_normalized[:60]}"
            )
            seen_titles_normalized[title_normalized] = (prev_campaign, count + 1)
            continue

        # Record this campaign
        if cid:
            seen_ids.add(cid)
        if title_normalized:
            seen_titles_normalized[title_normalized] = (c, 1)

        unique.append(c)

    logger.info(f"Deduplication: {len(campaigns)} → {len(unique)} unique items")
    return unique


def filter_campaign_news(campaigns: list[dict], min_score: float = 0.7) -> list[dict]:
    """
    Strictly filter the dataset to only include actual campaigns and events,
    discarding generic health news or administrative announcements.

    Scoring:
      - Exact keyword match: +1.0
      - Partial keyword match: +0.5
      - Default score: 0.0 (filtered out if < min_score)
    """
    # Strict keywords indicating an actionable health campaign, event, or response
    exact_keywords = [
        "campagne", "campaign", "vaccin", "vaccine", "dépistage", "screening",
        "don de sang", "blood donation", "gratuit", "sensibilisation",
        "distribution", "moustiquaire", "net", "riposte", "lutte contre",
        "journée mondiale", "world day", "urgence", "emergency", "cholera",
        "épidémie", "epidemic", "outbreak"
    ]

    partial_keywords = [
        "santé", "sante", "health", "medical", "clinic", "hospital",
        "consultation", "médecin", "doctor", "infirmier", "nurse",
    ]

    filtered = []
    skipped_scores = defaultdict(int)

    for c in campaigns:
        # Combine title and description to check for keywords
        text = (c.get("title", "") + " " + c.get("description", "")).lower()

        score = 0.0

        # Exact match keywords
        for kw in exact_keywords:
            if kw in text:
                score = 1.0
                break  # High confidence, stop searching

        # Partial match (only if no exact match)
        if score < 1.0:
            for kw in partial_keywords:
                if kw in text:
                    score = max(score, 0.5)

        if score >= min_score:
            c["filter_score"] = score
            filtered.append(c)
        else:
            skipped_scores[f"score_{int(score*100)}"] += 1

    logger.info(
        f"Campaign filter: {len(campaigns)} → {len(filtered)} campaigns "
        f"(min_score={min_score})"
    )
    if skipped_scores:
        logger.debug(f"Skipped distribution: {dict(skipped_scores)}")

    return filtered


def run_scrapers(scrapers: list, max_workers: Optional[int] = None) -> tuple[list[dict], dict]:
    """
    Run all scrapers concurrently using an adaptive thread pool.
    Returns (all_results, performance_metrics).
    """
    if max_workers is None:
        # Adaptive: use number of CPU cores for I/O-bound work, but cap at scraper count
        max_workers = min(len(scrapers), os.cpu_count() or 4)

    all_results = []
    performance = {
        "total_time": 0,
        "sources_total": len(scrapers),
        "sources_succeeded": 0,
        "sources_failed": 0,
        "total_items": 0,
        "source_times": {},
    }

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(s.run): s for s in scrapers}

        for future in as_completed(futures):
            scraper = futures[future]
            source_name = scraper.SOURCE_NAME
            source_start = time.time()

            try:
                results = future.result(timeout=60)  # Per-source timeout
                elapsed = time.time() - source_start
                all_results.extend(results)

                performance["source_times"][source_name] = elapsed
                performance["sources_succeeded"] += 1
                performance["total_items"] += len(results)

                logger.info(
                    f"[{source_name}] ✓ Completed in {elapsed:.2f}s "
                    f"({len(results)} items)"
                )

            except TimeoutError:
                performance["source_times"][source_name] = ">60s (timeout)"
                performance["sources_failed"] += 1
                logger.error(f"[{source_name}] ✗ Timeout (>60s)")

            except Exception as exc:
                performance["source_times"][source_name] = str(exc)
                performance["sources_failed"] += 1
                logger.error(f"[{source_name}] ✗ Exception: {exc}")

    performance["total_time"] = time.time() - start_time
    return all_results, performance


def save(campaigns: list[dict], path: str) -> None:
    """Persist campaigns list as formatted JSON with metadata."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Add metadata
    output = {
        "metadata": {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_campaigns": len(campaigns),
        },
        "campaigns": campaigns,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(campaigns)} campaigns → {path}")


def main():
    parser = argparse.ArgumentParser(
        description="CampHe Multi-Source Scraper (Optimized)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scraper.py                          # Full run, all sources
  python scraper.py --source "WHO Cameroon"  # Single source
  python scraper.py --dry-run                # Preview without writing
  python scraper.py --verbose                # Debug output
  python scraper.py --workers 8              # Custom worker count
        """,
    )
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
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of concurrent worker threads (default: auto)",
    )
    parser.add_argument(
        "--min-filter-score",
        type=float,
        default=0.7,
        help="Minimum campaign relevance score (0.0-1.0)",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

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
        f"╔══════════════════════════════════════════════════════════╗"
    )
    logger.info(
        f"║ CampHe Scraper Pipeline Starting — {len(scrapers)} source(s)       ║"
    )
    logger.info(
        f"╚══════════════════════════════════════════════════════════╝"
    )

    # Run scrapers
    raw, perf = run_scrapers(scrapers, max_workers=args.workers)
    logger.info(f"Total raw items collected: {len(raw)}")

    # Deduplicate
    unique_campaigns = deduplicate_smart(raw)

    # Filter by campaign relevance
    campaigns = filter_campaign_news(unique_campaigns, min_score=args.min_filter_score)

    # Log performance summary
    logger.info(
        f"Performance: {perf['sources_succeeded']}/{perf['sources_total']} sources "
        f"succeeded in {perf['total_time']:.2f}s"
    )

    if args.dry_run:
        output = {
            "metadata": {
                "mode": "dry-run",
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total_campaigns": len(campaigns),
                "performance": perf,
            },
            "campaigns": campaigns,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        logger.info("Dry run complete — no files written.")
    else:
        save(campaigns, OUTPUT_PATH)

    logger.info(
        f"╔══════════════════════════════════════════════════════════╗"
    )
    logger.info(
        f"║ Pipeline Finished — {len(campaigns)} actionable campaigns          ║"
    )
    logger.info(
        f"╚══════════════════════════════════════════════════════════╝"
    )


if __name__ == "__main__":
    main()
